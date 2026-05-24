from datetime import UTC, datetime, timedelta

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from app.core.config import settings
from app.schemas.auth import UserResponse

bearer_scheme = HTTPBearer()


def _build_user_response(
    email: str,
    name: str | None = None,
    role: str | None = None,
    created_at: datetime | None = None,
) -> UserResponse:
    return UserResponse(
        id=1,
        name=name or settings.AUTH_USER_NAME,
        email=email,
        role=role or settings.AUTH_USER_ROLE,
        created_at=created_at or datetime.now(UTC),
    )


def verify_login_credentials(email: str, password: str) -> bool:
    return email == settings.AUTH_LOGIN_EMAIL and password == settings.AUTH_LOGIN_PASSWORD


def create_access_token(
    subject: str,
    expires_delta: timedelta | None = None,
    extra_claims: dict[str, str] | None = None,
) -> str:
    expire = datetime.now(UTC) + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    payload: dict[str, object] = {"sub": subject, "exp": expire}
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> UserResponse:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    token = credentials.credentials

    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        email = payload.get("sub")
        if email is None:
            raise credentials_exception
    except (JWTError, ValueError) as exc:
        raise credentials_exception from exc

    created_at_raw = payload.get("created_at")
    created_at = datetime.fromisoformat(created_at_raw) if isinstance(created_at_raw, str) else datetime.now(UTC)
    return _build_user_response(
        email=str(email),
        name=str(payload.get("name") or settings.AUTH_USER_NAME),
        role=str(payload.get("role") or settings.AUTH_USER_ROLE),
        created_at=created_at,
    )


def build_user_response(
    email: str,
    name: str | None = None,
    role: str | None = None,
) -> UserResponse:
    return _build_user_response(email=email, name=name, role=role)


def build_login_user(email: str | None = None) -> UserResponse:
    return _build_user_response(email=email or settings.AUTH_LOGIN_EMAIL)
