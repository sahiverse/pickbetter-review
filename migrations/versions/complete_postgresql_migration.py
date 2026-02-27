"""Complete PostgreSQL migration with all tables, indexes, and constraints

Revision ID: complete_postgresql_migration
Revises: 
Create Date: 2026-02-26

This migration creates the complete database schema for PostgreSQL including:
- All 6 tables (products, normalized_nutrition, user_profiles, scan_history, product_contributions, user_favorites)
- All indexes for performance
- All constraints and foreign keys
- Triggers for auto-update timestamps
- Soft delete support
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'complete_postgresql_migration'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create all tables with PostgreSQL-specific features."""
    
    # ============================================================================
    # 1. PRODUCTS TABLE
    # ============================================================================
    op.create_table(
        'products',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('barcode', sa.String(length=13), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('brand', sa.String(length=100), nullable=True),
        sa.Column('category', sa.String(length=100), nullable=True),
        sa.Column('image_url', sa.String(length=500), nullable=True),
        sa.Column('ingredients_text', sa.Text(), nullable=True),
        sa.Column('ingredients_list', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('nutriments', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('nutrition_grades', sa.String(length=1), nullable=True),
        sa.Column('nova_group', sa.Integer(), nullable=True),
        sa.Column('ecoscore_grade', sa.String(length=1), nullable=True),
        sa.Column('last_modified', sa.DateTime(timezone=True), nullable=True),
        sa.Column('health_score', sa.Integer(), nullable=True),
        sa.Column('health_grade', sa.String(length=1), nullable=True),
        sa.Column('score_last_calculated', sa.DateTime(timezone=True), nullable=True),
        sa.Column('verification_status', sa.String(length=20), nullable=False, server_default='verified'),
        sa.Column('source', sa.String(length=50), nullable=True, server_default='openfoodfacts'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint('health_score >= 0 AND health_score <= 100', name='check_health_score_range'),
        sa.CheckConstraint("health_grade IN ('A', 'B', 'C', 'D', 'E', 'F')", name='check_health_grade_values'),
        sa.CheckConstraint('nova_group >= 1 AND nova_group <= 4', name='check_nova_group_range'),
        sa.CheckConstraint("barcode ~ '^[0-9]{8,13}$'", name='check_barcode_format'),
    )
    
    # Products indexes
    op.create_index('idx_products_barcode', 'products', ['barcode'], unique=True, postgresql_where=sa.text('deleted_at IS NULL'))
    op.create_index('idx_products_category', 'products', ['category'], postgresql_where=sa.text('deleted_at IS NULL'))
    op.create_index('idx_products_brand', 'products', ['brand'], postgresql_where=sa.text('deleted_at IS NULL'))
    op.create_index('idx_products_health_grade', 'products', ['health_grade'], postgresql_where=sa.text('deleted_at IS NULL'))
    op.create_index('idx_products_created_at', 'products', [sa.text('created_at DESC')], postgresql_where=sa.text('deleted_at IS NULL'))
    op.create_index('idx_products_category_health_grade', 'products', ['category', 'health_grade'], postgresql_where=sa.text('deleted_at IS NULL'))
    op.create_index('idx_products_brand_health_score', 'products', ['brand', sa.text('health_score DESC')], postgresql_where=sa.text('deleted_at IS NULL'))
    
    # Full-text search index
    op.execute("""
        CREATE INDEX idx_products_search ON products 
        USING GIN(to_tsvector('english', name || ' ' || COALESCE(brand, '') || ' ' || COALESCE(category, '')))
        WHERE deleted_at IS NULL
    """)
    
    # JSONB index for nutriments
    op.create_index('idx_products_nutriments', 'products', ['nutriments'], postgresql_using='gin')
    
    # ============================================================================
    # 2. NORMALIZED_NUTRITION TABLE
    # ============================================================================
    op.create_table(
        'normalized_nutrition',
        sa.Column('product_id', sa.Integer(), nullable=False),
        sa.Column('calories_100g', sa.Float(), nullable=True),
        sa.Column('protein_100g', sa.Float(), nullable=True),
        sa.Column('carbohydrates_100g', sa.Float(), nullable=True),
        sa.Column('sugars_100g', sa.Float(), nullable=True),
        sa.Column('fat_100g', sa.Float(), nullable=True),
        sa.Column('saturated_fat_100g', sa.Float(), nullable=True),
        sa.Column('trans_fat_100g', sa.Float(), nullable=True),
        sa.Column('fiber_100g', sa.Float(), nullable=True),
        sa.Column('added_sugar_100g', sa.Float(), nullable=True),
        sa.Column('sodium_100g', sa.Float(), nullable=True),
        sa.Column('salt_100g', sa.Float(), nullable=True),
        sa.Column('fvnl_percent', sa.Float(), nullable=True, server_default='0.0'),
        sa.Column('serving_size', sa.String(length=50), nullable=True),
        sa.Column('serving_quantity', sa.Float(), nullable=True),
        sa.Column('nutrition_score_fr_100g', sa.Integer(), nullable=True),
        sa.Column('nutrition_score_fr', sa.Integer(), nullable=True),
        sa.Column('general_health_score', sa.Integer(), nullable=True),
        sa.Column('nutri_grade', sa.String(length=1), nullable=True),
        sa.PrimaryKeyConstraint('product_id'),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ondelete='CASCADE'),
    )
    
    # ============================================================================
    # 3. USER_PROFILES TABLE
    # ============================================================================
    op.create_table(
        'user_profiles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.String(length=100), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('age', sa.Integer(), nullable=True),
        sa.Column('sex', sa.String(length=20), nullable=True),
        sa.Column('height', sa.Integer(), nullable=True),
        sa.Column('weight', sa.Integer(), nullable=True),
        sa.Column('allergens', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('health_conditions', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('custom_needs', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('custom_needs_status', sa.String(length=20), nullable=False, server_default='pending'),
        sa.Column('dietary_preference', sa.String(length=50), nullable=True, server_default='General'),
        sa.Column('primary_goal', sa.String(length=100), nullable=True, server_default='General Wellness'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    
    # User profiles indexes
    op.create_index('idx_user_profiles_user_id', 'user_profiles', ['user_id'], unique=True, postgresql_where=sa.text('deleted_at IS NULL'))
    op.create_index('idx_user_profiles_allergens', 'user_profiles', ['allergens'], postgresql_using='gin')
    op.create_index('idx_user_profiles_health_conditions', 'user_profiles', ['health_conditions'], postgresql_using='gin')
    
    # ============================================================================
    # 4. SCAN_HISTORY TABLE
    # ============================================================================
    op.create_table(
        'scan_history',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.String(length=100), nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=False),
        sa.Column('scanned_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('health_score_at_scan', sa.Integer(), nullable=True),
        sa.Column('health_grade_at_scan', sa.String(length=1), nullable=True),
        sa.Column('user_feedback', sa.String(length=20), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ondelete='CASCADE'),
    )
    
    # Scan history indexes
    op.create_index('idx_scan_history_user_id', 'scan_history', ['user_id'])
    op.create_index('idx_scan_history_product_id', 'scan_history', ['product_id'])
    op.create_index('idx_scan_history_scanned_at', 'scan_history', ['scanned_at'], postgresql_using='brin')
    op.create_index('idx_scan_history_user_scanned', 'scan_history', ['user_id', sa.text('scanned_at DESC')])
    
    # ============================================================================
    # 5. PRODUCT_CONTRIBUTIONS TABLE
    # ============================================================================
    op.create_table(
        'product_contributions',
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
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ondelete='SET NULL'),
    )
    
    # Product contributions indexes
    op.create_index('idx_contributions_status', 'product_contributions', ['status'])
    op.create_index('idx_contributions_barcode', 'product_contributions', ['barcode'])
    op.create_index('idx_contributions_contributor', 'product_contributions', ['contributor_user_id'])
    op.create_index('idx_contributions_created_at', 'product_contributions', [sa.text('created_at DESC')])
    
    # ============================================================================
    # 6. USER_FAVORITES TABLE
    # ============================================================================
    op.create_table(
        'user_favorites',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.String(length=100), nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('user_id', 'product_id', name='uq_user_product_favorite'),
    )
    
    # User favorites indexes
    op.create_index('idx_favorites_user_id', 'user_favorites', ['user_id'])
    op.create_index('idx_favorites_product_id', 'user_favorites', ['product_id'])
    
    # ============================================================================
    # 7. TRIGGERS FOR AUTO-UPDATE TIMESTAMPS
    # ============================================================================
    
    # Create the trigger function
    op.execute("""
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ language 'plpgsql';
    """)
    
    # Apply trigger to products table
    op.execute("""
        CREATE TRIGGER update_products_updated_at 
        BEFORE UPDATE ON products
        FOR EACH ROW 
        EXECUTE FUNCTION update_updated_at_column();
    """)
    
    # Apply trigger to user_profiles table
    op.execute("""
        CREATE TRIGGER update_user_profiles_updated_at 
        BEFORE UPDATE ON user_profiles
        FOR EACH ROW 
        EXECUTE FUNCTION update_updated_at_column();
    """)
    
    # ============================================================================
    # 8. MATERIALIZED VIEW FOR RECOMMENDATIONS
    # ============================================================================
    op.execute("""
        CREATE MATERIALIZED VIEW mv_product_recommendations AS
        SELECT 
            p.id,
            p.barcode,
            p.name,
            p.brand,
            p.category,
            p.health_score,
            p.health_grade,
            p.image_url,
            nn.calories_100g,
            nn.protein_100g,
            nn.sugars_100g,
            nn.fat_100g,
            nn.fiber_100g,
            nn.sodium_100g,
            p.created_at
        FROM products p
        LEFT JOIN normalized_nutrition nn ON p.id = nn.product_id
        WHERE p.deleted_at IS NULL
            AND p.health_score IS NOT NULL
            AND p.verification_status = 'verified';
    """)
    
    # Indexes on materialized view
    op.execute("""
        CREATE UNIQUE INDEX idx_mv_recommendations_id ON mv_product_recommendations(id);
    """)
    op.execute("""
        CREATE INDEX idx_mv_recommendations_category_score ON mv_product_recommendations(category, health_score DESC);
    """)
    op.execute("""
        CREATE INDEX idx_mv_recommendations_brand ON mv_product_recommendations(brand);
    """)
    
    print("✅ Complete PostgreSQL migration applied successfully!")


def downgrade() -> None:
    """Drop all tables and objects."""
    
    # Drop materialized view
    op.execute('DROP MATERIALIZED VIEW IF EXISTS mv_product_recommendations CASCADE')
    
    # Drop triggers
    op.execute('DROP TRIGGER IF EXISTS update_products_updated_at ON products')
    op.execute('DROP TRIGGER IF EXISTS update_user_profiles_updated_at ON user_profiles')
    op.execute('DROP FUNCTION IF EXISTS update_updated_at_column()')
    
    # Drop tables in reverse order (respecting foreign keys)
    op.drop_table('user_favorites')
    op.drop_table('product_contributions')
    op.drop_table('scan_history')
    op.drop_table('user_profiles')
    op.drop_table('normalized_nutrition')
    op.drop_table('products')
    
    print("✅ Complete PostgreSQL migration rolled back successfully!")
