from pydantic import BaseModel, ConfigDict


class ApplicationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    application_id: int
    candidate_id: int
    job_id: int
    status: str
    application_date: str


class ApplicationCreate(BaseModel):
    candidate_id: int
    job_id: int
    status: str
    application_date: str


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
