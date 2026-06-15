from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Candidate(Base):
    __tablename__ = "candidates"

    candidate_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    email: Mapped[str] = mapped_column(Text, unique=True, index=True, nullable=False)
    skills: Mapped[str] = mapped_column(Text, nullable=False)
    experience_years: Mapped[int] = mapped_column(BigInteger, nullable=False)
    education: Mapped[str] = mapped_column(Text, nullable=False)
    projects: Mapped[str] = mapped_column(Text, nullable=False)

    # Lifecycle & soft-delete
    status: Mapped[str] = mapped_column(Text, nullable=False, default="new", index=True)
    is_deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Resume file
    resume_path: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Audit fields
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )
    created_by: Mapped[str | None] = mapped_column(Text, nullable=True)
    updated_by: Mapped[str | None] = mapped_column(Text, nullable=True)

    applications = relationship("Application", back_populates="candidate", cascade="all, delete-orphan")
    scores = relationship("Score", back_populates="candidate", cascade="all, delete-orphan")
    notes = relationship("CandidateNote", back_populates="candidate", cascade="all, delete-orphan")
