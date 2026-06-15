import asyncio
import os
import uuid
import pytest
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("TEST_DATABASE_URL") or os.getenv("DATABASE_URL")

@pytest.fixture(scope="module")
def client():
    if not DATABASE_URL:
        pytest.skip("DATABASE_URL must be set.")
        
    from fastapi.testclient import TestClient
    from app.main import app

    with TestClient(app) as test_client:
        yield test_client


# Helper to get auth headers for any role
def get_auth_headers(client, email, role):
    res = client.post(
        "/api/auth/register",
        json={"name": f"Test {role}", "email": email, "password": "password", "role": role}
    )
    assert res.status_code == 201
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


# ==========================================
# 1. Authentication Endpoints
# ==========================================

def test_register_and_login(client):
    email = f"user_{uuid.uuid4().hex[:8]}@example.com"
    # Register
    res = client.post(
        "/api/auth/register",
        json={"name": "New Recruiter", "email": email, "password": "password123", "role": "recruiter"}
    )
    assert res.status_code == 201
    data = res.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["user"]["email"] == email

    # Login failure
    res_fail = client.post(
        "/api/auth/login",
        json={"email": email, "password": "wrongpassword"}
    )
    assert res_fail.status_code == 401

    # Login success (uses default settings credentials)
    res_success = client.post(
        "/api/auth/login",
        json={"email": "recruiter@hireai.com", "password": "admin123"}
    )
    assert res_success.status_code == 200
    assert "access_token" in res_success.json()


def test_token_refresh(client):
    email = f"refresh_{uuid.uuid4().hex[:8]}@example.com"
    # Register to get refresh token
    res = client.post(
        "/api/auth/register",
        json={"name": "Refresher", "email": email, "password": "password", "role": "recruiter"}
    )
    refresh_token = res.json()["refresh_token"]

    # Valid refresh
    res_refresh = client.post(
        "/api/auth/refresh",
        json={"refresh_token": refresh_token}
    )
    assert res_refresh.status_code == 200
    assert "access_token" in res_refresh.json()

    # Invalid refresh
    res_invalid = client.post(
        "/api/auth/refresh",
        json={"refresh_token": "invalid_refresh_token_string"}
    )
    assert res_invalid.status_code == 401


def test_get_me(client):
    email = f"me_{uuid.uuid4().hex[:8]}@example.com"
    headers = get_auth_headers(client, email, "recruiter")
    res = client.get("/api/auth/me", headers=headers)
    assert res.status_code == 200
    assert res.json()["email"] == email

    # Missing auth - FastAPI's HTTPBearer returns 403 Forbidden when credentials missing by default
    res_no_auth = client.get("/api/auth/me")
    assert res_no_auth.status_code == 403


# ==========================================
# 2. Candidates Endpoints
# ==========================================

def test_candidate_permissions(client):
    email = f"viewer_{uuid.uuid4().hex[:8]}@example.com"
    viewer_headers = get_auth_headers(client, email, "viewer")
    
    # Viewer should not be allowed to POST candidates
    res = client.post(
        "/api/candidates",
        headers=viewer_headers,
        json={
            "name": "Test Candidate",
            "email": f"test_c_{uuid.uuid4().hex[:8]}@example.com",
            "skills": "Python, FastAPI",
            "experience_years": 3,
            "education": "B.S. CS",
            "projects": "Project A"
        }
    )
    assert res.status_code == 403


def test_candidate_crud_and_filters(client):
    email = f"recruiter_{uuid.uuid4().hex[:8]}@example.com"
    recruiter_headers = get_auth_headers(client, email, "recruiter")
    
    # Create Candidate
    candidate_email = f"john_doe_{uuid.uuid4().hex[:8]}@example.com"
    res_create = client.post(
        "/api/candidates",
        headers=recruiter_headers,
        json={
            "name": "John Doe",
            "email": candidate_email,
            "skills": "Python, FastAPI, Docker",
            "experience_years": 4,
            "education": "M.S. CS",
            "projects": "Project X"
        }
    )
    assert res_create.status_code == 201
    candidate_id = res_create.json()["candidate_id"]

    # Get Candidates with page and pagination headers
    res_list = client.get("/api/candidates?page=1&page_size=5", headers=recruiter_headers)
    assert res_list.status_code == 200
    assert "X-Total-Count" in res_list.headers
    assert int(res_list.headers["X-Page-Size"]) == 5

    # Get Candidates filtered by skills
    res_filter_skill = client.get("/api/candidates?skills=FastAPI", headers=recruiter_headers)
    assert res_filter_skill.status_code == 200
    assert len(res_filter_skill.json()) >= 1
    assert any(c["candidate_id"] == candidate_id for c in res_filter_skill.json())

    # Get Candidate Full Details
    res_full = client.get(f"/api/candidates/{candidate_id}/full", headers=recruiter_headers)
    assert res_full.status_code == 200
    assert "applications" in res_full.json()
    assert "scores" in res_full.json()

    # Get Non-existent Candidate Full Details
    res_full_missing = client.get("/api/candidates/999999/full", headers=recruiter_headers)
    assert res_full_missing.status_code == 404

    # Patch Candidate
    res_patch = client.patch(
        f"/api/candidates/{candidate_id}",
        headers=recruiter_headers,
        json={"experience_years": 5, "skills": "Python, FastAPI, Kubernetes"}
    )
    assert res_patch.status_code == 200
    assert res_patch.json()["experience_years"] == 5
    assert "Kubernetes" in res_patch.json()["skills"]


# ==========================================
# 3. Jobs Endpoints
# ==========================================

def test_job_crud(client):
    email = f"job_rec_{uuid.uuid4().hex[:8]}@example.com"
    recruiter_headers = get_auth_headers(client, email, "recruiter")
    
    # Create Job
    res_create = client.post(
        "/api/jobs",
        headers=recruiter_headers,
        json={
            "role": "Software Engineer",
            "required_skills": "Python, SQL",
            "min_experience": 2
        }
    )
    assert res_create.status_code == 201
    job_id = res_create.json()["job_id"]

    # List Jobs
    res_list = client.get("/api/jobs?page=1&page_size=10", headers=recruiter_headers)
    assert res_list.status_code == 200
    assert "X-Total-Count" in res_list.headers

    # Patch Job
    res_patch = client.patch(
        f"/api/jobs/{job_id}",
        headers=recruiter_headers,
        json={"min_experience": 3}
    )
    assert res_patch.status_code == 200
    assert res_patch.json()["min_experience"] == 3


# ==========================================
# 4. Applications Endpoints
# ==========================================

def test_application_crud(client):
    email = f"app_rec_{uuid.uuid4().hex[:8]}@example.com"
    recruiter_headers = get_auth_headers(client, email, "recruiter")
    
    # Create Job & Candidate first
    cand_email = f"app_candidate_{uuid.uuid4().hex[:8]}@example.com"
    cand_res = client.post(
        "/api/candidates",
        headers=recruiter_headers,
        json={
            "name": "App Candidate",
            "email": cand_email,
            "skills": "Go, Postgres",
            "experience_years": 2,
            "education": "CS",
            "projects": "None"
        }
    )
    candidate_id = cand_res.json()["candidate_id"]

    job_res = client.post(
        "/api/jobs",
        headers=recruiter_headers,
        json={
            "role": "Go Developer",
            "required_skills": "Go",
            "min_experience": 1
        }
    )
    job_id = job_res.json()["job_id"]

    # Create Application
    res_create = client.post(
        "/api/applications",
        headers=recruiter_headers,
        json={
            "candidate_id": candidate_id,
            "job_id": job_id,
            "status": "applied",
            "application_date": "2026-06-11"
        }
    )
    assert res_create.status_code == 201
    application_id = res_create.json()["application_id"]

    # List Applications with filters
    res_list = client.get(f"/api/applications?job_id={job_id}&status=applied", headers=recruiter_headers)
    assert res_list.status_code == 200
    assert len(res_list.json()) >= 1

    # Patch Application
    res_patch = client.patch(
        f"/api/applications/{application_id}",
        headers=recruiter_headers,
        json={"status": "interviewing"}
    )
    assert res_patch.status_code == 200
    assert res_patch.json()["status"] == "interviewing"
