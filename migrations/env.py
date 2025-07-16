"""
Alembic environment configuration for the Reality Checker WhatsApp bot.

This module configures Alembic for database migrations with support for
both SQLite and PostgreSQL databases.
"""

import asyncio
import os
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import create_async_engine
from alembic import context

# Import the database configuration
from app.database.database import Base, Database

# This is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Add your model's MetaData object here for 'autogenerate' support
target_metadata = Base.metadata

# Other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def get_database_url():
    """Get database URL from environment or use default."""
    # Try to get from environment first
    database_url = os.getenv('DATABASE_URL')
    if database_url:
        return database_url
    
    # Check for PostgreSQL configuration
    if all(env_var in os.environ for env_var in ['DB_HOST', 'DB_NAME', 'DB_USER', 'DB_PASSWORD']):
        host = os.getenv('DB_HOST', 'localhost')
        port = os.getenv('DB_PORT', '5432')
        name = os.getenv('DB_NAME')
        user = os.getenv('DB_USER')
        password = os.getenv('DB_PASSWORD')
        return f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{name}"
    
    # Default to SQLite
    db_path = os.getenv('DATABASE_PATH', 'data/reality_checker.db')
    # Create data directory if it doesn't exist
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    return f"sqlite+aiosqlite:///{db_path}"


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.
    """
    url = get_database_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """Run migrations with a database connection."""
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Run migrations in async mode."""
    database_url = get_database_url()
    
    # Configure engine based on database type
    if database_url.startswith('sqlite'):
        connectable = create_async_engine(
            database_url,
            poolclass=pool.StaticPool,
            connect_args={"check_same_thread": False}
        )
    else:
        connectable = create_async_engine(database_url)

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()