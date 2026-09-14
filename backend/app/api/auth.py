from fastapi import APIRouter, Depends, HTTPException, Request, status
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.dependencies import get_current_user, get_db
from app.exceptions import (
    InvalidCredentialsError,
    TokenRevokedError,
    UserAlreadyExistsError,
)
from app.models.user import User
from app.schemas.auth import (
    RefreshRequest,
    TokenPairResponse,
    UserLoginRequest,
    UserRegisterRequest,
    UserResponse,
)
from app.services.auth_service import AuthService

# ponytail: in-process limiter; move to Redis when >1 API replica
limiter = Limiter(key_func=get_remote_address)

router = APIRouter(prefix="/auth", tags=["auth"])


def _token_pair(access: str, refresh: str) -> TokenPairResponse:
    return TokenPairResponse(
        access_token=access,
        refresh_token=refresh,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post(
    "/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED
)
@limiter.limit("10/minute")
async def register(
    request: Request,
    body: UserRegisterRequest,
    db: AsyncSession = Depends(get_db),
):
    try:
        user = await AuthService(db).register(
            email=str(body.email), password=body.password
        )
        await db.commit()
        return UserResponse.model_validate(user)
    except UserAlreadyExistsError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email is already registered",
        ) from e


@router.post("/login", response_model=TokenPairResponse)
@limiter.limit("5/minute")
async def login(
    request: Request,
    body: UserLoginRequest,
    db: AsyncSession = Depends(get_db),
):
    service = AuthService(db)
    try:
        user = await service.authenticate(
            email=str(body.email), password=body.password
        )
    except InvalidCredentialsError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        ) from e
    access, refresh = await service.issue_pair(user)
    await db.commit()
    return _token_pair(access, refresh)


@router.get("/me", response_model=UserResponse)
async def me(current_user: User = Depends(get_current_user)):
    return UserResponse.model_validate(current_user)


@router.post("/refresh", response_model=TokenPairResponse)
@limiter.limit("10/minute")
async def refresh(
    request: Request,
    body: RefreshRequest,
    db: AsyncSession = Depends(get_db),
):
    try:
        _, access, new_refresh = await AuthService(db).rotate_refresh(
            body.refresh_token
        )
    except TokenRevokedError as e:
        # Persist family revocation from reuse detection before responding.
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        ) from e
    await db.commit()
    return _token_pair(access, new_refresh)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    body: RefreshRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await AuthService(db).logout(body.refresh_token)
    await db.commit()


@router.post("/logout-all", status_code=status.HTTP_204_NO_CONTENT)
async def logout_all(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await AuthService(db).logout_all(current_user)
    await db.commit()
