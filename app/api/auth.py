from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.config import settings
from app.core.security import (
    build_user_from_payload,
    build_user_response,
    create_access_token,
    create_refresh_token,
    decode_token_payload,
    get_current_user,
    verify_login_credentials,
)
from app.schemas.auth import LoginRequest, RefreshTokenRequest, RegisterRequest, TokenResponse, UserResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])


def _build_claims(user: UserResponse) -> dict[str, str]:
    return {
        "email": user.email,
        "name": user.name,
        "role": user.role,
        "created_at": user.created_at.isoformat(),
    }


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(payload: RegisterRequest) -> TokenResponse:
    """
    Register a new recruiter/administrator account.
    
    Generates a secure access token and refresh token upon successful registration.
    """
    user = build_user_response(email=payload.email, name=payload.name, role=payload.role)
    claims = _build_claims(user)
    token = create_access_token(subject=user.email, extra_claims=claims)
    refresh_token = create_refresh_token(subject=user.email, extra_claims=claims)
    return TokenResponse(access_token=token, refresh_token=refresh_token, user=user)


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest) -> TokenResponse:
    """
    Authenticate credentials and obtain access and refresh tokens.
    
    Validates user credentials and issues a JSON Web Token (JWT) to access protected API endpoints.
    """
    email = payload.email
    password = payload.password

    if not verify_login_credentials(email, password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    user = build_user_response(
        email=settings.AUTH_LOGIN_EMAIL,
        name=settings.AUTH_USER_NAME,
        role=settings.AUTH_USER_ROLE,
    )
    claims = _build_claims(user)
    token = create_access_token(subject=user.email, extra_claims=claims)
    refresh_token = create_refresh_token(subject=user.email, extra_claims=claims)
    return TokenResponse(access_token=token, refresh_token=refresh_token, user=user)


@router.post("/refresh", response_model=TokenResponse)
async def refresh_access_token(payload: RefreshTokenRequest) -> TokenResponse:
    """
    Refresh an expired access token using a valid refresh token.
    
    Validates the refresh token and returns a fresh access token along with a new refresh token.
    """
    token_payload = decode_token_payload(payload.refresh_token, detail="Invalid refresh token")
    if token_payload.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    user = build_user_from_payload(token_payload)
    claims = _build_claims(user)
    access_token = create_access_token(subject=user.email, extra_claims=claims)
    refresh_token = create_refresh_token(subject=user.email, extra_claims=claims)
    return TokenResponse(access_token=access_token, refresh_token=refresh_token, user=user)


@router.get("/me", response_model=UserResponse)
async def me(current_user: UserResponse = Depends(get_current_user)) -> UserResponse:
    """
    Retrieve profile details of the currently authenticated user.
    
    Requires a valid JWT bearer token in the Authorization header.
    """
    return current_user
