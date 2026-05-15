from sqlalchemy import Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Score(Base):
    __tablename__ = "scores"

    candidate_id: Mapped[int] = mapped_column(ForeignKey("candidates.candidate_id", ondelete="CASCADE"), primary_key=True, index=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("jobs.job_id", ondelete="CASCADE"), primary_key=True, index=True)
    score: Mapped[float] = mapped_column(Float, nullable=False)
    skills_match: Mapped[float] = mapped_column(Float, nullable=False)
    experience_score: Mapped[float] = mapped_column(Float, nullable=False)
    project_score: Mapped[float] = mapped_column(Float, nullable=False)
    label: Mapped[str] = mapped_column(nullable=False)

    candidate = relationship("Candidate", back_populates="scores")
    job = relationship("Job", back_populates="scores")
