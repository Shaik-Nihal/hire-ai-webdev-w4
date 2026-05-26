from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.config import settings
from app.core.security import build_user_response, create_access_token, get_current_user, verify_login_credentials
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(payload: RegisterRequest) -> TokenResponse:
    user = build_user_response(email=payload.email, name=payload.name, role=payload.role)
    token = create_access_token(
        subject=user.email,
        extra_claims={
            "email": user.email,
            "name": user.name,
            "role": user.role,
            "created_at": user.created_at.isoformat(),
        },
    )
    return TokenResponse(access_token=token, user=user)


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest) -> TokenResponse:
    email = payload.email
    password = payload.password

    if not verify_login_credentials(email, password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    user = build_user_response(
        email=settings.AUTH_LOGIN_EMAIL,
        name=settings.AUTH_USER_NAME,
        role=settings.AUTH_USER_ROLE,
    )
    token = create_access_token(
        subject=user.email,
        extra_claims={
            "email": user.email,
            "name": user.name,
            "role": user.role,
            "created_at": user.created_at.isoformat(),
        },
    )
    return TokenResponse(access_token=token, user=user)


@router.get("/me", response_model=UserResponse)
async def me(current_user: UserResponse = Depends(get_current_user)) -> UserResponse:
    return current_user
