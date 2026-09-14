"""purge_expired removes only expired sessions."""

import uuid
from datetime import UTC, datetime, timedelta

import pytest

from app.repositories.refresh_token_repo import RefreshTokenRepository
from app.repositories.user_repo import UserRepository


@pytest.mark.asyncio
async def test_purge_expired_keeps_live_sessions(db_session):
    user = await UserRepository(db_session).create(
        email="purge@example.com", password_hash="x"
    )
    repo = RefreshTokenRepository(db_session)
    now = datetime.now(UTC)
    expired = await repo.store(
        user_id=user.id, family_id=uuid.uuid4(), token_hash="expired",
        expires_at=now - timedelta(seconds=1),
    )
    live = await repo.store(
        user_id=user.id, family_id=uuid.uuid4(), token_hash="live",
        expires_at=now + timedelta(days=30),
    )
    await db_session.commit()

    assert await repo.purge_expired() == 1
    await db_session.commit()

    assert await repo.get_by_hash("expired") is None
    assert (await repo.get_by_hash("live")).jti == live.jti
    assert expired.jti != live.jti
