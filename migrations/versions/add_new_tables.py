"""add scan_history, product_contributions, and user_favorites tables

Revision ID: add_new_tables
Revises: cd08fc4abd93
Create Date: 2024-02-26 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_new_tables'
down_revision = 'cd08fc4abd93'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add deleted_at column to products table for soft delete
    op.add_column('products', sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True))
    
    # Add deleted_at column to user_profiles table for soft delete
    op.add_column('user_profiles', sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True))
    
    # Update user_profiles to use JSONB instead of Text for allergens, health_conditions, custom_needs
    # Note: This will work for PostgreSQL. For SQLite, it will use JSON
    op.alter_column('user_profiles', 'allergens',
                    existing_type=sa.Text(),
                    type_=postgresql.JSONB(astext_type=sa.Text()),
                    existing_nullable=True,
                    postgresql_using='allergens::jsonb')
    
    op.alter_column('user_profiles', 'health_conditions',
                    existing_type=sa.Text(),
                    type_=postgresql.JSONB(astext_type=sa.Text()),
                    existing_nullable=True,
                    postgresql_using='health_conditions::jsonb')
    
    op.alter_column('user_profiles', 'custom_needs',
                    existing_type=sa.Text(),
                    type_=postgresql.JSONB(astext_type=sa.Text()),
                    existing_nullable=True,
                    postgresql_using='custom_needs::jsonb')
    
    # Create scan_history table
    op.create_table('scan_history',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.String(length=100), nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=False),
        sa.Column('scanned_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('health_score_at_scan', sa.Integer(), nullable=True),
        sa.Column('health_grade_at_scan', sa.String(length=1), nullable=True),
        sa.Column('user_feedback', sa.String(length=20), nullable=True),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_scan_history_user_id', 'scan_history', ['user_id'])
    op.create_index('idx_scan_history_product_id', 'scan_history', ['product_id'])
    op.create_index('idx_scan_history_user_scanned', 'scan_history', ['user_id', 'scanned_at'])
    
    # Create product_contributions table
    op.create_table('product_contributions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=True),
        sa.Column('contributor_user_id', sa.String(length=100), nullable=True),
        sa.Column('contribution_type', sa.String(length=50), nullable=False),
        sa.Column('barcode', sa.String(length=13), nullable=False),
        sa.Column('nutrition_image_url', sa.String(length=500), nullable=True),
        sa.Column('ingredients_image_url', sa.String(length=500), nullable=True),
        sa.Column('ocr_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='pending'),
        sa.Column('reviewed_by', sa.String(length=100), nullable=True),
        sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_contributions_status', 'product_contributions', ['status'])
    op.create_index('idx_contributions_barcode', 'product_contributions', ['barcode'])
    op.create_index('idx_contributions_contributor', 'product_contributions', ['contributor_user_id'])
    op.create_index('idx_contributions_created_at', 'product_contributions', ['created_at'])
    
    # Create user_favorites table
    op.create_table('user_favorites',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.String(length=100), nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'product_id', name='uq_user_product_favorite')
    )
    op.create_index('idx_favorites_user_id', 'user_favorites', ['user_id'])
    op.create_index('idx_favorites_product_id', 'user_favorites', ['product_id'])


def downgrade() -> None:
    # Drop indexes and tables in reverse order
    op.drop_index('idx_favorites_product_id', table_name='user_favorites')
    op.drop_index('idx_favorites_user_id', table_name='user_favorites')
    op.drop_table('user_favorites')
    
    op.drop_index('idx_contributions_created_at', table_name='product_contributions')
    op.drop_index('idx_contributions_contributor', table_name='product_contributions')
    op.drop_index('idx_contributions_barcode', table_name='product_contributions')
    op.drop_index('idx_contributions_status', table_name='product_contributions')
    op.drop_table('product_contributions')
    
    op.drop_index('idx_scan_history_user_scanned', table_name='scan_history')
    op.drop_index('idx_scan_history_product_id', table_name='scan_history')
    op.drop_index('idx_scan_history_user_id', table_name='scan_history')
    op.drop_table('scan_history')
    
    # Revert user_profiles columns back to Text
    op.alter_column('user_profiles', 'custom_needs',
                    existing_type=postgresql.JSONB(astext_type=sa.Text()),
                    type_=sa.Text(),
                    existing_nullable=True)
    
    op.alter_column('user_profiles', 'health_conditions',
                    existing_type=postgresql.JSONB(astext_type=sa.Text()),
                    type_=sa.Text(),
                    existing_nullable=True)
    
    op.alter_column('user_profiles', 'allergens',
                    existing_type=postgresql.JSONB(astext_type=sa.Text()),
                    type_=sa.Text(),
                    existing_nullable=True)

    # Drop soft-delete columns
    op.drop_column('user_profiles', 'deleted_at')
    op.drop_column('products', 'deleted_at')