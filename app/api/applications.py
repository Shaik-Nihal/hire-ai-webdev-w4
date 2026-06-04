from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

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
)

router = APIRouter(prefix="/applications", tags=["Applications"])


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
    application = Application(**payload.model_dump())
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



@router.patch("/{application_id}", response_model=ApplicationResponse)
async def update_application(
    application_id: int,
    payload: ApplicationUpdate,
    current_user: UserResponse = Depends(require_roles("admin", "recruiter")),
    db: AsyncSession = Depends(get_db),
) -> Application:
    result = await db.execute(select(Application).where(Application.application_id == application_id))
    application = result.scalar_one_or_none()
    if application is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")

    updates = payload.model_dump(exclude_unset=True)
    for key, value in updates.items():
        setattr(application, key, value)

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

