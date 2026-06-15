from datetime import datetime

from pydantic import BaseModel, ConfigDict


# ── Base response ──────────────────────────────────────────────────────────────

class ApplicationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    application_id: int
    candidate_id: int
    job_id: int
    status: str
    application_date: str
    created_at: datetime | None = None
    updated_at: datetime | None = None
    created_by: str | None = None
    updated_by: str | None = None


# ── Nested detail response (includes candidate + job) ─────────────────────────

class _CandidateBasic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    candidate_id: int
    name: str
    email: str
    skills: str
    experience_years: int


class _JobBasic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    job_id: int
    role: str
    required_skills: str
    min_experience: int


class ApplicationDetailResponse(ApplicationResponse):
    candidate: _CandidateBasic | None = None
    job: _JobBasic | None = None


# ── Create / Update ────────────────────────────────────────────────────────────

class ApplicationCreate(BaseModel):
    candidate_id: int
    job_id: int
    status: str
    application_date: str

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "candidate_id": 1,
                "job_id": 2,
                "status": "applied",
                "application_date": "2026-06-15",
            }
        }
    )


class ApplicationUpdate(BaseModel):
    candidate_id: int | None = None
    job_id: int | None = None
    status: str | None = None
    application_date: str | None = None


class ApplicationStatusUpdate(BaseModel):
    status: str


class ApplicationBulkUpdate(BaseModel):
    application_ids: list[int]
    status: str


# ── Timeline ───────────────────────────────────────────────────────────────────

class TimelineEvent(BaseModel):
    event_type: str
    application_id: int
    candidate_id: int
    job_id: int
    status: str
    timestamp: datetime


class TimelineResponse(BaseModel):
    events: list[TimelineEvent]
    total: int
    page: int
    page_size: int


# ── Pipeline (Kanban) ──────────────────────────────────────────────────────────

class PipelineResponse(BaseModel):
    applied: int = 0
    screening: int = 0
    interviewing: int = 0
    shortlisted: int = 0
    selected: int = 0
    rejected: int = 0
