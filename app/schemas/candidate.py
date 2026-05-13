from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr


class CandidateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: EmailStr
    skills: list[str]
    experience_years: int
    education: str
    projects: list[str]
    created_at: datetime
