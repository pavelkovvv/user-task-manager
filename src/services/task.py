from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from logs import logger
from src.crud import task as task_crud
from src.crud import user as user_crud
from src.models.task import Task, TaskStatus
from src.schemas.task import TaskCreate, TaskList, TaskRead, TaskStats, TaskStatusUpdate

log = logger.getChild("services.task")


async def _ensure_user_exists(db: AsyncSession, user_id: int) -> None:
    """Проверка существования пользователя"""
    user = await user_crud.get_user_by_id(db, user_id)
    if user is None:
        log.warning("Пользователь не найден: user_id=%s", user_id)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")


async def create_task(db: AsyncSession, user_id: int, data: TaskCreate) -> Task:
    """Создание объекта задачи"""
    async with db.begin():
        await _ensure_user_exists(db, user_id)
        task = await task_crud.create_task(
            db,
            user_id=user_id,
            title=data.title,
            description=data.description,
        )
    log.info("Создана задача id=%s user_id=%s title=%r", task.id, user_id, task.title)
    return task


async def list_tasks(
    db: AsyncSession,
    user_id: int,
    *,
    status: TaskStatus | None,
    limit: int,
    offset: int,
) -> TaskList:
    """Получить список задач определенного пользователя"""
    await _ensure_user_exists(db, user_id)
    tasks = await task_crud.list_tasks_by_user(
        db,
        user_id,
        status=status,
        limit=limit,
        offset=offset,
    )
    total = await task_crud.count_tasks_by_user(db, user_id, status=status)
    return TaskList(
        items=[TaskRead.model_validate(task) for task in tasks],
        total=total,
    )


async def get_task_stats(db: AsyncSession, user_id: int) -> TaskStats:
    """Получить статистику по задачам пользователя"""
    await _ensure_user_exists(db, user_id)
    stats = await task_crud.get_task_stats(db, user_id)
    return TaskStats(**stats)


async def update_task_status(db: AsyncSession, task_id: int, data: TaskStatusUpdate) -> Task:
    """Обновление статуса задачи"""
    async with db.begin():
        task = await task_crud.get_task_by_id(db, task_id)
        if task is None:
            log.warning("Задача не найдена: task_id=%s", task_id)
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Задача не найдена")
        task = await task_crud.update_task_status(db, task, data.status)
    log.info("Обновлён статус задачи id=%s -> %s", task_id, data.status.value)
    return task


async def delete_task(db: AsyncSession, task_id: int) -> None:
    """Удаление задачи"""
    async with db.begin():
        task = await task_crud.get_task_by_id(db, task_id)
        if task is None:
            log.warning("Задача не найдена: task_id=%s", task_id)
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Задача не найдена")
        await task_crud.delete_task(db, task)
    log.info("Удалена задача id=%s user_id=%s", task_id, task.user_id)
