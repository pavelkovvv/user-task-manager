from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator

from src.models.task import TaskStatus


class TaskCreate(BaseModel):
    title: str
    description: str | None = None

    @field_validator("title")
    @classmethod
    def validate_title(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Поле 'title' обязательно для заполнения")
        return value


class TaskRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    title: str
    description: str | None
    status: TaskStatus
    created_at: datetime
    updated_at: datetime | None


class TaskStatusUpdate(BaseModel):
    status: TaskStatus


class TaskList(BaseModel):
    items: list[TaskRead]
    total: int


class TaskStats(BaseModel):
    total: int
    new: int
    in_progress: int
    done: int
    cancelled: int
