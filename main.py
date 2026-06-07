from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from settings import config_loader
from src.database import engine
from src.routers import api_v1_router


@asynccontextmanager
async def lifespan(_app: FastAPI):
    yield
    await engine.dispose()


def create_app() -> FastAPI:
    app = FastAPI(
        title="user-task-manager",
        version="0.0.1",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_v1_router)

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
