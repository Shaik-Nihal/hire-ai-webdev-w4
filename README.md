# HireAI Copilot Backend

FastAPI backend for the HireAI Copilot recruitment platform.

---

## Table of Contents

1. [Stack](#stack)
2. [Project Structure](#project-structure)
3. [Week 1 and Week 2 Summary](#week-1-and-week-2-summary)
4. [Setup Instructions](#setup-instructions)
5. [Running the Application](#running-the-application)
6. [API Endpoints](#api-endpoints)
7. [Authentication](#authentication)
8. [Verification Checklist](#verification-checklist)
9. [Docker Deployment](#docker-deployment)
10. [Database Migrations](#database-migrations)
11. [Documentation](#documentation)

---

## Stack

- **FastAPI** - Modern web framework for building APIs
- **SQLAlchemy 2.0** - Async ORM for database operations
- **PostgreSQL** - Primary database with asyncpg driver
- **Alembic** - Database migration management
- **Pydantic v2** - Data validation and serialization
- **JWT (python-jose)** - Secure token-based authentication
- **Uvicorn** - ASGI web server

---

## Project Structure

```
backend/
├── app/
│   ├── main.py              # FastAPI application entrypoint
│   ├── api/                 # API routes
│   │   ├── auth.py          # Authentication endpoints
│   │   ├── candidates.py    # Candidate management
│   │   ├── jobs.py          # Job listings
│   │   └── applications.py  # Job applications
│   ├── core/                # Core configurations
│   │   ├── config.py        # Settings from environment
│   │   ├── security.py      # JWT and authentication logic
│   │   ├── exceptions.py    # Custom exception handlers
│   │   └── middleware.py    # CORS and other middleware
│   ├── db/                  # Database setup
│   │   ├── base.py          # SQLAlchemy declarative base
│   │   └── session.py       # Database session management
│   ├── models/              # ORM models
│   │   ├── candidate.py     # Candidate model
│   │   ├── job.py           # Job model
│   │   ├── application.py   # Application model
│   │   └── score.py         # Scoring model
│   ├── schemas/             # Pydantic request/response schemas
│   │   ├── auth.py
│   │   ├── candidate.py
│   │   ├── job.py
│   │   └── application.py
│   └── tests/               # Test files
├── alembic/                 # Database migrations
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
├── .env                     # Environment variables
├── requirements.txt         # Production dependencies
├── requirements-dev.txt     # Development dependencies
├── Dockerfile              # Docker image configuration
├── docker-compose.yml      # Multi-container Docker setup
└── README.md               # This file
```

---

## Week 1 and Week 2 Summary

### Week 1 (Baseline API)

- Auth endpoints: `POST /api/auth/register`, `POST /api/auth/login`, `GET /api/auth/me`
- Read endpoints: `GET /api/candidates`, `GET /api/jobs`, `GET /api/applications`
- Health check: `GET /health`
- Docs: `/docs`, `/redoc`, `/api/openapi.json`

### Week 2 (Auth + CRUD + Filtering)

- `register` now returns a JWT (same format as login)
- Bearer auth required for all candidates, jobs, applications endpoints
- Added `POST` and `PATCH` for candidates, jobs, applications
- Applications filtering: `GET /api/applications?job_id=...&status=...`
- Swagger uses HTTP Bearer token paste in **Authorize**

Middleware is live:
- CORS
- Request ID + process time headers
- Custom exception handler

---

## Setup Instructions

### Prerequisites

- **Python 3.9+** installed
- **PostgreSQL** database (local or remote)
- **pip** package manager
- **Git** (optional, for version control)

### Windows Setup

#### Step 1: Clone/Navigate to the Project

```bash
cd path\to\Skillvance\backend
```

#### Step 2: Create a Virtual Environment

```bash
python -m venv venv
```

**Why**: Virtual environments isolate project dependencies, preventing conflicts with system Python packages.

#### Step 3: Activate the Virtual Environment

```bash
venv\Scripts\activate
```

You should see `(venv)` in your command prompt after activation.

#### Step 4: Upgrade pip

```bash
python -m pip install --upgrade pip
```

**Why**: Ensures you have the latest package manager with bug fixes and improvements.

#### Step 5: Install Dependencies

```bash
pip install -r requirements.txt
```

For development (includes testing tools):

```bash
pip install -r requirements-dev.txt
```

#### Step 6: Configure Environment Variables

Create a `.env` file in the `backend` directory (if not already present). You can copy from the example:

```env
PROJECT_NAME=HireAI Copilot API
API_V1_STR=/api
DATABASE_URL=postgresql+asyncpg://username:password@hostname:5432/database_name?ssl=require
JWT_SECRET_KEY=your-secret-key-here
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
AUTO_CREATE_TABLES=false
CORS_ORIGINS=["http://localhost:3000","http://127.0.0.1:3000"]
```

**Important fields**:
- `DATABASE_URL`: Connection string to PostgreSQL
- `JWT_SECRET_KEY`: Secret key for signing JWT tokens (change in production)
- `CORS_ORIGINS`: Allowed frontend origins

#### Step 7: Apply Database Migrations

```bash
alembic upgrade head
```

**Why**: Applies all pending database schema changes to your PostgreSQL database.

#### Step 8: Start the Development Server

```bash
uvicorn app.main:app --reload
```

The API will be available at: `http://127.0.0.1:8000`

---

### macOS Setup

#### Step 1: Navigate to the Project

```bash
cd path/to/Skillvance/backend
```

#### Step 2: Create a Virtual Environment

```bash
python3 -m venv venv
```

#### Step 3: Activate the Virtual Environment

```bash
source venv/bin/activate
```

You should see `(venv)` in your terminal prompt.

#### Step 4: Upgrade pip

```bash
python -m pip install --upgrade pip
```

#### Step 5: Install Dependencies

```bash
pip install -r requirements.txt
```

For development:

```bash
pip install -r requirements-dev.txt
```

#### Step 6: Configure Environment Variables

Create or edit `.env` in the `backend` directory:

```env
PROJECT_NAME=HireAI Copilot API
API_V1_STR=/api
DATABASE_URL=postgresql+asyncpg://username:password@hostname:5432/database_name?ssl=require
JWT_SECRET_KEY=your-secret-key-here
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
AUTO_CREATE_TABLES=false
CORS_ORIGINS=["http://localhost:3000","http://127.0.0.1:3000"]
```

#### Step 7: Apply Database Migrations

```bash
alembic upgrade head
```

#### Step 8: Start the Development Server

```bash
uvicorn app.main:app --reload
```

The API will be available at: `http://127.0.0.1:8000`

---

### Linux (Ubuntu/Debian) Setup

#### Step 1: Install Python and pip (if not already installed)

```bash
sudo apt-get update
sudo apt-get install python3 python3-pip python3-venv
```

#### Step 2: Navigate to the Project

```bash
cd path/to/Skillvance/backend
```

#### Step 3: Create a Virtual Environment

```bash
python3 -m venv venv
```

#### Step 4: Activate the Virtual Environment

```bash
source venv/bin/activate
```

#### Step 5: Upgrade pip

```bash
python -m pip install --upgrade pip
```

#### Step 6: Install Dependencies

```bash
pip install -r requirements.txt
```

For development:

```bash
pip install -r requirements-dev.txt
```

#### Step 7: Configure Environment Variables

Create or edit `.env` in the `backend` directory:

```env
PROJECT_NAME=HireAI Copilot API
API_V1_STR=/api
DATABASE_URL=postgresql+asyncpg://username:password@hostname:5432/database_name?ssl=require
JWT_SECRET_KEY=your-secret-key-here
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
AUTO_CREATE_TABLES=false
CORS_ORIGINS=["http://localhost:3000","http://127.0.0.1:3000"]
```

#### Step 8: Apply Database Migrations

```bash
alembic upgrade head
```

#### Step 9: Start the Development Server

```bash
uvicorn app.main:app --reload
```

The API will be available at: `http://127.0.0.1:8000`

---

## Running the Application

### Development Mode (with auto-reload)

```bash
uvicorn app.main:app --reload
```

### Production Mode

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Deactivate Virtual Environment

When finished, deactivate the virtual environment:

```bash
deactivate
```

---

## API Endpoints

### Health Check

#### GET `/health`

**Purpose**: Verify that the API is running and responsive.

**Why it's needed**: Used for monitoring, load balancer health checks, and debugging connectivity issues.

**Request**:

```bash
curl http://127.0.0.1:8000/health
```

**Response** (200 OK):

```json
{
  "status": "ok"
}
```

---

### Authentication Endpoints

Base URL: `/api/auth`

---

#### 1. POST `/api/auth/register`

**Purpose**: Register a new recruiter account and return a JWT.

**Why it's needed**: Creates a user and immediately issues a token for protected routes.

**Request Headers**:

```
Content-Type: application/json
```

**Request Body**:

```json
{
  "name": "John Recruiter",
  "email": "john@company.com",
  "password": "securepassword123",
  "role": "recruiter"
}
```

**cURL Example**:

```bash
curl -X POST http://127.0.0.1:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Recruiter",
    "email": "john@company.com",
    "password": "securepassword123",
    "role": "recruiter"
  }'
```

**Response** (201 Created):

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "name": "John Recruiter",
    "email": "john@company.com",
    "role": "recruiter",
    "created_at": "2026-05-20T10:30:00"
  }
}
```

**Status Codes**:
- `201 Created`: User registered successfully
- `400 Bad Request`: Invalid input data
- `422 Unprocessable Entity`: Validation error

---

#### 2. POST `/api/auth/login`

**Purpose**: Authenticate user and receive a JWT token for subsequent requests.

**Why it's needed**: Provides secure access to protected endpoints. The returned token must be used in the Authorization header for all authenticated requests.

**Default Credentials** (for testing):

```
email: recruiter@hireai.com
password: admin123
```

**Request Headers**:

```
Content-Type: application/json
```

**Request Body** (JSON):

```json
{
  "email": "recruiter@hireai.com",
  "password": "admin123"
}
```

**Alternative: Form Data**:

```
Content-Type: application/x-www-form-urlencoded

username=recruiter@hireai.com&password=admin123
```

**cURL Example** (JSON):

```bash
curl -X POST http://127.0.0.1:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "recruiter@hireai.com",
    "password": "admin123"
  }'
```

**cURL Example** (Form Data):

```bash
curl -X POST http://127.0.0.1:8000/api/auth/login \
  -d "email=recruiter@hireai.com&password=admin123"
```

**Response** (200 OK):

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "name": "Recruiter User",
    "email": "recruiter@hireai.com",
    "role": "recruiter",
    "created_at": "2026-01-01T00:00:00"
  }
}
```

**Status Codes**:
- `200 OK`: Login successful
- `401 Unauthorized`: Invalid credentials
- `422 Unprocessable Entity`: Missing or invalid email/password

---

#### 3. GET `/api/auth/me`

**Purpose**: Get the authenticated user's profile information.

**Why it's needed**: Verify the current user's identity and permissions. Useful after login to confirm session validity.

**Request Headers**:

```
Authorization: Bearer <access_token>
```

**cURL Example**:

```bash
curl http://127.0.0.1:8000/api/auth/me \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

**Response** (200 OK):

```json
{
  "id": 1,
  "name": "Recruiter User",
  "email": "recruiter@hireai.com",
  "role": "recruiter",
  "created_at": "2026-01-01T00:00:00"
}
```

**Status Codes**:
- `200 OK`: User authenticated
- `401 Unauthorized`: Invalid or missing token
- `403 Forbidden`: Token expired

---

### Candidates Endpoints

Base URL: `/api/candidates`

---

#### GET `/api/candidates`

**Purpose**: Retrieve a list of all candidates in the system.

**Why it's needed**: Allows recruiters to browse candidates, their skills, experience, and qualifications to find suitable matches for job openings.

**Request Headers**:

```
Authorization: Bearer <access_token>
```

**Query Parameters** (optional):
- `job_id`: Filter by job id
- `status`: Filter by application status

**cURL Example**:

```bash
curl http://127.0.0.1:8000/api/candidates \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

**Response** (200 OK):

```json
[
  {
    "candidate_id": 1,
    "name": "Alice Johnson",
    "email": "alice@email.com",
    "skills": "Python, FastAPI, Docker, PostgreSQL",
    "experience_years": 5,
    "education": "B.S. Computer Science",
    "projects": "Built 3 production microservices, Led team of 4 developers"
  },
  {
    "candidate_id": 2,
    "name": "Bob Smith",
    "email": "bob@email.com",
    "skills": "JavaScript, React, Node.js, MongoDB",
    "experience_years": 3,
    "education": "B.S. Information Technology",
    "projects": "Created 5 full-stack web applications"
  }
]
```

**Status Codes**:
- `200 OK`: Candidates retrieved successfully
- `401 Unauthorized`: Invalid or missing token

**Response Fields Explained**:
- `candidate_id`: Unique identifier for the candidate
- `name`: Full name of the candidate
- `email`: Contact email address
- `skills`: Comma-separated list of technical skills
- `experience_years`: Years of professional experience
- `education`: Educational background
- `projects`: Summary of key projects and accomplishments

---

#### POST `/api/candidates`

**Purpose**: Create a new candidate.

**Request Body**:

```json
{
  "name": "Alice Johnson",
  "email": "alice@email.com",
  "skills": "Python, FastAPI, Docker",
  "experience_years": 5,
  "education": "B.S. Computer Science",
  "projects": "Built 3 production microservices"
}
```

**Response**: Candidate record

---

#### PATCH `/api/candidates/{candidate_id}`

**Purpose**: Update candidate fields.

**Request Body** (partial update):

```json
{
  "skills": "Python, FastAPI, Docker, PostgreSQL",
  "experience_years": 6
}
```

**Response**: Updated candidate record

---

### Jobs Endpoints

Base URL: `/api/jobs`

---

#### GET `/api/jobs`

**Purpose**: Retrieve a list of all active job openings.

**Why it's needed**: Allows recruiters to see available job positions, required skills, and experience levels. Essential for matching candidates to appropriate roles.

**Request Headers**:

```
Authorization: Bearer <access_token>
```

**Query Parameters**: None (currently)

**cURL Example**:

```bash
curl http://127.0.0.1:8000/api/jobs \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

**Response** (200 OK):

```json
[
  {
    "job_id": 1,
    "role": "Senior Backend Engineer",
    "required_skills": "Python, FastAPI, PostgreSQL, Docker, AWS",
    "min_experience": 5
  },
  {
    "job_id": 2,
    "role": "Frontend Developer",
    "required_skills": "JavaScript, React, CSS, HTML, TypeScript",
    "min_experience": 2
  },
  {
    "job_id": 3,
    "role": "Full Stack Engineer",
    "required_skills": "JavaScript, React, Node.js, MongoDB, Docker",
    "min_experience": 3
  }
]
```

**Status Codes**:
- `200 OK`: Jobs retrieved successfully
- `401 Unauthorized`: Invalid or missing token

**Response Fields Explained**:
- `job_id`: Unique identifier for the job posting
- `role`: Job title/position name
- `required_skills`: Comma-separated list of required technical skills
- `min_experience`: Minimum years of experience required

---

#### POST `/api/jobs`

**Purpose**: Create a new job.

**Request Body**:

```json
{
  "role": "Backend Engineer",
  "required_skills": "Python, FastAPI, PostgreSQL",
  "min_experience": 3
}
```

**Response**: Job record

---

#### PATCH `/api/jobs/{job_id}`

**Purpose**: Update job fields.

**Request Body** (partial update):

```json
{
  "required_skills": "Python, FastAPI, PostgreSQL, Docker"
}
```

**Response**: Updated job record

---

### Applications Endpoints

Base URL: `/api/applications`

---

#### GET `/api/applications`

**Purpose**: Retrieve a list of all job applications (candidate-to-job submissions).

**Why it's needed**: Allows recruiters to track which candidates have applied for which positions and monitor application status (pending, accepted, rejected).

**Request Headers**:

```
Authorization: Bearer <access_token>
```

**Query Parameters**: None (currently)

**cURL Example**:

```bash
curl http://127.0.0.1:8000/api/applications \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

**Filtered Example**:

```bash
curl "http://127.0.0.1:8000/api/applications?job_id=1&status=pending" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```
```

**Response** (200 OK):

```json
[
  {
    "application_id": 1,
    "candidate_id": 1,
    "job_id": 1,
    "status": "pending",
    "application_date": "2026-05-18T14:30:00"
  },
  {
    "application_id": 2,
    "candidate_id": 2,
    "job_id": 2,
    "status": "accepted",
    "application_date": "2026-05-17T09:15:00"
  },
  {
    "application_id": 3,
    "candidate_id": 1,
    "job_id": 2,
    "status": "rejected",
    "application_date": "2026-05-16T11:45:00"
  }
]
```

**Status Codes**:
- `200 OK`: Applications retrieved successfully
- `401 Unauthorized`: Invalid or missing token

**Response Fields Explained**:
- `application_id`: Unique identifier for the application
- `candidate_id`: ID of the candidate who applied
- `job_id`: ID of the job position
- `status`: Current status of the application (pending, accepted, rejected)
- `application_date`: Timestamp when the application was submitted

---

#### POST `/api/applications`

**Purpose**: Create a new application.

**Request Body**:

```json
{
  "candidate_id": 1,
  "job_id": 1,
  "status": "pending",
  "application_date": "2026-05-18T14:30:00"
}
```

**Response**: Application record

---

#### PATCH `/api/applications/{application_id}`

**Purpose**: Update application fields.

**Request Body** (partial update):

```json
{
  "status": "accepted"
}
```

**Response**: Updated application record

---

## Authentication

### How JWT Authentication Works

1. **Register or Login**: User registers via `/api/auth/register` or logs in via `/api/auth/login`
2. **Token Generation**: Server returns a JWT access token
3. **Token Storage**: Client stores the token (usually in browser localStorage or sessionStorage)
4. **Authenticated Requests**: Client includes token in the `Authorization` header for protected endpoints
5. **Token Verification**: Server verifies token validity and user permissions

### Using the Token

All authenticated endpoints require the Authorization header:

```bash
Authorization: Bearer <your_access_token_here>
```

**Example**:

```bash
curl http://127.0.0.1:8000/api/candidates \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJyZWNydWl0ZXJAaGlyZWFpLmNvbSIsImVtYWlsIjoicmVjcnVpdGVyQGhpcmVhaS5jb20iLCJuYW1lIjoiUmVjcnVpdGVyIFVzZXIiLCJyb2xlIjoicmVjcnVpdGVyIn0.ABC123..."

### Swagger UI Authorize

Swagger uses HTTP Bearer auth. Paste the token in the **Authorize** dialog:

```
Bearer <access_token>
```

All `/api/candidates`, `/api/jobs`, and `/api/applications` routes require a Bearer token.
```

### Token Expiration

- **Default Expiration**: 60 minutes (configurable via `ACCESS_TOKEN_EXPIRE_MINUTES` in `.env`)
- **After Expiration**: Token becomes invalid and user must login again
- **Response**: `401 Unauthorized` if token is expired

---

## Verification Checklist

### 1) Health Check

```bash
curl http://127.0.0.1:8000/health
```

### 2) Register and Login

```bash
curl -X POST http://127.0.0.1:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"name":"Test User","email":"test@example.com","password":"admin123","role":"recruiter"}'

curl -X POST http://127.0.0.1:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"recruiter@hireai.com","password":"admin123"}'
```

Both should return `access_token` and `token_type`.

### 3) Verify Token

```bash
curl http://127.0.0.1:8000/api/auth/me \
  -H "Authorization: Bearer <access_token>"
```

### 4) Protected Endpoints

```bash
curl http://127.0.0.1:8000/api/candidates \
  -H "Authorization: Bearer <access_token>"

curl http://127.0.0.1:8000/api/jobs \
  -H "Authorization: Bearer <access_token>"

curl http://127.0.0.1:8000/api/applications \
  -H "Authorization: Bearer <access_token>"
```

### 5) Filtering

```bash
curl "http://127.0.0.1:8000/api/applications?job_id=1&status=pending" \
  -H "Authorization: Bearer <access_token>"
```

### 6) Negative Tests

```bash
# Missing token
curl -i http://127.0.0.1:8000/api/jobs

# Invalid token
curl -i http://127.0.0.1:8000/api/jobs \
  -H "Authorization: Bearer badtoken"
```

Expected: `403` for missing token, `401` for invalid token.

Note: Candidates/jobs/applications require a reachable database. If the DB is down or blocked, these endpoints will time out.

---

## Docker Deployment

### Why Docker?

Docker containerizes your application and database, ensuring consistency across different machines and simplifying deployment.

### Prerequisites

- Docker installed ([https://www.docker.com/products/docker-desktop](https://www.docker.com/products/docker-desktop))
- Docker Compose included with Docker Desktop

### Building and Running with Docker Compose

#### Step 1: Navigate to the Project

```bash
cd path/to/Skillvance/backend
```

#### Step 2: Build and Start Services

```bash
docker compose up --build
```

**What this does**:
- Builds the FastAPI application image
- Starts PostgreSQL database container
- Starts FastAPI application container
- Sets up networking between containers

#### Step 3: Access the API

```
http://127.0.0.1:8000
```

#### Step 4: View Swagger API Documentation

```
http://127.0.0.1:8000/docs
```

#### Step 5: Stop the Services

```bash
docker compose down
```

**Useful Docker Commands**:

```bash
# View running containers
docker compose ps

# View logs
docker compose logs -f

# Stop services but keep data
docker compose stop

# Remove services and volumes
docker compose down -v
```

### Why Docker Compose Over Plain Docker?

- **Service Networking**: Containers communicate by service name (e.g., `db:5432`)
- **Automatic Startup**: Both database and API start in correct order
- **Environment Isolation**: Each service has isolated environment and ports
- **Simplified Configuration**: Everything defined in `docker-compose.yml`

---

## Database Migrations

### Why Alembic?

Alembic manages database schema changes safely, tracking migrations and allowing rollbacks.

### Common Migration Commands

#### Check Current Database Version

```bash
alembic current
```

#### Apply All Pending Migrations

```bash
alembic upgrade head
```

**Why**: Applies schema changes to the database. Run this after pulling new code or updating requirements.

#### Rollback Last Migration

```bash
alembic downgrade -1
```

#### Create a New Migration

After modifying models, create a migration:

```bash
alembic revision --autogenerate -m "Add new_column to candidates"
```

Then review and apply:

```bash
alembic upgrade head
```

### Migration Files

Located in `alembic/versions/`, migration files track all schema changes with timestamps and sequential numbering.

---

## Documentation

### Interactive API Docs (Swagger UI)

```
http://127.0.0.1:8000/docs
```

**Features**:
- Interactive endpoint testing
- Automatic request/response documentation
- Authentication token integration
- Schema validation visualization

### Alternative OpenAPI Documentation (ReDoc)

```
http://127.0.0.1:8000/redoc
```

**Features**:
- Read-only, beautifully formatted documentation
- Better for documentation publishing
- Organized by tags (Authentication, Candidates, etc.)

### OpenAPI JSON Schema

```
http://127.0.0.1:8000/api/openapi.json
```

Used by tools and clients to understand the API structure programmatically.

---

## Common Issues and Troubleshooting

### Issue: `Connection refused` when connecting to database

**Solution**: Ensure `DATABASE_URL` in `.env` is correct and database is running.

### Issue: Virtual environment not activated

**Solution**: Run `source venv/bin/activate` (Linux/macOS) or `venv\Scripts\activate` (Windows).

### Issue: Module not found errors

**Solution**: Ensure all dependencies are installed with `pip install -r requirements.txt`.

### Issue: Port 8000 already in use

**Solution**: Run on a different port:
```bash
uvicorn app.main:app --port 8001
```

### Issue: JWT token errors

**Solution**: Ensure token is included in Authorization header and hasn't expired. Login again to get a fresh token.

---

## Support and Resources

- FastAPI Documentation: [https://fastapi.tiangolo.com](https://fastapi.tiangolo.com)
- SQLAlchemy Documentation: [https://docs.sqlalchemy.org](https://docs.sqlalchemy.org)
- PostgreSQL Documentation: [https://www.postgresql.org/docs](https://www.postgresql.org/docs)
- Alembic Documentation: [https://alembic.sqlalchemy.org](https://alembic.sqlalchemy.org)

---

## License

This project is part of the HireAI Copilot platform.
