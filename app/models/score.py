from enum import Enum

from sqlalchemy import Enum as SAEnum, Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ScoreLabel(str, Enum):
    GOOD_FIT = "Good Fit"
    AVERAGE_FIT = "Average Fit"
    POOR_FIT = "Poor Fit"


class Score(Base):
    __tablename__ = "scores"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    candidate_id: Mapped[int] = mapped_column(ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False, index=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    score: Mapped[float] = mapped_column(Float, nullable=False)
    skills_match: Mapped[float] = mapped_column(Float, nullable=False)
    experience_score: Mapped[float] = mapped_column(Float, nullable=False)
    project_score: Mapped[float] = mapped_column(Float, nullable=False)
    label: Mapped[ScoreLabel] = mapped_column(SAEnum(ScoreLabel, name="score_label"), nullable=False)

    candidate = relationship("Candidate", back_populates="scores")
    job = relationship("Job", back_populates="scores")
