from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from sqlmodel import SQLModel
from alembic import context
import os
import sys
from dotenv import load_dotenv

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import your models here to ensure they're registered with SQLModel.metadata
from app.models.product import Product, NormalizedNutrition
from app.models.user import UserProfile
from app.models.scan_history import ScanHistory
from app.models.product_contribution import ProductContribution
from app.models.user_favorite import UserFavorite

# Load environment variables
load_dotenv()

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
target_metadata = SQLModel.metadata

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    # Get URL from environment or config
    url = os.getenv('DATABASE_URL') or config.get_main_option("sqlalchemy.url")
    if not url:
        raise ValueError("DATABASE_URL environment variable or alembic.ini sqlalchemy.url must be set")
    
    # Convert to async URL for PostgreSQL
    if url.startswith('postgresql://'):
        url = url.replace('postgresql://', 'postgresql+asyncpg://')
    
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    from sqlalchemy.ext.asyncio import create_async_engine
    from sqlalchemy.pool import NullPool
    
    # Get URL from environment or config
    url = os.getenv('DATABASE_URL') or config.get_main_option("sqlalchemy.url")
    if not url:
        raise ValueError("DATABASE_URL environment variable or alembic.ini sqlalchemy.url must be set")
    
    # Convert to async URL for PostgreSQL
    if url.startswith('postgresql://'):
        url = url.replace('postgresql://', 'postgresql+asyncpg://')
    
    connectable = create_async_engine(
        url,
        poolclass=NullPool,
        echo=True
    )

    async def run_migrations():
        async with connectable.connect() as connection:
            await connection.run_sync(do_run_migrations)
        await connectable.dispose()
            
    import asyncio
    asyncio.run(run_migrations())

def do_run_migrations(connection):
    context.configure(
        connection=connection, 
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True
    )

    with context.begin_transaction():
        context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
