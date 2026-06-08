from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_obj_db
from src.schemas.common import OkResponse
from src.schemas.task import TaskRead, TaskStatusUpdate
from src.services import task as task_service

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.patch("/{task_id}/status", response_model=TaskRead, summary="Обновить статус задачи")
async def update_task_status(
    task_id: int,
    body: TaskStatusUpdate,
    db: AsyncSession = Depends(get_obj_db),
) -> TaskRead:
    task = await task_service.update_task_status(db, task_id, body)
    return TaskRead.model_validate(task)


@router.delete("/{task_id}", response_model=OkResponse, summary="Удалить задачу")
async def delete_task(
    task_id: int,
    db: AsyncSession = Depends(get_obj_db),
) -> OkResponse:
    await task_service.delete_task(db, task_id)
    return OkResponse()
