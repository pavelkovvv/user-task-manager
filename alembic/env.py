import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import create_async_engine

from src.database import SQLALCHEMY_DATABASE_URI, Base  # noqa
from src.models import *  # noqa

# Alembic Config
config = context.config

# Логирование
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Metadata для autogenerate
target_metadata = Base.metadata


def get_sync_url(async_url: str) -> str:
    """Convert async DB URL to sync URL for offline migrations."""
    if async_url.startswith("postgresql+asyncpg://"):
        return async_url.replace("postgresql+asyncpg://", "postgresql://", 1)
    return async_url


def run_migrations_offline() -> None:
    """Run migrations in offline mode."""
    context.configure(
        url=get_sync_url(SQLALCHEMY_DATABASE_URI),
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in online mode with async engine."""
    # Keep Alembic config URL aligned with runtime config.
    config.set_main_option("sqlalchemy.url", get_sync_url(SQLALCHEMY_DATABASE_URI))

    connectable = create_async_engine(
        SQLALCHEMY_DATABASE_URI,
        poolclass=pool.NullPool,
    )

    async def run_async_migrations() -> None:
        async with connectable.connect() as connection:
            await connection.run_sync(do_run_migrations)
        await connectable.dispose()

    def do_run_migrations(connection) -> None:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )

        with context.begin_transaction():
            context.run_migrations()

    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
