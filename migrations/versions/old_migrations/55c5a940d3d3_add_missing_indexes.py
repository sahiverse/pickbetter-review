"""add_missing_indexes

Revision ID: 55c5a940d3d3
Revises: 7d9194c9637d
Create Date: 2026-01-17 16:44:58.782160+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '55c5a940d3d3'
down_revision: Union[str, Sequence[str], None] = '7d9194c9637d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create single-column indexes on products table
    op.create_index(op.f('ix_products_name'), 'products', ['name'])
    op.create_index(op.f('ix_products_brand'), 'products', ['brand'])
    op.create_index(op.f('ix_products_category'), 'products', ['category'])


def downgrade() -> None:
    """Downgrade schema."""
    # Drop indexes in reverse order of creation
    op.drop_index(op.f('ix_products_category'), table_name='products')
    op.drop_index(op.f('ix_products_brand'), table_name='products')
    op.drop_index(op.f('ix_products_name'), table_name='products')
