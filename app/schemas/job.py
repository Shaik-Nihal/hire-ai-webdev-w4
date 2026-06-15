from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.enums import JobStatus


# ── Base response ──────────────────────────────────────────────────────────────

class JobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    job_id: int
    role: str
    required_skills: str
    min_experience: int
    description: str | None = None
    status: str = "draft"
    is_archived: bool = False
    created_at: datetime | None = None
    updated_at: datetime | None = None
    created_by: str | None = None
    updated_by: str | None = None


# ── Create / Update ────────────────────────────────────────────────────────────

class JobCreate(BaseModel):
    role: str
    required_skills: str
    min_experience: int
    description: str | None = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "role": "Backend Engineer",
                "required_skills": "Python, FastAPI, PostgreSQL",
                "min_experience": 3,
                "description": "Build scalable APIs for the HireAI platform.",
            }
        }
    )


class JobUpdate(BaseModel):
    """Partial update — all fields optional."""
    role: str | None = None
    required_skills: str | None = None
    min_experience: int | None = None
    description: str | None = None


class JobReplaceRequest(BaseModel):
    """Full replacement — all fields required (PUT)."""
    role: str
    required_skills: str
    min_experience: int
    description: str | None = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "role": "Senior Backend Engineer",
                "required_skills": "Python, FastAPI, PostgreSQL, Redis",
                "min_experience": 5,
                "description": "Lead the API team.",
            }
        }
    )


# ── Applicants for a job ───────────────────────────────────────────────────────

class JobApplicantsResponse(BaseModel):
    job: JobResponse
    applicants: list[dict]
    total: int
    page: int
    page_size: int
