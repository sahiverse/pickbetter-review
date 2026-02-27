"""
Admin verification utility for managing pending product contributions.

This script provides a simple interface for administrators to:
- List all pending contributions
- View details of a specific contribution
- Approve or reject contributions
- Bulk approve/reject multiple contributions

Usage:
    python -m app.scripts.verify_contributions --list
    python -m app.scripts.verify_contributions --verify <product_id>
    python -m app.scripts.verify_contributions --reject <product_id>
    python -m app.scripts.verify_contributions --bulk-approve
"""

import asyncio
import argparse
import sys
from datetime import datetime
from typing import List, Optional

from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.database_dev import get_async_session
from app.models.product import Product


async def list_pending_contributions(session: AsyncSession, limit: int = 50) -> List[Product]:
    """List all pending contributions."""
    result = await session.execute(
        select(Product)
        .where(Product.pending_verification == True)
        .order_by(Product.created_at.desc())
        .limit(limit)
    )
    return list(result.scalars().all())


async def get_contribution_by_id(session: AsyncSession, product_id: int) -> Optional[Product]:
    """Get a specific contribution by ID."""
    result = await session.execute(
        select(Product).where(Product.id == product_id)
    )
    return result.scalar_one_or_none()


async def approve_contribution(session: AsyncSession, product_id: int) -> dict:
    """
    Approve a pending contribution.
    
    Args:
        session: Database session
        product_id: Product ID to approve
        
    Returns:
        Dictionary with approval result
    """
    product = await get_contribution_by_id(session, product_id)
    
    if not product:
        return {"success": False, "error": f"Product with ID {product_id} not found"}
    
    if not product.pending_verification:
        return {
            "success": False, 
            "error": f"Product {product.name} is not pending verification (already verified or not a contribution)"
        }
    
    product.verified = True
    product.pending_verification = False
    await session.commit()
    
    return {
        "success": True,
        "message": f"✅ Approved: {product.name} (Barcode: {product.barcode})",
        "product": {
            "id": product.id,
            "barcode": product.barcode,
            "name": product.name,
            "brand": product.brand,
            "grade": product.health_grade,
            "score": product.health_score,
            "source": product.source
        }
    }


async def reject_contribution(session: AsyncSession, product_id: int) -> dict:
    """
    Reject and delete a pending contribution.
    
    Args:
        session: Database session
        product_id: Product ID to reject
        
    Returns:
        Dictionary with rejection result
    """
    product = await get_contribution_by_id(session, product_id)
    
    if not product:
        return {"success": False, "error": f"Product with ID {product_id} not found"}
    
    if not product.pending_verification:
        return {
            "success": False,
            "error": f"Product {product.name} is not pending verification"
        }
    
    product_info = {
        "id": product.id,
        "barcode": product.barcode,
        "name": product.name
    }
    
    await session.delete(product)
    await session.commit()
    
    return {
        "success": True,
        "message": f"❌ Rejected and removed: {product_info['name']} (Barcode: {product_info['barcode']})",
        "product": product_info
    }


async def bulk_approve(session: AsyncSession) -> dict:
    """Approve all pending contributions."""
    pending = await list_pending_contributions(session)
    
    if not pending:
        return {"success": True, "message": "No pending contributions to approve", "approved": 0}
    
    approved_count = 0
    for product in pending:
        product.verified = True
        product.pending_verification = False
        approved_count += 1
    
    await session.commit()
    
    return {
        "success": True,
        "message": f"✅ Bulk approved {approved_count} contributions",
        "approved": approved_count
    }


async def bulk_reject(session: AsyncSession) -> dict:
    """Reject all pending contributions."""
    pending = await list_pending_contributions(session)
    
    if not pending:
        return {"success": True, "message": "No pending contributions to reject", "rejected": 0}
    
    rejected_count = 0
    for product in pending:
        await session.delete(product)
        rejected_count += 1
    
    await session.commit()
    
    return {
        "success": True,
        "message": f"❌ Bulk rejected and removed {rejected_count} contributions",
        "rejected": rejected_count
    }


def print_contribution_details(product: Product, index: int = None):
    """Print formatted contribution details."""
    prefix = f"[{index}] " if index is not None else ""
    
    print(f"\n{'='*60}")
    print(f"{prefix}Product ID: {product.id}")
    print(f"   Barcode: {product.barcode}")
    print(f"   Name: {product.name}")
    print(f"   Brand: {product.brand or 'N/A'}")
    print(f"   Health Grade: {product.health_grade} ({product.health_score}/100)")
    print(f"   Source: {product.source}")
    print(f"   Created: {product.created_at.strftime('%Y-%m-%d %H:%M') if product.created_at else 'N/A'}")
    
    if product.nutriments:
        print(f"\n   Nutrition Data (per 100g):")
        for key, value in product.nutriments.items():
            if value is not None:
                print(f"     - {key}: {value}")
    
    if product.ingredients_text:
        print(f"\n   Ingredients: {product.ingredients_text[:100]}...")
    
    print(f"{'='*60}")


async def interactive_mode(session: AsyncSession):
    """Run interactive verification mode."""
    print("\n🔍 PickBetter Contribution Verification Tool")
    print("=" * 60)
    
    while True:
        pending = await list_pending_contributions(session, limit=20)
        
        if not pending:
            print("\n✨ No pending contributions to verify!")
            break
        
        print(f"\n📋 Found {len(pending)} pending contribution(s):\n")
        
        for i, product in enumerate(pending, 1):
            print_contribution_details(product, i)
        
        print("\n" + "=" * 60)
        print("Commands:")
        print("  v <number>  - Verify/approve contribution")
        print("  r <number>  - Reject contribution")
        print("  va          - Verify all pending")
        print("  ra          - Reject all pending")
        print("  q           - Quit")
        print("=" * 60)
        
        choice = input("\nEnter command: ").strip().lower()
        
        if choice == 'q':
            print("\n👋 Goodbye!")
            break
        
        elif choice == 'va':
            confirm = input("Are you sure you want to approve ALL pending contributions? (yes/no): ")
            if confirm.lower() == 'yes':
                result = await bulk_approve(session)
                print(f"\n{result['message']}")
            else:
                print("\nCancelled.")
        
        elif choice == 'ra':
            confirm = input("Are you sure you want to reject ALL pending contributions? (yes/no): ")
            if confirm.lower() == 'yes':
                result = await bulk_reject(session)
                print(f"\n{result['message']}")
            else:
                print("\nCancelled.")
        
        elif choice.startswith('v '):
            try:
                index = int(choice.split()[1]) - 1
                if 0 <= index < len(pending):
                    product = pending[index]
                    result = await approve_contribution(session, product.id)
                    print(f"\n{result['message']}" if result['success'] else f"\n❌ Error: {result['error']}")
                else:
                    print("\n❌ Invalid number. Please try again.")
            except (ValueError, IndexError):
                print("\n❌ Invalid command format. Use: v <number>")
        
        elif choice.startswith('r '):
            try:
                index = int(choice.split()[1]) - 1
                if 0 <= index < len(pending):
                    product = pending[index]
                    result = await reject_contribution(session, product.id)
                    print(f"\n{result['message']}" if result['success'] else f"\n❌ Error: {result['error']}")
                else:
                    print("\n❌ Invalid number. Please try again.")
            except (ValueError, IndexError):
                print("\n❌ Invalid command format. Use: r <number>")
        
        else:
            print("\n❌ Unknown command. Please try again.")


async def main():
    """Main entry point for the verification utility."""
    parser = argparse.ArgumentParser(
        description="PickBetter Admin Contribution Verification Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m app.scripts.verify_contributions --list
  python -m app.scripts.verify_contributions --verify 123
  python -m app.scripts.verify_contributions --reject 123
  python -m app.scripts.verify_contributions --bulk-approve
  python -m app.scripts.verify_contributions --interactive
        """
    )
    
    parser.add_argument('--list', '-l', action='store_true', help='List all pending contributions')
    parser.add_argument('--verify', '-v', type=int, metavar='ID', help='Approve contribution by ID')
    parser.add_argument('--reject', '-r', type=int, metavar='ID', help='Reject contribution by ID')
    parser.add_argument('--bulk-approve', '-ba', action='store_true', help='Approve all pending contributions')
    parser.add_argument('--bulk-reject', '-br', action='store_true', help='Reject all pending contributions')
    parser.add_argument('--interactive', '-i', action='store_true', help='Run in interactive mode')
    parser.add_argument('--limit', type=int, default=50, help='Limit number of results (default: 50)')
    
    args = parser.parse_args()
    
    # If no arguments, default to interactive mode
    if not any([args.list, args.verify, args.reject, args.bulk_approve, args.bulk_reject, args.interactive]):
        args.interactive = True
    
    # Get database session
    session_gen = get_async_session()
    session = await session_gen.__anext__()
    
    try:
        if args.list:
            pending = await list_pending_contributions(session, args.limit)
            
            if not pending:
                print("\n✨ No pending contributions found.")
                return
            
            print(f"\n📋 Found {len(pending)} pending contribution(s):\n")
            for i, product in enumerate(pending, 1):
                print_contribution_details(product, i)
        
        elif args.verify:
            result = await approve_contribution(session, args.verify)
            if result['success']:
                print(f"\n{result['message']}")
                print(f"\n📊 Product Details:")
                for key, value in result['product'].items():
                    print(f"   {key}: {value}")
            else:
                print(f"\n❌ Error: {result['error']}")
                sys.exit(1)
        
        elif args.reject:
            result = await reject_contribution(session, args.reject)
            if result['success']:
                print(f"\n{result['message']}")
            else:
                print(f"\n❌ Error: {result['error']}")
                sys.exit(1)
        
        elif args.bulk_approve:
            confirm = input("Are you sure you want to approve ALL pending contributions? (yes/no): ")
            if confirm.lower() == 'yes':
                result = await bulk_approve(session)
                print(f"\n{result['message']}")
            else:
                print("\nCancelled.")
        
        elif args.bulk_reject:
            confirm = input("Are you sure you want to reject ALL pending contributions? (yes/no): ")
            if confirm.lower() == 'yes':
                result = await bulk_reject(session)
                print(f"\n{result['message']}")
            else:
                print("\nCancelled.")
        
        elif args.interactive:
            await interactive_mode(session)
    
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        sys.exit(1)
    finally:
        await session.close()


if __name__ == "__main__":
    asyncio.run(main())
