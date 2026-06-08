from datetime import UTC

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.task import Task, TaskStatus


async def get_task_by_id(db: AsyncSession, task_id: int) -> Task | None:
    return await db.get(Task, task_id)


async def create_task(
    db: AsyncSession,
    user_id: int,
    title: str,
    description: str | None,
) -> Task:
    task = Task(user_id=user_id, title=title, description=description)
    db.add(task)
    await db.flush()
    await db.refresh(task)
    return task


def _tasks_by_user_filter(user_id: int, status: TaskStatus | None):
    stmt = select(Task).where(Task.user_id == user_id)
    if status is not None:
        stmt = stmt.where(Task.status == status)
    return stmt


async def count_tasks_by_user(
    db: AsyncSession,
    user_id: int,
    *,
    status: TaskStatus | None = None,
) -> int:
    stmt = select(func.count()).where(Task.user_id == user_id)
    if status is not None:
        stmt = stmt.where(Task.status == status)
    result = await db.execute(stmt)
    return result.scalar_one()


async def list_tasks_by_user(
    db: AsyncSession,
    user_id: int,
    *,
    status: TaskStatus | None = None,
    limit: int,
    offset: int,
) -> list[Task]:
    stmt = _tasks_by_user_filter(user_id, status).order_by(Task.id).limit(limit).offset(offset)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def update_task_status(db: AsyncSession, task: Task, status: TaskStatus) -> Task:
    from datetime import datetime

    task.status = status
    task.updated_at = datetime.now(UTC).replace(tzinfo=None)
    await db.flush()
    await db.refresh(task)
    return task


async def delete_task(db: AsyncSession, task: Task) -> None:
    await db.delete(task)
    await db.flush()


async def get_task_stats(db: AsyncSession, user_id: int) -> dict[str, int]:
    result = await db.execute(select(Task.status, func.count()).where(Task.user_id == user_id).group_by(Task.status))
    counts = {status.value: count for status, count in result.all()}
    return {
        "total": sum(counts.values()),
        "new": counts.get(TaskStatus.NEW.value, 0),
        "in_progress": counts.get(TaskStatus.IN_PROGRESS.value, 0),
        "done": counts.get(TaskStatus.DONE.value, 0),
        "cancelled": counts.get(TaskStatus.CANCELLED.value, 0),
    }
