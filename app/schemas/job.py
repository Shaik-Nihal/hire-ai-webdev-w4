from pydantic import BaseModel, ConfigDict


class JobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    job_id: int
    role: str
    required_skills: str
    min_experience: int
