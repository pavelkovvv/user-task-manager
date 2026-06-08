import os

from sqlalchemy.engine import URL
from sqlalchemy.ext.asyncio import create_async_engine

from settings import config_loader

DEFAULT_TEST_DB_NAME = "user-task-manager-test"


def get_test_database_name() -> str:
    return str(os.getenv("POSTGRES_TEST_DB_NAME") or config_loader("POSTGRES_TEST_DB_NAME") or DEFAULT_TEST_DB_NAME)


def build_test_database_url() -> URL:
    return URL.create(
        drivername="postgresql+asyncpg",
        username=config_loader("POSTGRES_DB_USER"),
        password=config_loader("POSTGRES_DB_PASSWORD"),
        host=config_loader("POSTGRES_DB_HOST"),
        port=int(config_loader("POSTGRES_DB_PORT")),
        database=get_test_database_name(),
    )


test_engine = create_async_engine(build_test_database_url(), pool_pre_ping=True)
