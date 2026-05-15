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
