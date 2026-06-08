from collections.abc import AsyncGenerator
from typing import Any, cast

import pytest
from httpx import ASGITransport, AsyncClient
from main import app
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from settings import config_loader
from src.database import get_obj_db
from tests.db import get_test_database_name, test_engine

API_PREFIX = ""
TEST_EMAIL = "user@example.com"

_TRUNCATE_TABLES = text('TRUNCATE TABLE task, "user" RESTART IDENTITY CASCADE')


def _test_database_setup_hint() -> str:
    db_name = get_test_database_name()
    return f"  createdb {db_name}\n  POSTGRES_DB_NAME={db_name} alembic upgrade head"


@pytest.fixture(scope="session", autouse=True)
def ensure_test_database_isolated() -> None:
    prod_db_name = config_loader("POSTGRES_DB_NAME")
    test_db_name = get_test_database_name()
    if prod_db_name == test_db_name:
        pytest.fail(
            f"Тесты должны использовать отдельную БД: POSTGRES_TEST_DB_NAME "
            f"({test_db_name!r}) совпадает с POSTGRES_DB_NAME."
        )


@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession]:
    """Чистые таблицы на старт теста; изменения внутри теста откатываются в конце."""
    try:
        async with test_engine.begin() as connection:
            await connection.execute(_TRUNCATE_TABLES)
    except Exception as exc:
        if "does not exist" in str(exc):
            pytest.fail(
                f"Тестовая БД {get_test_database_name()!r} не найдена.\n"
                f"Создайте БД и примените миграции:\n{_test_database_setup_hint()}"
            )
        raise

    async with test_engine.connect() as connection:
        transaction = await connection.begin()
        session = AsyncSession(
            bind=connection,
            expire_on_commit=False,
            join_transaction_mode="create_savepoint",
        )
        try:
            yield session
        finally:
            await session.close()
            await transaction.rollback()


@pytest.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient]:
    async def override_get_obj_db() -> AsyncGenerator[AsyncSession]:
        yield db_session

    app.dependency_overrides[get_obj_db] = override_get_obj_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as http_client:
        yield http_client
    app.dependency_overrides.clear()


@pytest.fixture
def test_email() -> str:
    return TEST_EMAIL


async def create_user(client: AsyncClient, email: str, name: str = "Ivan") -> dict[str, Any]:
    response = await client.post(f"{API_PREFIX}/users", json={"email": email, "name": name})
    response.raise_for_status()
    return cast(dict[str, Any], response.json())


async def create_task(
    client: AsyncClient,
    user_id: int,
    title: str,
    description: str | None = None,
) -> dict[str, Any]:
    response = await client.post(
        f"{API_PREFIX}/users/{user_id}/tasks",
        json={"title": title, "description": description},
    )
    response.raise_for_status()
    return cast(dict[str, Any], response.json())
