"""add enums, audit fields, soft delete, resume path, candidate notes

Revision ID: 0002_enums_audit_soft_delete
Revises: 0001_initial
Create Date: 2026-06-15 00:00:00

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0002_enums_audit_soft_delete"
down_revision: str | None = "0001_initial"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # ── candidates: new columns ────────────────────────────────────────────────
    op.add_column("candidates", sa.Column("status", sa.Text(), nullable=False, server_default="new"))
    op.add_column("candidates", sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("candidates", sa.Column("resume_path", sa.Text(), nullable=True))
    op.add_column(
        "candidates",
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.add_column(
        "candidates",
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.add_column("candidates", sa.Column("created_by", sa.Text(), nullable=True))
    op.add_column("candidates", sa.Column("updated_by", sa.Text(), nullable=True))
    op.create_index("ix_candidates_status", "candidates", ["status"], unique=False)

    # ── jobs: new columns ──────────────────────────────────────────────────────
    op.add_column("jobs", sa.Column("description", sa.Text(), nullable=True))
    op.add_column("jobs", sa.Column("status", sa.Text(), nullable=False, server_default="draft"))
    op.add_column("jobs", sa.Column("is_archived", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column(
        "jobs",
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.add_column(
        "jobs",
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.add_column("jobs", sa.Column("created_by", sa.Text(), nullable=True))
    op.add_column("jobs", sa.Column("updated_by", sa.Text(), nullable=True))
    op.create_index("ix_jobs_status", "jobs", ["status"], unique=False)

    # ── applications: new columns ──────────────────────────────────────────────
    op.add_column(
        "applications",
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.add_column(
        "applications",
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.add_column("applications", sa.Column("created_by", sa.Text(), nullable=True))
    op.add_column("applications", sa.Column("updated_by", sa.Text(), nullable=True))
    op.create_index("ix_applications_status", "applications", ["status"], unique=False)

    # ── candidate_notes: new table ─────────────────────────────────────────────
    op.create_table(
        "candidate_notes",
        sa.Column("note_id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("candidate_id", sa.BigInteger(), nullable=False),
        sa.Column("author", sa.Text(), nullable=False),
        sa.Column("note", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(["candidate_id"], ["candidates.candidate_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("note_id"),
    )
    op.create_index("ix_candidate_notes_note_id", "candidate_notes", ["note_id"], unique=False)
    op.create_index("ix_candidate_notes_candidate_id", "candidate_notes", ["candidate_id"], unique=False)


def downgrade() -> None:
    # Drop candidate_notes
    op.drop_index("ix_candidate_notes_candidate_id", table_name="candidate_notes")
    op.drop_index("ix_candidate_notes_note_id", table_name="candidate_notes")
    op.drop_table("candidate_notes")

    # Revert applications columns
    op.drop_index("ix_applications_status", table_name="applications")
    op.drop_column("applications", "updated_by")
    op.drop_column("applications", "created_by")
    op.drop_column("applications", "updated_at")
    op.drop_column("applications", "created_at")

    # Revert jobs columns
    op.drop_index("ix_jobs_status", table_name="jobs")
    op.drop_column("jobs", "updated_by")
    op.drop_column("jobs", "created_by")
    op.drop_column("jobs", "updated_at")
    op.drop_column("jobs", "created_at")
    op.drop_column("jobs", "is_archived")
    op.drop_column("jobs", "status")
    op.drop_column("jobs", "description")

    # Revert candidates columns
    op.drop_index("ix_candidates_status", table_name="candidates")
    op.drop_column("candidates", "updated_by")
    op.drop_column("candidates", "created_by")
    op.drop_column("candidates", "updated_at")
    op.drop_column("candidates", "created_at")
    op.drop_column("candidates", "resume_path")
    op.drop_column("candidates", "is_deleted")
    op.drop_column("candidates", "status")
