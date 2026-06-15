from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Job(Base):
    __tablename__ = "jobs"

    job_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True)
    role: Mapped[str] = mapped_column(Text, nullable=False)
    required_skills: Mapped[str] = mapped_column(Text, nullable=False)
    min_experience: Mapped[int] = mapped_column(BigInteger, nullable=False)

    # Description (for clone support)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Lifecycle & soft-delete
    status: Mapped[str] = mapped_column(Text, nullable=False, default="draft", index=True)
    is_archived: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Audit fields
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )
    created_by: Mapped[str | None] = mapped_column(Text, nullable=True)
    updated_by: Mapped[str | None] = mapped_column(Text, nullable=True)

    applications = relationship("Application", back_populates="job", cascade="all, delete-orphan")
    scores = relationship("Score", back_populates="job", cascade="all, delete-orphan")
