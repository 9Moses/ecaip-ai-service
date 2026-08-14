from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.api.v1 import router as v1_router
from prometheus_fastapi_instrumentator import Instrumentator
from app.core.tracing import setup_tracing

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # before startup: place for future init db, redis
    yield
    # Shutdown: place for future cleanup


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="Enterprise AI Claims Intelligence Platform — API",
    lifespan=lifespan,
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

setup_tracing("eacip-api", app=app)

Instrumentator().instrument(app).expose(app, endpoint="/metrics", include_in_schema=False)

app.include_router(v1_router, prefix=settings.api_v1_prefix)
