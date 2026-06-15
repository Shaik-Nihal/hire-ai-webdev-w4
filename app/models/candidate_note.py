from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class CandidateNote(Base):
    """Recruiter notes attached to a specific candidate."""

    __tablename__ = "candidate_notes"

    note_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, index=True)
    candidate_id: Mapped[int] = mapped_column(
        ForeignKey("candidates.candidate_id", ondelete="CASCADE"), nullable=False, index=True
    )
    author: Mapped[str] = mapped_column(Text, nullable=False)  # email from JWT
    note: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    candidate = relationship("Candidate", back_populates="notes")
