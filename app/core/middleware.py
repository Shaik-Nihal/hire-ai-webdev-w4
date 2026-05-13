from time import perf_counter
from uuid import uuid4

from fastapi import FastAPI, Request
from starlette.middleware.cors import CORSMiddleware

from app.core.config import settings


def setup_middleware(app: FastAPI) -> None:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def add_process_time_header(request: Request, call_next):
        request_id = request.headers.get("X-Request-ID") or str(uuid4())
        request.state.request_id = request_id
        start = perf_counter()
        response = await call_next(request)
        response.headers["X-Process-Time"] = f"{perf_counter() - start:.6f}"
        response.headers["X-Request-ID"] = request_id
        return response
