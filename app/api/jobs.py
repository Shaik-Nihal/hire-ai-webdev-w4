from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.security import require_roles
from app.db.session import get_db
from app.models.application import Application
from app.models.candidate import Candidate
from app.models.job import Job
from app.schemas.auth import UserResponse
from app.schemas.job import JobCreate, JobReplaceRequest, JobResponse, JobUpdate

router = APIRouter(prefix="/jobs", tags=["Jobs"])


def _get_or_404(job: Job | None) -> Job:
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    return job


# ══════════════════════════════════════════════════════════════════════════════
# Collection routes
# ══════════════════════════════════════════════════════════════════════════════

@router.get("", response_model=list[JobResponse])
async def list_jobs(
    response: Response,
    current_user: UserResponse = Depends(require_roles("admin", "recruiter", "viewer")),
    job_status: str | None = Query(default=None, alias="status", description="Filter by job status"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> list[Job]:
    """
    Retrieve a paginated list of active (non-archived) job listings.

    Supports filtering by `status` (draft, published, archived).
    Pagination headers `X-Total-Count`, `X-Page`, and `X-Page-Size` are returned.
    """
    filters = [Job.is_archived.is_(False)]
    if job_status is not None:
        filters.append(Job.status == job_status)

    total = await db.scalar(select(func.count()).select_from(Job).where(*filters))
    response.headers["X-Total-Count"] = str(total or 0)
    response.headers["X-Page"] = str(page)
    response.headers["X-Page-Size"] = str(page_size)

    stmt = (
        select(Job)
        .where(*filters)
        .order_by(Job.job_id.desc())
        .limit(page_size)
        .offset((page - 1) * page_size)
    )
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

    Requires 'admin' or 'recruiter' roles. New jobs start with `status = draft`.
    """
    job = Job(**payload.model_dump(), created_by=current_user.email, updated_by=current_user.email)
    db.add(job)
    await db.commit()
    await db.refresh(job)
    return job


# ══════════════════════════════════════════════════════════════════════════════
# Single-resource routes
# ══════════════════════════════════════════════════════════════════════════════

@router.get("/{job_id}", response_model=JobResponse)
async def get_job(
    job_id: int,
    current_user: UserResponse = Depends(require_roles("admin", "recruiter", "viewer")),
    db: AsyncSession = Depends(get_db),
) -> Job:
    """
    Retrieve a single job listing by ID.

    Returns 404 if the job does not exist or has been archived.
    """
    result = await db.execute(select(Job).where(Job.job_id == job_id, Job.is_archived.is_(False)))
    return _get_or_404(result.scalar_one_or_none())


@router.put("/{job_id}", response_model=JobResponse)
async def replace_job(
    job_id: int,
    payload: JobReplaceRequest,
    current_user: UserResponse = Depends(require_roles("admin", "recruiter")),
    db: AsyncSession = Depends(get_db),
) -> Job:
    """
    Fully replace a job listing (all required fields must be supplied).

    Returns 404 if the job does not exist or is archived.
    """
    result = await db.execute(select(Job).where(Job.job_id == job_id, Job.is_archived.is_(False)))
    job = _get_or_404(result.scalar_one_or_none())

    for key, value in payload.model_dump().items():
        setattr(job, key, value)
    job.updated_by = current_user.email

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
    result = await db.execute(select(Job).where(Job.job_id == job_id, Job.is_archived.is_(False)))
    job = _get_or_404(result.scalar_one_or_none())

    updates = payload.model_dump(exclude_unset=True)
    for key, value in updates.items():
        setattr(job, key, value)
    job.updated_by = current_user.email

    await db.commit()
    await db.refresh(job)
    return job


@router.delete("/{job_id}", status_code=status.HTTP_200_OK)
async def delete_job(
    job_id: int,
    current_user: UserResponse = Depends(require_roles("admin")),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """
    Soft-delete a job by setting `is_archived = true`.

    The record is preserved but hidden from all standard list/get queries.
    Requires 'admin' role only.
    """
    result = await db.execute(select(Job).where(Job.job_id == job_id, Job.is_archived.is_(False)))
    job = _get_or_404(result.scalar_one_or_none())

    job.is_archived = True
    job.status = "archived"
    job.updated_by = current_user.email
    await db.commit()
    return {"message": "Job archived successfully"}


@router.patch("/{job_id}/publish", response_model=JobResponse)
async def publish_job(
    job_id: int,
    current_user: UserResponse = Depends(require_roles("admin", "recruiter")),
    db: AsyncSession = Depends(get_db),
) -> Job:
    """
    Publish a draft job listing, making it visible to candidates.

    Sets `status = published`. Returns 400 if the job is already published or archived.
    """
    result = await db.execute(select(Job).where(Job.job_id == job_id, Job.is_archived.is_(False)))
    job = _get_or_404(result.scalar_one_or_none())

    if job.status == "published":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Job is already published")

    job.status = "published"
    job.updated_by = current_user.email
    await db.commit()
    await db.refresh(job)
    return job


@router.patch("/{job_id}/archive", response_model=JobResponse)
async def archive_job(
    job_id: int,
    current_user: UserResponse = Depends(require_roles("admin", "recruiter")),
    db: AsyncSession = Depends(get_db),
) -> Job:
    """
    Archive a job listing, removing it from active search results.

    Sets `status = archived` and `is_archived = true`.
    Returns 400 if the job is already archived.
    """
    result = await db.execute(select(Job).where(Job.job_id == job_id))
    job = _get_or_404(result.scalar_one_or_none())

    if job.is_archived:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Job is already archived")

    job.status = "archived"
    job.is_archived = True
    job.updated_by = current_user.email
    await db.commit()
    await db.refresh(job)
    return job


@router.post("/{job_id}/clone", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
async def clone_job(
    job_id: int,
    current_user: UserResponse = Depends(require_roles("admin", "recruiter")),
    db: AsyncSession = Depends(get_db),
) -> Job:
    """
    Clone an existing job listing into a new draft.

    Copies `role`, `required_skills`, `min_experience`, and `description`.
    The new job starts with `status = draft` and no applications.
    """
    result = await db.execute(select(Job).where(Job.job_id == job_id))
    source = _get_or_404(result.scalar_one_or_none())

    cloned = Job(
        role=source.role,
        required_skills=source.required_skills,
        min_experience=source.min_experience,
        description=source.description,
        status="draft",
        is_archived=False,
        created_by=current_user.email,
        updated_by=current_user.email,
    )
    db.add(cloned)
    await db.commit()
    await db.refresh(cloned)
    return cloned


@router.get("/{job_id}/applicants")
async def get_job_applicants(
    job_id: int,
    response: Response,
    current_user: UserResponse = Depends(require_roles("admin", "recruiter", "viewer")),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Retrieve all applicants for a specific job with pagination.

    Returns job details alongside a paginated list of applicants (candidate + application info).
    Pagination headers `X-Total-Count`, `X-Page`, and `X-Page-Size` are returned.
    """
    job_result = await db.execute(select(Job).where(Job.job_id == job_id))
    job = _get_or_404(job_result.scalar_one_or_none())

    count_stmt = select(func.count()).select_from(Application).where(Application.job_id == job_id)
    total = await db.scalar(count_stmt)

    stmt = (
        select(Application)
        .where(Application.job_id == job_id)
        .options(selectinload(Application.candidate))
        .order_by(Application.application_id.desc())
        .limit(page_size)
        .offset((page - 1) * page_size)
    )
    apps_result = await db.execute(stmt)
    applications = apps_result.scalars().all()

    response.headers["X-Total-Count"] = str(total or 0)
    response.headers["X-Page"] = str(page)
    response.headers["X-Page-Size"] = str(page_size)

    applicants = []
    for app in applications:
        c = app.candidate
        applicants.append(
            {
                "application_id": app.application_id,
                "status": app.status,
                "application_date": app.application_date,
                "candidate": {
                    "candidate_id": c.candidate_id,
                    "name": c.name,
                    "email": c.email,
                    "skills": c.skills,
                    "experience_years": c.experience_years,
                }
                if c
                else None,
            }
        )

    return {
        "job": {
            "job_id": job.job_id,
            "role": job.role,
            "required_skills": job.required_skills,
            "min_experience": job.min_experience,
            "status": job.status,
        },
        "applicants": applicants,
        "total": total or 0,
        "page": page,
        "page_size": page_size,
    }
