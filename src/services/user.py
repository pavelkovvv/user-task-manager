from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from logs import logger
from src.crud import user as user_crud
from src.models import User
from src.schemas.user import UserCreate

log = logger.getChild("services.user")


async def create_user(db: AsyncSession, data: UserCreate) -> User:
    """Создание объекта пользователя"""
    try:
        async with db.begin():
            user = await user_crud.create_user(db, email=str(data.email), name=data.name)
    except IntegrityError as exc:
        log.warning("Конфликт при создании пользователя: email=%s уже существует", data.email)
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Пользователь с данным email уже существует",
        ) from exc

    log.info("Создан пользователь id=%s email=%s", user.id, user.email)
    return user


async def get_user(db: AsyncSession, user_id: int) -> type[User]:
    """Получить объект пользователя"""
    user = await user_crud.get_user_by_id(db, user_id)
    if user is None:
        log.warning("Пользователь не найден: user_id=%s", user_id)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")
    return user
