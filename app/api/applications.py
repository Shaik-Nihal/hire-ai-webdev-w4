from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.security import require_roles
from app.db.session import get_db
from app.models.application import Application
from app.schemas.auth import UserResponse
from app.schemas.application import (
    ApplicationCreate,
    ApplicationResponse,
    ApplicationUpdate,
    ApplicationStatusUpdate,
    ApplicationBulkUpdate,
    ApplicationDetailResponse,
    PipelineResponse,
    TimelineEvent,
    TimelineResponse,
)

router = APIRouter(prefix="/applications", tags=["Applications"])


def _get_or_404(application: Application | None) -> Application:
    if application is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")
    return application


# ══════════════════════════════════════════════════════════════════════════════
# Fixed-path routes (must be before /{application_id} to avoid path conflicts)
# ══════════════════════════════════════════════════════════════════════════════

@router.get("/pipeline", response_model=PipelineResponse)
async def get_pipeline(
    current_user: UserResponse = Depends(require_roles("admin", "recruiter", "viewer")),
    db: AsyncSession = Depends(get_db),
) -> PipelineResponse:
    """
    Retrieve recruitment pipeline counts by application status.

    Designed for Kanban boards and analytics dashboards. Returns the count of
    applications in each stage: applied, screening, interviewing, shortlisted,
    selected, and rejected.
    """
    result = await db.execute(
        select(Application.status, func.count().label("cnt"))
        .group_by(Application.status)
    )
    rows = result.all()
    counts: dict[str, int] = {row.status: row.cnt for row in rows}

    return PipelineResponse(
        applied=counts.get("applied", 0),
        screening=counts.get("screening", 0),
        interviewing=counts.get("interviewing", 0),
        shortlisted=counts.get("shortlisted", 0),
        selected=counts.get("selected", 0),
        rejected=counts.get("rejected", 0),
    )


@router.get("/timeline", response_model=TimelineResponse)
async def get_timeline(
    current_user: UserResponse = Depends(require_roles("admin", "recruiter", "viewer")),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> TimelineResponse:
    """
    Retrieve a paginated recruitment activity timeline.

    Returns recent application events ordered by most recently updated first.
    Each event includes the application status, IDs, and timestamp.
    """
    count_total = await db.scalar(select(func.count()).select_from(Application))
    total = count_total or 0

    stmt = (
        select(Application)
        .order_by(Application.updated_at.desc(), Application.application_id.desc())
        .limit(page_size)
        .offset((page - 1) * page_size)
    )
    result = await db.execute(stmt)
    applications = result.scalars().all()

    events = [
        TimelineEvent(
            event_type="status_change",
            application_id=app.application_id,
            candidate_id=app.candidate_id,
            job_id=app.job_id,
            status=app.status,
            timestamp=app.updated_at,
        )
        for app in applications
    ]

    return TimelineResponse(
        events=events,
        total=total,
        page=page,
        page_size=page_size,
    )


# ══════════════════════════════════════════════════════════════════════════════
# Collection routes
# ══════════════════════════════════════════════════════════════════════════════

@router.get("", response_model=list[ApplicationResponse])
async def list_applications(
    response: Response,
    current_user: UserResponse = Depends(require_roles("admin", "recruiter", "viewer")),
    job_id: int | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> list[Application]:
    """
    Retrieve a paginated list of job applications.

    Supports filtering by job ID, application status, and custom pagination.
    Pagination headers `X-Total-Count`, `X-Page`, and `X-Page-Size` are returned in the response.
    """
    filters = []
    if job_id is not None:
        filters.append(Application.job_id == job_id)
    if status_filter is not None:
        filters.append(Application.status == status_filter)

    count_stmt = select(func.count()).select_from(Application)
    if filters:
        count_stmt = count_stmt.where(*filters)
    total = await db.scalar(count_stmt)

    stmt = select(Application)
    if filters:
        stmt = stmt.where(*filters)
    stmt = stmt.order_by(Application.application_id.desc())
    stmt = stmt.limit(page_size).offset((page - 1) * page_size)

    response.headers["X-Total-Count"] = str(total or 0)
    response.headers["X-Page"] = str(page)
    response.headers["X-Page-Size"] = str(page_size)
    result = await db.execute(stmt)
    return list(result.scalars().all())


@router.post("", response_model=ApplicationResponse, status_code=status.HTTP_201_CREATED)
async def create_application(
    payload: ApplicationCreate,
    current_user: UserResponse = Depends(require_roles("admin", "recruiter")),
    db: AsyncSession = Depends(get_db),
) -> Application:
    """
    Create a new job application.

    Requires 'admin' or 'recruiter' roles. Connects a candidate to a job with a status and date.
    """
    application = Application(
        **payload.model_dump(),
        created_by=current_user.email,
        updated_by=current_user.email,
    )
    db.add(application)
    await db.commit()
    await db.refresh(application)
    return application

@router.patch("/bulk", response_model=dict)
async def bulk_update_applications(
    payload: ApplicationBulkUpdate,
    current_user: UserResponse = Depends(require_roles("admin", "recruiter")),
    db: AsyncSession = Depends(get_db),
):
    if not payload.application_ids:
        return {"updated_count": 0}

    result = await db.execute(select(Application).where(Application.application_id.in_(payload.application_ids)))
    applications = result.scalars().all()
    
    for app in applications:
        app.status = payload.status
        
    await db.commit()
    return {"updated_count": len(applications)}



# ══════════════════════════════════════════════════════════════════════════════
# Single-resource routes
# ══════════════════════════════════════════════════════════════════════════════

@router.get("/{application_id}", response_model=ApplicationDetailResponse)
async def get_application(
    application_id: int,
    current_user: UserResponse = Depends(require_roles("admin", "recruiter", "viewer")),
    db: AsyncSession = Depends(get_db),
) -> Application:
    """
    Retrieve a single application with nested candidate and job details.

    Returns 404 if the application does not exist.
    """
    stmt = (
        select(Application)
        .where(Application.application_id == application_id)
        .options(
            selectinload(Application.candidate),
            selectinload(Application.job),
        )
    )
    result = await db.execute(stmt)
    return _get_or_404(result.scalar_one_or_none())


@router.patch("/{application_id}", response_model=ApplicationResponse)
async def update_application(
    application_id: int,
    payload: ApplicationUpdate,
    current_user: UserResponse = Depends(require_roles("admin", "recruiter")),
    db: AsyncSession = Depends(get_db),
) -> Application:
    """
    Partially update an existing job application.

    Requires 'admin' or 'recruiter' roles. Updates only fields provided in request body.
    """
    result = await db.execute(select(Application).where(Application.application_id == application_id))
    application = _get_or_404(result.scalar_one_or_none())

    updates = payload.model_dump(exclude_unset=True)
    for key, value in updates.items():
        setattr(application, key, value)
    application.updated_by = current_user.email

    await db.commit()
    await db.refresh(application)
    return application


@router.patch("/{application_id}/status", response_model=ApplicationResponse)
async def update_application_status(
    application_id: int,
    payload: ApplicationStatusUpdate,
    current_user: UserResponse = Depends(require_roles("admin", "recruiter")),
    db: AsyncSession = Depends(get_db),
) -> Application:
    result = await db.execute(select(Application).where(Application.application_id == application_id))
    application = result.scalar_one_or_none()
    if application is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")

    application.status = payload.status
    await db.commit()
    await db.refresh(application)
    return application

