"""initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-05-13 00:00:00

"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0001_initial"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "candidates",
        sa.Column("candidate_id", sa.BigInteger(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("email", sa.Text(), nullable=False),
        sa.Column("skills", sa.Text(), nullable=False),
        sa.Column("experience_years", sa.BigInteger(), nullable=False),
        sa.Column("education", sa.Text(), nullable=False),
        sa.Column("projects", sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint("candidate_id"),
    )
    op.create_index(op.f("ix_candidates_email"), "candidates", ["email"], unique=True)
    op.create_index(op.f("ix_candidates_candidate_id"), "candidates", ["candidate_id"], unique=False)

    op.create_table(
        "jobs",
        sa.Column("job_id", sa.BigInteger(), nullable=False),
        sa.Column("role", sa.Text(), nullable=False),
        sa.Column("required_skills", sa.Text(), nullable=False),
        sa.Column("min_experience", sa.BigInteger(), nullable=False),
        sa.PrimaryKeyConstraint("job_id"),
    )
    op.create_index(op.f("ix_jobs_job_id"), "jobs", ["job_id"], unique=False)
    op.create_index(op.f("ix_jobs_role"), "jobs", ["role"], unique=False)

    op.create_table(
        "applications",
        sa.Column("application_id", sa.BigInteger(), nullable=False),
        sa.Column("candidate_id", sa.BigInteger(), nullable=False),
        sa.Column("job_id", sa.BigInteger(), nullable=False),
        sa.Column("application_date", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(["candidate_id"], ["candidates.candidate_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["job_id"], ["jobs.job_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("application_id"),
    )
    op.create_index(op.f("ix_applications_candidate_id"), "applications", ["candidate_id"], unique=False)
    op.create_index(op.f("ix_applications_application_id"), "applications", ["application_id"], unique=False)
    op.create_index(op.f("ix_applications_job_id"), "applications", ["job_id"], unique=False)

    op.create_table(
        "scores",
        sa.Column("candidate_id", sa.BigInteger(), nullable=False),
        sa.Column("job_id", sa.BigInteger(), nullable=False),
        sa.Column("score", sa.Float(), nullable=False),
        sa.Column("skills_match", sa.Float(), nullable=False),
        sa.Column("experience_score", sa.Float(), nullable=False),
        sa.Column("project_score", sa.Float(), nullable=False),
        sa.Column("label", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(["candidate_id"], ["candidates.candidate_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["job_id"], ["jobs.job_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("candidate_id", "job_id"),
    )
    op.create_index(op.f("ix_scores_candidate_id"), "scores", ["candidate_id"], unique=False)
    op.create_index(op.f("ix_scores_job_id"), "scores", ["job_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_scores_job_id"), table_name="scores")
    op.drop_index(op.f("ix_scores_candidate_id"), table_name="scores")
    op.drop_table("scores")

    op.drop_index(op.f("ix_applications_job_id"), table_name="applications")
    op.drop_index(op.f("ix_applications_candidate_id"), table_name="applications")
    op.drop_table("applications")

    op.drop_index(op.f("ix_jobs_role"), table_name="jobs")
    op.drop_index(op.f("ix_jobs_job_id"), table_name="jobs")
    op.drop_table("jobs")

    op.drop_index(op.f("ix_candidates_email"), table_name="candidates")
    op.drop_table("candidates")

