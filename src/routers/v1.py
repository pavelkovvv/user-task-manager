"""Агрегирующий роутер для API версии v1"""

from fastapi import APIRouter

# Все endpoint'ы v1 подключаются под единым префиксом версии.
# Любой новый router v1 подключается только здесь — так проще контролировать
# публичный API и избежать рассинхронизации префиксов
api_v1_router = APIRouter(prefix="/api/v1")

__all__ = ("api_v1_router",)
