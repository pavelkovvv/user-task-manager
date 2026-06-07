from datetime import datetime

from pydantic import EmailStr, TypeAdapter
from sqlalchemy import CheckConstraint, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column, validates

from src.database import Base

_email_validator = TypeAdapter(EmailStr)


class User(Base):
    """Модель пользователя"""

    __tablename__ = "user"
    __table_args__ = (CheckConstraint("char_length(name) > 0", name="ck_user_name_not_empty"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())

    @validates("email")
    def validate_email(self, _key: str, value: str) -> str:
        return str(_email_validator.validate_python(value))

    @validates("name")
    def validate_name(self, _key: str, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("name не должен быть пустым")
        return value
