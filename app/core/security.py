from datetime import UTC, datetime, timedelta

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from app.core.config import settings
from app.schemas.auth import UserResponse

bearer_scheme = HTTPBearer()
ALLOWED_ROLES = {"admin", "recruiter", "viewer"}


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


def _create_token(
    subject: str,
    token_type: str,
    expires_delta: timedelta | None = None,
    extra_claims: dict[str, str] | None = None,
) -> str:
    expire = datetime.now(UTC) + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    payload: dict[str, object] = {"sub": subject, "exp": expire, "type": token_type}
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_access_token(
    subject: str,
    expires_delta: timedelta | None = None,
    extra_claims: dict[str, str] | None = None,
) -> str:
    return _create_token(
        subject=subject,
        token_type="access",
        expires_delta=expires_delta,
        extra_claims=extra_claims,
    )


def create_refresh_token(
    subject: str,
    extra_claims: dict[str, str] | None = None,
) -> str:
    return _create_token(
        subject=subject,
        token_type="refresh",
        expires_delta=timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        extra_claims=extra_claims,
    )


def decode_token_payload(token: str, *, detail: str = "Could not validate credentials") -> dict[str, object]:
    try:
        return jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    except (JWTError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


def build_user_from_payload(payload: dict[str, object]) -> UserResponse:
    created_at_raw = payload.get("created_at")
    created_at = datetime.fromisoformat(created_at_raw) if isinstance(created_at_raw, str) else datetime.now(UTC)
    return _build_user_response(
        email=str(payload.get("sub") or settings.AUTH_LOGIN_EMAIL),
        name=str(payload.get("name") or settings.AUTH_USER_NAME),
        role=str(payload.get("role") or settings.AUTH_USER_ROLE),
        created_at=created_at,
    )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> UserResponse:
    token = credentials.credentials
    payload = decode_token_payload(token)

    token_type = payload.get("type")
    if token_type not in (None, "access"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid access token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if payload.get("sub") is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return build_user_from_payload(payload)


def build_user_response(
    email: str,
    name: str | None = None,
    role: str | None = None,
) -> UserResponse:
    return _build_user_response(email=email, name=name, role=role)


def build_login_user(email: str | None = None) -> UserResponse:
    return _build_user_response(email=email or settings.AUTH_LOGIN_EMAIL)


def require_roles(*roles: str):
    invalid_roles = [role for role in roles if role not in ALLOWED_ROLES]
    if invalid_roles:
        raise ValueError(f"Unknown roles: {', '.join(invalid_roles)}")

    async def _require_roles(current_user: UserResponse = Depends(get_current_user)) -> UserResponse:
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return current_user

    return _require_roles
