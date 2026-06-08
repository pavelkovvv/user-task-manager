"""Агрегирующий роутер API."""

from fastapi import APIRouter

from src.routers.tasks import router as tasks_router
from src.routers.users import router as users_router

api_router = APIRouter()
api_router.include_router(users_router)
api_router.include_router(tasks_router)

__all__ = ("api_router",)
