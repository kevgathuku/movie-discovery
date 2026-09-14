import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.exceptions import (
    InvalidCredentialsError,
    TokenRevokedError,
    UserAlreadyExistsError,
)
from app.models.user import User
from app.repositories.refresh_token_repo import RefreshTokenRepository
from app.repositories.user_repo import UserRepository
from app.security.passwords import hash_password, verify_password
from app.security.tokens import (
    hash_token,
    mint_access_token,
    new_refresh_token,
)


class AuthService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.users = UserRepository(db)
        self.tokens = RefreshTokenRepository(db)

    async def register(self, email: str, password: str) -> User:
        if len(password) < 8:
            raise ValueError("password must be at least 8 characters")
        if await self.users.get_by_email(email) is not None:
            raise UserAlreadyExistsError(
                UserRepository.normalize_email(email)
            )
        return await self.users.create(
            email=email, password_hash=hash_password(password)
        )

    async def authenticate(self, email: str, password: str) -> User:
        user = await self.users.get_by_email(email)
        if user is None or not user.is_active:
            raise InvalidCredentialsError()
        if not verify_password(password, user.password_hash):
            raise InvalidCredentialsError()
        return user

    async def issue_pair(self, user: User) -> tuple[str, str]:
        access = mint_access_token(user.id, user.role.value)
        refresh, token_hash = new_refresh_token()
        await self.tokens.store(
            user_id=user.id,
            family_id=uuid.uuid4(),
            token_hash=token_hash,
            expires_at=datetime.now(UTC)
            + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        )
        return access, refresh

    async def _live_refresh_record(self, refresh_token: str):
        record = await self.tokens.get_by_hash(hash_token(refresh_token))
        if record is None or record.revoked_at is not None:
            raise TokenRevokedError()
        expires_at = record.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=UTC)
        if expires_at <= datetime.now(UTC):
            raise TokenRevokedError()
        return record
