from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.models.candidate import Candidate
from app.models.job import Job
from app.models.user import User


async def seed_initial_data(db: AsyncSession) -> None:
    users_count = await db.scalar(select(func.count()).select_from(User))
    if users_count == 0:
        admin = User(
            name="Admin Recruiter",
            email="recruiter@hireai.com",
            hashed_password=hash_password("admin123"),
            role="admin",
        )
        db.add(admin)

    candidates_count = await db.scalar(select(func.count()).select_from(Candidate))
    if candidates_count == 0:
        db.add_all(
            [
                Candidate(
                    name="Anika Sharma",
                    email="anika.sharma@example.com",
                    skills=["Python", "FastAPI", "PostgreSQL"],
                    experience_years=3,
                    education="B.Tech Computer Science",
                    projects=["Resume Parser", "Hiring Dashboard"],
                ),
                Candidate(
                    name="Rahul Verma",
                    email="rahul.verma@example.com",
                    skills=["React", "TypeScript", "Node.js"],
                    experience_years=4,
                    education="B.E Information Technology",
                    projects=["ATS Frontend", "Interview Scheduler"],
                ),
                Candidate(
                    name="Sara Khan",
                    email="sara.khan@example.com",
                    skills=["Data Analysis", "SQL", "Power BI"],
                    experience_years=2,
                    education="MSc Data Science",
                    projects=["Candidate Insights", "KPI Visualizer"],
                ),
            ]
        )

    jobs_count = await db.scalar(select(func.count()).select_from(Job))
    if jobs_count == 0:
        db.add_all(
            [
                Job(
                    title="Backend Engineer",
                    department="Engineering",
                    required_skills=["Python", "FastAPI", "SQLAlchemy"],
                    min_experience=2,
                    description="Build and maintain scalable backend services.",
                ),
                Job(
                    title="Frontend Engineer",
                    department="Engineering",
                    required_skills=["React", "Tailwind", "Zustand"],
                    min_experience=2,
                    description="Develop responsive and accessible recruiter-facing UI.",
                ),
            ]
        )

    await db.commit()
