from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_obj_db
from src.models.task import TaskStatus
from src.schemas.task import TaskCreate, TaskList, TaskRead, TaskStats
from src.schemas.user import UserCreate, UserRead
from src.services import task as task_service
from src.services import user as user_service

router = APIRouter(prefix="/users", tags=["users"])


@router.post("", response_model=UserRead, status_code=status.HTTP_201_CREATED, summary="Создание пользователя")
async def create_user(
    body: UserCreate,
    db: AsyncSession = Depends(get_obj_db),
) -> UserRead:
    user = await user_service.create_user(db, body)
    return UserRead.model_validate(user)


@router.get("/{user_id}/tasks/stats", response_model=TaskStats, summary="Получить статистику по задачам пользователя")
async def get_user_task_stats(
    user_id: int,
    db: AsyncSession = Depends(get_obj_db),
) -> TaskStats:
    return await task_service.get_task_stats(db, user_id)


@router.post("/{user_id}/tasks", response_model=TaskRead, status_code=status.HTTP_201_CREATED, summary="Создать задачу")
async def create_task(
    user_id: int,
    body: TaskCreate,
    db: AsyncSession = Depends(get_obj_db),
) -> TaskRead:
    task = await task_service.create_task(db, user_id, body)
    return TaskRead.model_validate(task)


@router.get("/{user_id}/tasks", response_model=TaskList, summary="Получить список задач пользователя")
async def list_user_tasks(
    user_id: int,
    status: TaskStatus | None = None,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_obj_db),
) -> TaskList:
    return await task_service.list_tasks(db, user_id, status=status, limit=limit, offset=offset)


@router.get("/{user_id}", response_model=UserRead, summary="Получить объект пользователя")
async def get_user(
    user_id: int,
    db: AsyncSession = Depends(get_obj_db),
) -> UserRead:
    user = await user_service.get_user(db, user_id)
    return UserRead.model_validate(user)
