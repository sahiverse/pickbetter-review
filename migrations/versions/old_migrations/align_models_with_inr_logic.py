"""align_models_with_inr_logic

Revision ID: align_models_with_inr_logic
Revises: cd08fc4abd93
Create Date: 2026-02-18 21:50:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'align_models_with_inr_logic'
down_revision = 'cd08fc4abd93'
branch_labels = None
depends_on = None


def upgrade():
    # Add verification_status column to products table, replacing verified and pending_verification
    op.add_column('products', sa.Column('verification_status', sa.String(length=20), nullable=False, default='verified', server_default='verified'))

    # Add new nutrition columns to normalized_nutrition table
    op.add_column('normalized_nutrition', sa.Column('added_sugar_100g', sa.Float(), nullable=True))
    op.add_column('normalized_nutrition', sa.Column('trans_fat_100g', sa.Float(), nullable=True))
    op.add_column('normalized_nutrition', sa.Column('fvnl_percent', sa.Float(), nullable=True, default=0.0, server_default='0.0'))

    # Rename diet_type to dietary_preference in user_profiles table
    op.alter_column('user_profiles', 'diet_type', new_column_name='dietary_preference')

    # Remove old verification columns from products table
    op.drop_column('products', 'verified')
    op.drop_column('products', 'pending_verification')


def downgrade():
    # Reverse the changes
    op.add_column('products', sa.Column('pending_verification', sa.Boolean(), nullable=False, default=False, server_default='false'))
    op.add_column('products', sa.Column('verified', sa.Boolean(), nullable=False, default=True, server_default='true'))

    op.drop_column('products', 'verification_status')

    op.drop_column('normalized_nutrition', 'fvnl_percent')
    op.drop_column('normalized_nutrition', 'trans_fat_100g')
    op.drop_column('normalized_nutrition', 'added_sugar_100g')

    op.alter_column('user_profiles', 'dietary_preference', new_column_name='diet_type')
