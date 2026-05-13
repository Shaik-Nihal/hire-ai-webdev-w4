from datetime import date

from pydantic import BaseModel, ConfigDict

from app.models.application import ApplicationStatus


class ApplicationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    candidate_id: int
    job_id: int
    status: ApplicationStatus
    application_date: date
