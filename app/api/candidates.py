from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.candidate import Candidate
from app.schemas.candidate import CandidateResponse

router = APIRouter(prefix="/candidates", tags=["Candidates"])


@router.get("", response_model=list[CandidateResponse])
async def list_candidates(db: AsyncSession = Depends(get_db)) -> list[Candidate]:
    result = await db.execute(select(Candidate).order_by(Candidate.created_at.desc()))
    return list(result.scalars().all())
