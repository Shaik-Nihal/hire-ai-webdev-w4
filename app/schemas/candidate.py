from pydantic import BaseModel, ConfigDict, EmailStr


class CandidateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    candidate_id: int
    name: str
    email: EmailStr
    skills: str
    experience_years: int
    education: str
    projects: str


class CandidateCreate(BaseModel):
    name: str
    email: EmailStr
    skills: str
    experience_years: int
    education: str
    projects: str


class CandidateUpdate(BaseModel):
    name: str | None = None
    email: EmailStr | None = None
    skills: str | None = None
    experience_years: int | None = None
    education: str | None = None
    projects: str | None = None
