"""add_knn_index

Revision ID: 8818b9492018
Revises: 55c5a940d3d3
Create Date: 2026-01-17 17:07:14.733923+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8818b9492018'
down_revision: Union[str, Sequence[str], None] = '55c5a940d3d3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create composite index for KNN search on normalized_nutrition
    op.create_index(
        'ix_normalized_nutrition_knn',
        'normalized_nutrition',
        ['sugars_100g', 'sodium_100g', 'protein_100g', 'fiber_100g']
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Drop KNN index
    op.drop_index('ix_normalized_nutrition_knn', table_name='normalized_nutrition')
