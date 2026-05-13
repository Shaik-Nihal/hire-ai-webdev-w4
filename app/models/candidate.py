from datetime import datetime

from sqlalchemy import DateTime, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Candidate(Base):
    __tablename__ = "candidates"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    skills: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    experience_years: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    education: Mapped[str] = mapped_column(String(255), nullable=False)
    projects: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    applications = relationship("Application", back_populates="candidate", cascade="all, delete-orphan")
    scores = relationship("Score", back_populates="candidate", cascade="all, delete-orphan")
