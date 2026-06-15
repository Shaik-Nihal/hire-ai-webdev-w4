from collections.abc import AsyncGenerator
from uuid import uuid4

from sqlalchemy.engine.url import make_url
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.config import settings


def _uses_pooler(database_url: str) -> bool:
    url = make_url(database_url)
    host = (url.host or "").lower()
    return url.port == 6543 or "pooler" in host


engine_kwargs: dict[str, object] = {"pool_pre_ping": True}
connect_args: dict[str, object] = {}

if _uses_pooler(settings.DATABASE_URL):
    # PgBouncer-style poolers don't support prepared statements well.
    connect_args = {
        "statement_cache_size": 0,
        "prepared_statement_cache_size": 0,
        "prepared_statement_name_func": lambda: f"__asyncpg_{uuid4()}__",
    }
    engine_kwargs["poolclass"] = NullPool
else:
    engine_kwargs["pool_size"] = settings.DATABASE_POOL_SIZE
    engine_kwargs["max_overflow"] = settings.DATABASE_MAX_OVERFLOW
    engine_kwargs["pool_recycle"] = settings.DATABASE_POOL_RECYCLE
    engine_kwargs["pool_timeout"] = settings.DATABASE_POOL_TIMEOUT

engine = create_async_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    **engine_kwargs,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session
