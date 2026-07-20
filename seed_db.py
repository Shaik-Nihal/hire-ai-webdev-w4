import asyncio
import sys
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import AsyncSessionLocal, engine
from app.models.candidate import Candidate
from app.models.job import Job
from app.models.application import Application
from app.models.score import Score
from sqlalchemy import select

async def seed_data():
    async with AsyncSessionLocal() as session:
        # Check if candidates exist
        result = await session.execute(select(Candidate))
        candidates = result.scalars().all()
        if candidates:
            print("Database already contains candidates. Skipping seed.")
            return

        # Create sample Candidates
        c1 = Candidate(
            candidate_id=1,
            name="Alice Smith",
            email="alice.smith@example.com",
            skills="Python, FastAPI, PostgreSQL, Docker",
            experience_years=5,
            education="B.S. Computer Science",
            projects="Built high-throughput recruitment API and analytics engine",
            status="new",
            is_deleted=False
        )
        c2 = Candidate(
            candidate_id=2,
            name="Bob Johnson",
            email="bob.johnson@example.com",
            skills="React, TypeScript, Node.js, Tailwind",
            experience_years=3,
            education="B.S. Software Engineering",
            projects="Developed responsive Kanban board web app",
            status="new",
            is_deleted=False
        )
        session.add_all([c1, c2])

        # Create sample Jobs
        j1 = Job(
            job_id=1,
            role="Backend Engineer",
            required_skills="Python, FastAPI, PostgreSQL",
            min_experience=3,
            description="Looking for an experienced Backend Engineer to build robust microservices.",
            status="active",
            is_archived=False
        )
        j2 = Job(
            job_id=2,
            role="Frontend Engineer",
            required_skills="React, TypeScript, CSS",
            min_experience=2,
            description="Looking for a Frontend Engineer with UX design skills.",
            status="active",
            is_archived=False
        )
        session.add_all([j1, j2])

        # Create sample Applications
        a1 = Application(
            application_id=1,
            candidate_id=1,
            job_id=1,
            application_date="2026-07-01",
            status="applied"
        )
        session.add(a1)

        # Create sample Score
        s1 = Score(
            candidate_id=1,
            job_id=1,
            score=92.5,
            skills_match=95.0,
            experience_score=90.0,
            project_score=92.0,
            label="Highly Qualified"
        )
        session.add(s1)

        await session.commit()
        print("Database successfully seeded with initial sample data.")

if __name__ == "__main__":
    asyncio.run(seed_data())
