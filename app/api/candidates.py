from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.security import require_roles
from app.db.session import get_db
from app.models.candidate import Candidate
from app.models.score import Score
from app.schemas.auth import UserResponse
from app.schemas.candidate import CandidateCreate, CandidateFullResponse, CandidateResponse, CandidateUpdate

router = APIRouter(prefix="/candidates", tags=["Candidates"])


@router.get("", response_model=list[CandidateResponse])
async def list_candidates(
    response: Response,
    current_user: UserResponse = Depends(require_roles("admin", "recruiter", "viewer")),
    skills: str | None = Query(default=None, description="Comma-separated skills to match"),
    min_score: float | None = Query(default=None, ge=0, description="Minimum score filter"),
    max_score: float | None = Query(default=None, ge=0, description="Maximum score filter"),
    job_id: int | None = Query(default=None, description="Job id for score filtering"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> list[Candidate]:
    filters = []

    skill_tokens = [token.strip() for token in skills.split(",")] if skills else []
    if skill_tokens:
        filters.append(or_(*[Candidate.skills.ilike(f"%{token}%") for token in skill_tokens]))

    if min_score is not None or max_score is not None or job_id is not None:
        score_filters = []
        if min_score is not None:
            score_filters.append(Score.score >= min_score)
        if max_score is not None:
            score_filters.append(Score.score <= max_score)
        if job_id is not None:
            score_filters.append(Score.job_id == job_id)

        score_candidates = select(Score.candidate_id).where(*score_filters).distinct()
        filters.append(Candidate.candidate_id.in_(score_candidates))

    count_stmt = select(func.count()).select_from(Candidate)
    if filters:
        count_stmt = count_stmt.where(*filters)
    total = await db.scalar(count_stmt)

    stmt = select(Candidate)
    if filters:
        stmt = stmt.where(*filters)
    stmt = stmt.order_by(Candidate.candidate_id.desc())
    stmt = stmt.limit(page_size).offset((page - 1) * page_size)

    response.headers["X-Total-Count"] = str(total or 0)
    response.headers["X-Page"] = str(page)
    response.headers["X-Page-Size"] = str(page_size)

    result = await db.execute(stmt)
    return list(result.scalars().all())


@router.post("", response_model=CandidateResponse, status_code=status.HTTP_201_CREATED)
async def create_candidate(
    payload: CandidateCreate,
    current_user: UserResponse = Depends(require_roles("admin", "recruiter")),
    db: AsyncSession = Depends(get_db),
) -> Candidate:
    candidate = Candidate(**payload.model_dump())
    db.add(candidate)
    await db.commit()
    await db.refresh(candidate)
    return candidate


@router.patch("/{candidate_id}", response_model=CandidateResponse)
async def update_candidate(
    candidate_id: int,
    payload: CandidateUpdate,
    current_user: UserResponse = Depends(require_roles("admin", "recruiter")),
    db: AsyncSession = Depends(get_db),
) -> Candidate:
    result = await db.execute(select(Candidate).where(Candidate.candidate_id == candidate_id))
    candidate = result.scalar_one_or_none()
    if candidate is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidate not found")

    updates = payload.model_dump(exclude_unset=True)
    for key, value in updates.items():
        setattr(candidate, key, value)

    await db.commit()
    await db.refresh(candidate)
    return candidate


@router.get("/{candidate_id}/full", response_model=CandidateFullResponse)
async def get_candidate_full(
    candidate_id: int,
    current_user: UserResponse = Depends(require_roles("admin", "recruiter", "viewer")),
    db: AsyncSession = Depends(get_db),
) -> Candidate:
    stmt = (
        select(Candidate)
        .where(Candidate.candidate_id == candidate_id)
        .options(selectinload(Candidate.applications), selectinload(Candidate.scores))
    )
    result = await db.execute(stmt)
    candidate = result.scalar_one_or_none()
    if candidate is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidate not found")
    return candidate
