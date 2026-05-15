from datetime import UTC, datetime
from json import JSONDecodeError

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.core.config import settings
from app.core.security import build_user_response, create_access_token, get_current_user, verify_login_credentials
from app.schemas.auth import RegisterRequest, TokenResponse, UserResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(payload: RegisterRequest) -> UserResponse:
    return build_user_response(email=payload.email, name=payload.name, role=payload.role)


@router.post("/login", response_model=TokenResponse)
async def login(request: Request) -> TokenResponse:
    content_type = request.headers.get("content-type", "")

    email: str | None = None
    password: str | None = None

    if "application/x-www-form-urlencoded" in content_type or "multipart/form-data" in content_type:
        form = await request.form()
        email = form.get("username") or form.get("email")
        password = form.get("password")
    else:
        try:
            payload = await request.json()
        except JSONDecodeError as exc:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid login payload") from exc

        email = payload.get("email")
        password = payload.get("password")

    if not isinstance(email, str) or not isinstance(password, str):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Email and password are required")

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
