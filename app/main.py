from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api import applications, auth, candidates, jobs
from app.core.config import settings
from app.core.exceptions import setup_exception_handlers
from app.core.middleware import setup_middleware
from app.db.base import Base
from app.db.init_db import seed_initial_data
from app.db.session import AsyncSessionLocal, engine


@asynccontextmanager
async def lifespan(_: FastAPI):
    if settings.AUTO_CREATE_TABLES:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as session:
        await seed_initial_data(session)

    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

setup_middleware(app)
setup_exception_handlers(app)

app.include_router(auth.router, prefix=settings.API_V1_STR)
app.include_router(candidates.router, prefix=settings.API_V1_STR)
app.include_router(jobs.router, prefix=settings.API_V1_STR)
app.include_router(applications.router, prefix=settings.API_V1_STR)


@app.get("/health", tags=["Health"])
async def health_check() -> dict[str, str]:
    return {"status": "ok"}
