import asyncio
import os

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

DATABASE_URL = os.getenv("TEST_DATABASE_URL") or os.getenv("DATABASE_URL")


def _db_available(url: str) -> bool:
    engine = create_async_engine(url, pool_pre_ping=True)

    async def _probe() -> bool:
        try:
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            return True
        except Exception:
            return False
        finally:
            await engine.dispose()

    return asyncio.run(_probe())


@pytest.fixture(scope="module")
def client():
    if not DATABASE_URL:
        pytest.skip("DATABASE_URL or TEST_DATABASE_URL must be set for tests.")

    if not _db_available(DATABASE_URL):
        pytest.skip("PostgreSQL is not available for tests.")

    os.environ["DATABASE_URL"] = DATABASE_URL

    from fastapi.testclient import TestClient
    from app.main import app

    with TestClient(app) as test_client:
        yield test_client


def test_login_returns_token(client):
    response = client.post(
        "/api/auth/login",
        json={"email": "recruiter@hireai.com", "password": "admin123"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["token_type"] == "bearer"
    assert payload["access_token"]
    assert payload["user"]["email"] == "recruiter@hireai.com"


def _auth_headers(client):
    response = client.post(
        "/api/auth/login",
        json={"email": "recruiter@hireai.com", "password": "admin123"},
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_list_candidates_returns_seeded_data(client):
    response = client.get("/api/candidates", headers=_auth_headers(client))

    assert response.status_code == 200
    payload = response.json()
    assert len(payload) >= 1
    assert "skills" in payload[0]


def test_list_jobs_returns_seeded_data(client):
    response = client.get("/api/jobs", headers=_auth_headers(client))

    assert response.status_code == 200
    payload = response.json()
    assert len(payload) >= 1
    assert "required_skills" in payload[0]
