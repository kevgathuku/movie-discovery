import uuid
from datetime import UTC, datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.refresh_token import RefreshToken


class RefreshTokenRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def store(
        self,
        user_id: int,
        family_id: uuid.UUID,
        token_hash: str,
        expires_at: datetime,
    ) -> RefreshToken:
        record = RefreshToken(
            user_id=user_id,
            family_id=family_id,
            token_hash=token_hash,
            expires_at=expires_at,
        )
        self.session.add(record)
        await self.session.flush()
        return record

    async def get_by_hash(
        self, token_hash: str, for_update: bool = False
    ) -> RefreshToken | None:
        query = select(RefreshToken).where(
            RefreshToken.token_hash == token_hash
        )
        if for_update:
            # Serializes concurrent rotations of the same token: the loser
            # blocks until the winner commits, then sees the revoked record.
            query = query.with_for_update()
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def revoke(self, record: RefreshToken) -> None:
        record.revoked_at = datetime.now(UTC)
        await self.session.flush()

    async def _revoke_where(self, *conditions) -> int:
        result = await self.session.execute(
            update(RefreshToken)
            .where(*conditions, RefreshToken.revoked_at.is_(None))
            .values(revoked_at=datetime.now(UTC))
        )
        return result.rowcount

    async def revoke_family(self, family_id: uuid.UUID) -> int:
        return await self._revoke_where(RefreshToken.family_id == family_id)

    async def revoke_all_for_user(self, user_id: int) -> int:
        return await self._revoke_where(RefreshToken.user_id == user_id)

    async def purge_expired(self) -> int:
        result = await self.session.execute(
            RefreshToken.__table__.delete().where(
                RefreshToken.expires_at < datetime.now(UTC)
            )
        )
        return result.rowcount
