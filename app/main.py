import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api import applications, auth, candidates, jobs
from app.core.config import settings
from app.core.exceptions import setup_exception_handlers
from app.core.middleware import setup_middleware

UPLOAD_DIR = "uploads/resumes"


@asynccontextmanager
async def lifespan(_: FastAPI):
    # Ensure upload directory exists on startup
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    yield
    from app.db.session import engine
    await engine.dispose()


app = FastAPI(
    title=settings.PROJECT_NAME,
    version="2.0.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

setup_middleware(app)
setup_exception_handlers(app)

# Serve uploaded files as static assets (e.g. resumes)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

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
        "version": "2.0.0",
        "status": "ok",
        "docs": "/docs",
        "redoc": "/redoc",
        "openapi": f"{base}/openapi.json",
        "key_endpoints": [
            # Auth
            {"method": "POST", "path": f"{base}/auth/register", "purpose": "Register recruiter user"},
            {"method": "POST", "path": f"{base}/auth/login", "purpose": "Login and receive JWT token"},
            {"method": "POST", "path": f"{base}/auth/refresh", "purpose": "Refresh access token"},
            {"method": "GET", "path": f"{base}/auth/me", "purpose": "Get current authenticated user"},
            {"method": "POST", "path": f"{base}/auth/logout", "purpose": "Logout current user"},
            # Candidates
            {"method": "GET", "path": f"{base}/candidates", "purpose": "List candidates (filterable)"},
            {"method": "POST", "path": f"{base}/candidates", "purpose": "Create candidate"},
            {"method": "GET", "path": f"{base}/candidates/{{id}}", "purpose": "Get single candidate"},
            {"method": "PUT", "path": f"{base}/candidates/{{id}}", "purpose": "Replace candidate (all fields)"},
            {"method": "PATCH", "path": f"{base}/candidates/{{id}}", "purpose": "Partial update candidate"},
            {"method": "DELETE", "path": f"{base}/candidates/{{id}}", "purpose": "Soft-delete candidate"},
            {"method": "PATCH", "path": f"{base}/candidates/{{id}}/status", "purpose": "Update candidate lifecycle status"},
            {"method": "PATCH", "path": f"{base}/candidates/bulk-status", "purpose": "Bulk status update"},
            {"method": "PATCH", "path": f"{base}/candidates/bulk-assign-job", "purpose": "Bulk assign candidates to job"},
            {"method": "POST", "path": f"{base}/candidates/{{id}}/notes", "purpose": "Add recruiter note"},
            {"method": "POST", "path": f"{base}/candidates/{{id}}/resume", "purpose": "Upload resume file"},
            {"method": "GET", "path": f"{base}/candidates/{{id}}/applications", "purpose": "All applications for candidate"},
            {"method": "GET", "path": f"{base}/candidates/{{id}}/activity", "purpose": "Candidate activity timeline"},
            {"method": "GET", "path": f"{base}/candidates/{{id}}/similar", "purpose": "Similar candidates"},
            {"method": "GET", "path": f"{base}/candidates/{{id}}/full", "purpose": "Full profile with scores and applications"},
            # Jobs
            {"method": "GET", "path": f"{base}/jobs", "purpose": "List jobs"},
            {"method": "POST", "path": f"{base}/jobs", "purpose": "Create job"},
            {"method": "GET", "path": f"{base}/jobs/{{id}}", "purpose": "Get single job"},
            {"method": "PUT", "path": f"{base}/jobs/{{id}}", "purpose": "Replace job (all fields)"},
            {"method": "PATCH", "path": f"{base}/jobs/{{id}}", "purpose": "Partial update job"},
            {"method": "DELETE", "path": f"{base}/jobs/{{id}}", "purpose": "Archive job (soft delete)"},
            {"method": "PATCH", "path": f"{base}/jobs/{{id}}/publish", "purpose": "Publish draft job"},
            {"method": "PATCH", "path": f"{base}/jobs/{{id}}/archive", "purpose": "Archive job"},
            {"method": "POST", "path": f"{base}/jobs/{{id}}/clone", "purpose": "Clone job listing"},
            {"method": "GET", "path": f"{base}/jobs/{{id}}/applicants", "purpose": "List job applicants"},
            # Applications
            {"method": "GET", "path": f"{base}/applications", "purpose": "List job applications"},
            {"method": "POST", "path": f"{base}/applications", "purpose": "Create application"},
            {"method": "GET", "path": f"{base}/applications/{{id}}", "purpose": "Get single application with details"},
            {"method": "PATCH", "path": f"{base}/applications/{{id}}", "purpose": "Update application"},
            {"method": "GET", "path": f"{base}/applications/pipeline", "purpose": "Kanban pipeline counts"},
            {"method": "GET", "path": f"{base}/applications/timeline", "purpose": "Recruitment activity timeline"},
            # Health
            {"method": "GET", "path": "/health", "purpose": "Health check"},
        ],
    }
