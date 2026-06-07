from collections.abc import AsyncGenerator

from sqlalchemy.engine import URL
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from settings import config_loader

REQUIRED_DB_CONFIG = (
    "POSTGRES_DB_USER",
    "POSTGRES_DB_PASSWORD",
    "POSTGRES_DB_HOST",
    "POSTGRES_DB_PORT",
    "POSTGRES_DB_NAME",
)


def _required_config(key: str) -> str:
    value = config_loader(key)
    if value is None or str(value).strip() == "":
        raise ValueError(f"Отсутствует необходимое поле конфигурации базы данных: {key}")
    return str(value)


db_config = {key: _required_config(key) for key in REQUIRED_DB_CONFIG}

sqlalchemy_url = URL.create(
    drivername="postgresql+asyncpg",
    username=db_config["POSTGRES_DB_USER"],
    password=db_config["POSTGRES_DB_PASSWORD"],
    host=db_config["POSTGRES_DB_HOST"],
    port=int(db_config["POSTGRES_DB_PORT"]),
    database=db_config["POSTGRES_DB_NAME"],
)

SQLALCHEMY_DATABASE_URI = sqlalchemy_url.render_as_string(hide_password=False)

engine = create_async_engine(
    sqlalchemy_url,
    pool_pre_ping=True,
    pool_size=int(config_loader("POSTGRES_POOL_SIZE", 10)),
    max_overflow=int(config_loader("POSTGRES_MAX_OVERFLOW", 20)),
    pool_recycle=int(config_loader("POSTGRES_POOL_RECYCLE_SEC", 1800)),
)

SessionLocal = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_obj_db() -> AsyncGenerator[AsyncSession]:
    async with SessionLocal() as session:
        yield session
