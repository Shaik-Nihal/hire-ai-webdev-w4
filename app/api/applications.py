from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.application import Application
from app.schemas.application import ApplicationResponse

router = APIRouter(prefix="/applications", tags=["Applications"])


@router.get("", response_model=list[ApplicationResponse])
async def list_applications(db: AsyncSession = Depends(get_db)) -> list[Application]:
    result = await db.execute(select(Application).order_by(Application.application_id.desc()))
    return list(result.scalars().all())
