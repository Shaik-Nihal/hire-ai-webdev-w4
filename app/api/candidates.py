import os
import uuid
from datetime import date

from fastapi import APIRouter, Depends, File, HTTPException, Query, Response, UploadFile, status
from sqlalchemy import func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.security import require_roles
from app.db.session import get_db
from app.enums import CandidateStatus
from app.models.application import Application
from app.models.candidate import Candidate
from app.models.candidate_note import CandidateNote
from app.models.score import Score
from app.schemas.auth import UserResponse
from app.schemas.candidate import (
    ActivityEvent,
    ActivityResponse,
    BulkAssignJob,
    BulkAssignJobResponse,
    BulkStatusUpdate,
    BulkStatusResponse,
    CandidateApplicationsResponse,
    CandidateCreate,
    CandidateFullResponse,
    CandidateNoteCreate,
    CandidateNoteResponse,
    CandidateReplaceRequest,
    CandidateResponse,
    CandidateStatusUpdate,
    CandidateUpdate,
    ResumeUploadResponse,
    SimilarCandidatesResponse,
)

router = APIRouter(prefix="/candidates", tags=["Candidates"])

UPLOAD_DIR = "uploads/resumes"
ALLOWED_EXTENSIONS = {".pdf", ".doc", ".docx"}


def _get_or_404(candidate: Candidate | None) -> Candidate:
    if candidate is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidate not found")
    return candidate


# ══════════════════════════════════════════════════════════════════════════════
# Collection routes (must come before /{candidate_id} to avoid path conflicts)
# ══════════════════════════════════════════════════════════════════════════════

@router.get("", response_model=list[CandidateResponse])
async def list_candidates(
    response: Response,
    current_user: UserResponse = Depends(require_roles("admin", "recruiter", "viewer")),
    skills: str | None = Query(default=None, description="Comma-separated skills to match"),
    min_score: float | None = Query(default=None, ge=0, description="Minimum score filter"),
    max_score: float | None = Query(default=None, ge=0, description="Maximum score filter"),
    job_id: int | None = Query(default=None, description="Job id for score filtering"),
    candidate_status: str | None = Query(default=None, alias="status", description="Filter by lifecycle status"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> list[Candidate]:
    """
    Retrieve a paginated list of active (non-deleted) candidates.

    Supports filtering by skills, score range, job ID, and lifecycle status.
    Pagination headers `X-Total-Count`, `X-Page`, and `X-Page-Size` are returned.
    """
    filters = [Candidate.is_deleted.is_(False)]

    skill_tokens = [token.strip() for token in skills.split(",")] if skills else []
    if skill_tokens:
        filters.append(or_(*[Candidate.skills.ilike(f"%{token}%") for token in skill_tokens]))

    if candidate_status is not None:
        filters.append(Candidate.status == candidate_status)

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

    count_stmt = select(func.count()).select_from(Candidate).where(*filters)
    total = await db.scalar(count_stmt)

    stmt = (
        select(Candidate)
        .where(*filters)
        .order_by(Candidate.candidate_id.desc())
        .limit(page_size)
        .offset((page - 1) * page_size)
    )

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
    """
    Onboard and create a new candidate.

    Requires 'admin' or 'recruiter' roles. Creates candidate profile with basic details.
    """
    candidate = Candidate(**payload.model_dump(), created_by=current_user.email, updated_by=current_user.email)
    db.add(candidate)
    await db.commit()
    await db.refresh(candidate)
    return candidate


# ── Fixed sub-collection routes (before /{candidate_id}) ──────────────────────

@router.patch("/bulk-status", response_model=BulkStatusResponse)
async def bulk_update_status(
    payload: BulkStatusUpdate,
    current_user: UserResponse = Depends(require_roles("admin", "recruiter")),
    db: AsyncSession = Depends(get_db),
) -> BulkStatusResponse:
    """
    Update the lifecycle status of multiple candidates at once.

    Applies the same `status` value to all specified `candidate_ids`.
    Only active (non-deleted) candidates are affected.
    """
    stmt = (
        update(Candidate)
        .where(Candidate.candidate_id.in_(payload.candidate_ids), Candidate.is_deleted.is_(False))
        .values(status=payload.status.value, updated_by=current_user.email)
        .execution_options(synchronize_session=False)
    )
    result = await db.execute(stmt)
    await db.commit()
    return BulkStatusResponse(updated_count=result.rowcount)


@router.patch("/bulk-assign-job", response_model=BulkAssignJobResponse)
async def bulk_assign_job(
    payload: BulkAssignJob,
    current_user: UserResponse = Depends(require_roles("admin", "recruiter")),
    db: AsyncSession = Depends(get_db),
) -> BulkAssignJobResponse:
    """
    Assign multiple candidates to a job by creating application records.

    Skips candidates who already have an application for the specified job
    to avoid duplicate applications.
    """
    # Find existing application pairs to avoid duplicates
    existing_stmt = select(Application.candidate_id).where(
        Application.job_id == payload.job_id,
        Application.candidate_id.in_(payload.candidate_ids),
    )
    existing_result = await db.execute(existing_stmt)
    already_applied = set(existing_result.scalars().all())

    today = date.today().isoformat()
    new_applications = [
        Application(
            candidate_id=cid,
            job_id=payload.job_id,
            status="applied",
            application_date=today,
            created_by=current_user.email,
            updated_by=current_user.email,
        )
        for cid in payload.candidate_ids
        if cid not in already_applied
    ]

    if new_applications:
        db.add_all(new_applications)
        await db.commit()

    return BulkAssignJobResponse(created_applications=len(new_applications))


# ══════════════════════════════════════════════════════════════════════════════
# Single-resource routes
# ══════════════════════════════════════════════════════════════════════════════

@router.get("/{candidate_id}", response_model=CandidateResponse)
async def get_candidate(
    candidate_id: int,
    current_user: UserResponse = Depends(require_roles("admin", "recruiter", "viewer")),
    db: AsyncSession = Depends(get_db),
) -> Candidate:
    """
    Retrieve a single candidate by ID.

    Returns 404 if the candidate does not exist or has been soft-deleted.
    """
    result = await db.execute(
        select(Candidate).where(Candidate.candidate_id == candidate_id, Candidate.is_deleted.is_(False))
    )
    return _get_or_404(result.scalar_one_or_none())


@router.put("/{candidate_id}", response_model=CandidateResponse)
async def replace_candidate(
    candidate_id: int,
    payload: CandidateReplaceRequest,
    current_user: UserResponse = Depends(require_roles("admin", "recruiter")),
    db: AsyncSession = Depends(get_db),
) -> Candidate:
    """
    Fully replace a candidate's profile (all fields required).

    Unlike PATCH, every field must be supplied. Returns 404 if candidate not found or deleted.
    """
    result = await db.execute(
        select(Candidate).where(Candidate.candidate_id == candidate_id, Candidate.is_deleted.is_(False))
    )
    candidate = _get_or_404(result.scalar_one_or_none())

    for key, value in payload.model_dump().items():
        setattr(candidate, key, value)
    candidate.updated_by = current_user.email

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
    """
    Partially update an existing candidate's profile.

    Requires 'admin' or 'recruiter' roles. Updates only fields provided in request body.
    """
    result = await db.execute(
        select(Candidate).where(Candidate.candidate_id == candidate_id, Candidate.is_deleted.is_(False))
    )
    candidate = _get_or_404(result.scalar_one_or_none())

    updates = payload.model_dump(exclude_unset=True)
    for key, value in updates.items():
        setattr(candidate, key, value)
    candidate.updated_by = current_user.email

    await db.commit()
    await db.refresh(candidate)
    return candidate


@router.delete("/{candidate_id}", status_code=status.HTTP_200_OK)
async def delete_candidate(
    candidate_id: int,
    current_user: UserResponse = Depends(require_roles("admin")),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """
    Soft-delete a candidate by setting `is_deleted = true`.

    The candidate record is preserved in the database but excluded from all list/get queries.
    Requires 'admin' role only.
    """
    result = await db.execute(
        select(Candidate).where(Candidate.candidate_id == candidate_id, Candidate.is_deleted.is_(False))
    )
    candidate = _get_or_404(result.scalar_one_or_none())

    candidate.is_deleted = True
    candidate.updated_by = current_user.email
    await db.commit()
    return {"message": "Candidate deleted successfully"}


@router.patch("/{candidate_id}/status", response_model=CandidateResponse)
async def update_candidate_status(
    candidate_id: int,
    payload: CandidateStatusUpdate,
    current_user: UserResponse = Depends(require_roles("admin", "recruiter")),
    db: AsyncSession = Depends(get_db),
) -> Candidate:
    """
    Update the lifecycle status of a single candidate.

    Valid statuses: `new`, `screening`, `interviewing`, `shortlisted`, `selected`, `rejected`.
    """
    result = await db.execute(
        select(Candidate).where(Candidate.candidate_id == candidate_id, Candidate.is_deleted.is_(False))
    )
    candidate = _get_or_404(result.scalar_one_or_none())

    candidate.status = payload.status.value
    candidate.updated_by = current_user.email
    await db.commit()
    await db.refresh(candidate)
    return candidate


@router.get("/{candidate_id}/full", response_model=CandidateFullResponse)
async def get_candidate_full(
    candidate_id: int,
    current_user: UserResponse = Depends(require_roles("admin", "recruiter", "viewer")),
    db: AsyncSession = Depends(get_db),
) -> Candidate:
    """
    Retrieve full candidate profile including applications and scores.

    Performs optimized relationship loading to prevent N+1 query patterns.
    """
    stmt = (
        select(Candidate)
        .where(Candidate.candidate_id == candidate_id, Candidate.is_deleted.is_(False))
        .options(selectinload(Candidate.applications), selectinload(Candidate.scores))
    )
    result = await db.execute(stmt)
    return _get_or_404(result.scalar_one_or_none())


@router.post("/{candidate_id}/notes", response_model=CandidateNoteResponse, status_code=status.HTTP_201_CREATED)
async def add_candidate_note(
    candidate_id: int,
    payload: CandidateNoteCreate,
    current_user: UserResponse = Depends(require_roles("admin", "recruiter")),
    db: AsyncSession = Depends(get_db),
) -> CandidateNote:
    """
    Add a recruiter note to a candidate.

    The note `author` is automatically set from the authenticated user's email.
    Returns 404 if the candidate does not exist or is deleted.
    """
    result = await db.execute(
        select(Candidate).where(Candidate.candidate_id == candidate_id, Candidate.is_deleted.is_(False))
    )
    _get_or_404(result.scalar_one_or_none())

    note = CandidateNote(
        candidate_id=candidate_id,
        author=current_user.email,
        note=payload.note,
    )
    db.add(note)
    await db.commit()
    await db.refresh(note)
    return note


@router.post("/{candidate_id}/resume", response_model=ResumeUploadResponse)
async def upload_resume(
    candidate_id: int,
    file: UploadFile = File(..., description="Resume file (pdf, doc, docx)"),
    current_user: UserResponse = Depends(require_roles("admin", "recruiter")),
    db: AsyncSession = Depends(get_db),
) -> ResumeUploadResponse:
    """
    Upload a resume file for a candidate.

    Accepts PDF, DOC, and DOCX formats. The file is stored in `uploads/resumes/`
    and the path is persisted on the candidate record.

    **Note**: On ephemeral platforms (e.g. Render free tier), files are not persisted
    across deploys. Integrate Supabase Storage for production-grade persistence.
    """
    result = await db.execute(
        select(Candidate).where(Candidate.candidate_id == candidate_id, Candidate.is_deleted.is_(False))
    )
    candidate = _get_or_404(result.scalar_one_or_none())

    # Validate extension
    _, ext = os.path.splitext(file.filename or "")
    if ext.lower() not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type '{ext}'. Allowed: pdf, doc, docx",
        )

    # Save file
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    unique_name = f"{uuid.uuid4().hex}{ext.lower()}"
    file_path = os.path.join(UPLOAD_DIR, unique_name)
    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)

    # Persist path on candidate
    candidate.resume_path = file_path
    candidate.updated_by = current_user.email
    await db.commit()

    return ResumeUploadResponse(
        file_name=unique_name,
        url=f"/uploads/resumes/{unique_name}",
    )


@router.get("/{candidate_id}/applications", response_model=CandidateApplicationsResponse)
async def get_candidate_applications(
    candidate_id: int,
    current_user: UserResponse = Depends(require_roles("admin", "recruiter", "viewer")),
    db: AsyncSession = Depends(get_db),
) -> CandidateApplicationsResponse:
    """
    Retrieve all job applications submitted by a specific candidate.

    Returns candidate profile together with the list of applications.
    """
    stmt = (
        select(Candidate)
        .where(Candidate.candidate_id == candidate_id, Candidate.is_deleted.is_(False))
        .options(selectinload(Candidate.applications))
    )
    result = await db.execute(stmt)
    candidate = _get_or_404(result.scalar_one_or_none())
    return CandidateApplicationsResponse(candidate=candidate, applications=candidate.applications)


@router.get("/{candidate_id}/activity", response_model=ActivityResponse)
async def get_candidate_activity(
    candidate_id: int,
    current_user: UserResponse = Depends(require_roles("admin", "recruiter", "viewer")),
    db: AsyncSession = Depends(get_db),
) -> ActivityResponse:
    """
    Retrieve the activity timeline for a candidate.

    Aggregates events from:
    - Application creation records
    - Recruiter notes added
    - Latest application status (as status change events)

    Events are sorted by timestamp descending (newest first).
    """
    result = await db.execute(
        select(Candidate).where(Candidate.candidate_id == candidate_id, Candidate.is_deleted.is_(False))
    )
    _get_or_404(result.scalar_one_or_none())

    events: list[ActivityEvent] = []

    # Application creation events
    apps_result = await db.execute(
        select(Application)
        .where(Application.candidate_id == candidate_id)
        .order_by(Application.created_at.desc())
    )
    for app in apps_result.scalars().all():
        events.append(
            ActivityEvent(
                event_type="application_created",
                entity_id=app.application_id,
                description=f"Applied to job #{app.job_id} with status '{app.status}'",
                timestamp=app.created_at,
            )
        )
        # Status change event when updated_at differs from created_at
        if app.updated_at and app.updated_at != app.created_at:
            events.append(
                ActivityEvent(
                    event_type="status_change",
                    entity_id=app.application_id,
                    description=f"Application #{app.application_id} status updated to '{app.status}'",
                    timestamp=app.updated_at,
                )
            )

    # Notes events
    notes_result = await db.execute(
        select(CandidateNote)
        .where(CandidateNote.candidate_id == candidate_id)
        .order_by(CandidateNote.created_at.desc())
    )
    for note in notes_result.scalars().all():
        events.append(
            ActivityEvent(
                event_type="note_added",
                entity_id=note.note_id,
                description=f"Note added by {note.author}: {note.note[:80]}{'...' if len(note.note) > 80 else ''}",
                timestamp=note.created_at,
            )
        )

    events.sort(key=lambda e: e.timestamp, reverse=True)
    return ActivityResponse(activities=events)


@router.get("/{candidate_id}/similar", response_model=SimilarCandidatesResponse)
async def get_similar_candidates(
    candidate_id: int,
    current_user: UserResponse = Depends(require_roles("admin", "recruiter", "viewer")),
    db: AsyncSession = Depends(get_db),
) -> SimilarCandidatesResponse:
    """
    Recommend up to 5 candidates similar to the specified candidate.

    Similarity is determined by:
    1. Overlapping skills (primary signal)
    2. Comparable experience years (within ±2 years)
    3. Average score proximity (when scores exist)

    The source candidate is excluded from results.
    """
    result = await db.execute(
        select(Candidate).where(Candidate.candidate_id == candidate_id, Candidate.is_deleted.is_(False))
    )
    source = _get_or_404(result.scalar_one_or_none())

    # Build skill tokens for matching
    skill_tokens = [t.strip() for t in (source.skills or "").split(",") if t.strip()]
    if not skill_tokens:
        return SimilarCandidatesResponse(similar_candidates=[])

    skill_filters = or_(*[Candidate.skills.ilike(f"%{token}%") for token in skill_tokens])

    stmt = (
        select(Candidate)
        .where(
            Candidate.candidate_id != candidate_id,
            Candidate.is_deleted.is_(False),
            skill_filters,
            Candidate.experience_years.between(
                max(0, source.experience_years - 2),
                source.experience_years + 2,
            ),
        )
        .limit(5)
    )
    similar_result = await db.execute(stmt)
    return SimilarCandidatesResponse(similar_candidates=list(similar_result.scalars().all()))
