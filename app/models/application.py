from datetime import date
from enum import Enum

from sqlalchemy import Date, Enum as SAEnum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ApplicationStatus(str, Enum):
    APPLIED = "Applied"
    SHORTLISTED = "Shortlisted"
    INTERVIEWED = "Interviewed"
    HIRED = "Hired"
    REJECTED = "Rejected"


class Application(Base):
    __tablename__ = "applications"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    candidate_id: Mapped[int] = mapped_column(ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False, index=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    status: Mapped[ApplicationStatus] = mapped_column(
        SAEnum(ApplicationStatus, name="application_status"),
        nullable=False,
        default=ApplicationStatus.APPLIED,
    )
    application_date: Mapped[date] = mapped_column(Date, nullable=False)

    candidate = relationship("Candidate", back_populates="applications")
    job = relationship("Job", back_populates="applications")
