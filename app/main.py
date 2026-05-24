from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api import applications, auth, candidates, jobs
from app.core.config import settings
from app.core.exceptions import setup_exception_handlers
from app.core.middleware import setup_middleware


@asynccontextmanager
async def lifespan(_: FastAPI):
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


@app.get("/", tags=["Meta"])
async def root_info() -> dict[str, object]:
    base = settings.API_V1_STR
    return {
        "service": settings.PROJECT_NAME,
        "status": "ok",
        "docs": "/docs",
        "redoc": "/redoc",
        "openapi": f"{base}/openapi.json",
        "key_endpoints": [
            {"method": "POST", "path": f"{base}/auth/register", "purpose": "Register recruiter user"},
            {"method": "POST", "path": f"{base}/auth/login", "purpose": "Login and receive JWT token"},
            {"method": "GET", "path": f"{base}/auth/me", "purpose": "Get current authenticated user"},
            {"method": "GET", "path": f"{base}/candidates", "purpose": "List candidates"},
            {"method": "GET", "path": f"{base}/jobs", "purpose": "List jobs"},
            {"method": "GET", "path": f"{base}/applications", "purpose": "List job applications"},
            {"method": "GET", "path": "/health", "purpose": "Health check"},
        ],
    }
