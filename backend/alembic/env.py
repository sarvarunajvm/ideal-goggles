"""Alembic environment configuration for Ideal Goggles."""

import sys
from logging.config import fileConfig
from pathlib import Path

from sqlalchemy import engine_from_config, pool

from alembic import context

# Add the backend src directory to the path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir / "src"))

from src.core.config import settings

# this is the Alembic Config object
config = context.config

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Override sqlalchemy.url with app settings ONLY if not already set
# This allows connection.py to override the URL for tests and custom paths
if not config.get_main_option("sqlalchemy.url") or config.get_main_option("sqlalchemy.url") == "sqlite:///./data/photos.db":
    config.set_main_option("sqlalchemy.url", f"sqlite:///{settings.DATA_DIR / 'photos.db'}")

# NOTE: We're using raw SQLite, not SQLAlchemy ORM models
# For Alembic to work with explicit SQL migrations instead of autogenerate,
# we set target_metadata to None
target_metadata = None


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_as_batch=True,  # Important for SQLite
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.
    """
    import logging
    logger = logging.getLogger('alembic.env')
    logger.info(f"Running migrations online for: {config.get_main_option('sqlalchemy.url')}")
    
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    # Use begin() to get an auto-committing transaction
    with connectable.begin() as connection:
        logger.info("Connection established, configuring context")
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            render_as_batch=True,  # Important for SQLite
        )

        logger.info("Running migrations...")
        context.run_migrations()
        logger.info("Migrations completed")


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
