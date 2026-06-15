from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.enums import CandidateStatus
from app.schemas.application import ApplicationResponse
from app.schemas.score import ScoreResponse


# ── Base response ──────────────────────────────────────────────────────────────

class CandidateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    candidate_id: int
    name: str
    email: EmailStr
    skills: str
    experience_years: int
    education: str
    projects: str
    status: str = "new"
    is_deleted: bool = False
    resume_path: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    created_by: str | None = None
    updated_by: str | None = None


# ── Create / Update ────────────────────────────────────────────────────────────

class CandidateCreate(BaseModel):
    name: str
    email: EmailStr
    skills: str
    experience_years: int
    education: str
    projects: str


class CandidateUpdate(BaseModel):
    """Partial update — all fields optional."""
    name: str | None = None
    email: EmailStr | None = None
    skills: str | None = None
    experience_years: int | None = None
    education: str | None = None
    projects: str | None = None


class CandidateReplaceRequest(BaseModel):
    """Full replacement — all fields required (PUT)."""
    name: str
    email: EmailStr
    skills: str
    experience_years: int
    education: str
    projects: str


# ── Full profile ───────────────────────────────────────────────────────────────

class CandidateFullResponse(CandidateResponse):
    applications: list[ApplicationResponse] = Field(default_factory=list)
    scores: list[ScoreResponse] = Field(default_factory=list)


# ── Status update ──────────────────────────────────────────────────────────────

class CandidateStatusUpdate(BaseModel):
    status: CandidateStatus = Field(..., description="New lifecycle status for the candidate")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {"status": "shortlisted"}
        }
    )


# ── Bulk operations ────────────────────────────────────────────────────────────

class BulkStatusUpdate(BaseModel):
    candidate_ids: list[int] = Field(..., min_length=1, description="List of candidate IDs to update")
    status: CandidateStatus = Field(..., description="New status to apply to all candidates")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {"candidate_ids": [1, 2, 3], "status": "shortlisted"}
        }
    )


class BulkStatusResponse(BaseModel):
    updated_count: int


class BulkAssignJob(BaseModel):
    candidate_ids: list[int] = Field(..., min_length=1, description="Candidate IDs to assign")
    job_id: int = Field(..., description="Target job ID")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {"candidate_ids": [1, 2, 3], "job_id": 5}
        }
    )


class BulkAssignJobResponse(BaseModel):
    created_applications: int


# ── Notes ──────────────────────────────────────────────────────────────────────

class CandidateNoteCreate(BaseModel):
    note: str = Field(..., min_length=1, description="Recruiter note text")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {"note": "Strong Python background, good cultural fit."}
        }
    )


class CandidateNoteResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    note_id: int
    candidate_id: int
    author: str
    note: str
    created_at: datetime


# ── Resume upload ──────────────────────────────────────────────────────────────

class ResumeUploadResponse(BaseModel):
    file_name: str
    url: str


# ── Applications for a candidate ──────────────────────────────────────────────

class CandidateApplicationsResponse(BaseModel):
    candidate: CandidateResponse
    applications: list[ApplicationResponse]


# ── Activity timeline ──────────────────────────────────────────────────────────

class ActivityEvent(BaseModel):
    event_type: str  # "application_created" | "status_change" | "note_added"
    entity_id: int
    description: str
    timestamp: datetime


class ActivityResponse(BaseModel):
    activities: list[ActivityEvent]


# ── Similar candidates ─────────────────────────────────────────────────────────

class SimilarCandidatesResponse(BaseModel):
    similar_candidates: list[CandidateResponse]
