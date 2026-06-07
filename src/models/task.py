import enum
from datetime import datetime
from typing import Any

from sqlalchemy import CheckConstraint, DateTime, Enum, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, validates

from src.database import Base


class TaskStatus(enum.StrEnum):
    NEW = "new"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    CANCELLED = "cancelled"


class Task(Base):
    """Модель задачи"""

    __tablename__ = "task"
    __table_args__ = (CheckConstraint("char_length(title) > 0", name="ck_task_title_not_empty"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str | None] = mapped_column(String(256), nullable=True)
    status: Mapped[TaskStatus] = mapped_column(
        Enum(TaskStatus, native_enum=False, length=20),
        nullable=False,
        default=TaskStatus.NEW,
        server_default=TaskStatus.NEW.value,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    def __init__(self, **kwargs: Any) -> None:
        kwargs.setdefault("status", TaskStatus.NEW)
        super().__init__(**kwargs)

    @validates("title")
    def validate_title(self, _key: str, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("title обязателен")
        return value
