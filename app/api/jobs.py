from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import require_roles
from app.db.session import get_db
from app.models.job import Job
from app.schemas.auth import UserResponse
from app.schemas.job import JobCreate, JobResponse, JobUpdate

router = APIRouter(prefix="/jobs", tags=["Jobs"])


@router.get("", response_model=list[JobResponse])
async def list_jobs(
    response: Response,
    current_user: UserResponse = Depends(require_roles("admin", "recruiter", "viewer")),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> list[Job]:
    """
    Retrieve a paginated list of job listings.
    
    Returns basic job details like role, required skills, and min experience.
    Pagination headers `X-Total-Count`, `X-Page`, and `X-Page-Size` are returned in the response.
    """
    total = await db.scalar(select(func.count()).select_from(Job))
    response.headers["X-Total-Count"] = str(total or 0)
    response.headers["X-Page"] = str(page)
    response.headers["X-Page-Size"] = str(page_size)

    stmt = select(Job).order_by(Job.job_id.desc()).limit(page_size).offset((page - 1) * page_size)
    result = await db.execute(stmt)
    return list(result.scalars().all())


@router.post("", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
async def create_job(
    payload: JobCreate,
    current_user: UserResponse = Depends(require_roles("admin", "recruiter")),
    db: AsyncSession = Depends(get_db),
) -> Job:
    """
    Create a new job listing.
    
    Requires 'admin' or 'recruiter' roles. Defines role title, required skills, and min experience.
    """
    job = Job(**payload.model_dump())
    db.add(job)
    await db.commit()
    await db.refresh(job)
    return job


@router.patch("/{job_id}", response_model=JobResponse)
async def update_job(
    job_id: int,
    payload: JobUpdate,
    current_user: UserResponse = Depends(require_roles("admin", "recruiter")),
    db: AsyncSession = Depends(get_db),
) -> Job:
    """
    Partially update an existing job listing's details.
    
    Requires 'admin' or 'recruiter' roles. Updates only fields provided in request body.
    """
    result = await db.execute(select(Job).where(Job.job_id == job_id))
    job = result.scalar_one_or_none()
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    updates = payload.model_dump(exclude_unset=True)
    for key, value in updates.items():
        setattr(job, key, value)

    await db.commit()
    await db.refresh(job)
    return job
