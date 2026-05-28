from pydantic import BaseModel, ConfigDict


class ScoreResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    candidate_id: int
    job_id: int
    score: float
    skills_match: float
    experience_score: float
    project_score: float
    label: str
