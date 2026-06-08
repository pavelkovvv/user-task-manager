from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, Request
from starlette.middleware.cors import CORSMiddleware

from logs import log_writer, logger
from settings import config_loader
from src.database import engine
from src.routers import api_router

http_logger = logger.getChild("http")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    logger.info("Запуск приложения user-task-manager")
    yield
    logger.info("Остановка приложения user-task-manager")
    await engine.dispose()
    log_writer.shutdown()


def create_app() -> FastAPI:
    app = FastAPI(
        title="user-task-manager",
        version="0.0.1",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        response = await call_next(request)
        http_logger.info(
            "%s %s -> %s",
            request.method,
            request.url.path,
            response.status_code,
        )
        return response

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_router)

    return app


app = create_app()


def run() -> None:
    host = config_loader("FASTAPI_HOST")
    port = int(config_loader("FASTAPI_PORT"))
    reload = str(config_loader("FASTAPI_RELOAD")).lower() == "true"

    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=reload,
    )


if __name__ == "__main__":
    run()
