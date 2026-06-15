"""
Shared application enumerations used across models, schemas, and API endpoints.
"""
from enum import Enum


class CandidateStatus(str, Enum):
    """Lifecycle status of a candidate in the hiring pipeline."""

    new = "new"
    screening = "screening"
    interviewing = "interviewing"
    shortlisted = "shortlisted"
    selected = "selected"
    rejected = "rejected"


class ApplicationStatus(str, Enum):
    """Status of a job application."""

    applied = "applied"
    screening = "screening"
    interviewing = "interviewing"
    shortlisted = "shortlisted"
    selected = "selected"
    rejected = "rejected"


class JobStatus(str, Enum):
    """Publication status of a job listing."""

    draft = "draft"
    published = "published"
    archived = "archived"
