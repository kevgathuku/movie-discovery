import uuid
from datetime import UTC, datetime, timedelta

import pytest

from app.exceptions import TokenRevokedError
from app.models.refresh_token import RefreshToken
from app.models.user import User, UserRole
from app.services.auth_service import AuthService


def _user(**kwargs):
    now = datetime.now(UTC)
    defaults = {
        "id": 1,
        "email": "ana@example.com",
        "password_hash": "hashed",
        "role": UserRole.user,
        "is_active": True,
        "created_at": now,
        "updated_at": now,
    }
    defaults.update(kwargs)
    return User(**defaults)


def _record(**kwargs):
    now = datetime.now(UTC)
    defaults = {
        "jti": uuid.uuid4(),
        "user_id": 1,
        "family_id": uuid.uuid4(),
        "token_hash": "hash",
        "expires_at": now + timedelta(days=30),
        "revoked_at": None,
        "created_at": now,
    }
    defaults.update(kwargs)
    return RefreshToken(**defaults)


@pytest.fixture
def service(mock_db):
    return AuthService(mock_db)


@pytest.fixture
def mock_db(mocker):
    return mocker.AsyncMock()


@pytest.mark.asyncio
async def test_rotate_issues_new_pair_same_family(service, mocker):
    old = _record()
    mocker.patch.object(service.tokens, "get_by_hash", return_value=old)
    mocker.patch.object(
        service.users, "get_by_id", return_value=_user()
    )
    revoke = mocker.patch.object(service.tokens, "revoke")
    store = mocker.patch.object(service.tokens, "store")
    purge = mocker.patch.object(service.tokens, "purge_expired")

    user, access, refresh = await service.rotate_refresh("OLD")

    revoke.assert_called_once_with(old)
    purge.assert_called_once()
    assert store.call_args.kwargs["family_id"] == old.family_id
    assert user.id == 1 and access and refresh


@pytest.mark.asyncio
async def test_rotate_unknown_token_raises(service, mocker):
    mocker.patch.object(
        service.tokens, "get_by_hash", return_value=None
    )

    with pytest.raises(TokenRevokedError):
        await service.rotate_refresh("NOPE")


@pytest.mark.asyncio
async def test_rotate_expired_token_raises(service, mocker):
    mocker.patch.object(
        service.tokens,
        "get_by_hash",
        return_value=_record(expires_at=datetime.now(UTC) - timedelta(seconds=1)),
    )

    with pytest.raises(TokenRevokedError):
        await service.rotate_refresh("STALE")


@pytest.mark.asyncio
async def test_reuse_of_rotated_token_revokes_family(service, mocker):
    spent = _record(revoked_at=datetime.now(UTC))
    mocker.patch.object(
        service.tokens, "get_by_hash", return_value=spent
    )
    revoke_family = mocker.patch.object(service.tokens, "revoke_family")

    with pytest.raises(TokenRevokedError):
        await service.rotate_refresh("SPENT")
    revoke_family.assert_called_once_with(spent.family_id)


@pytest.mark.asyncio
async def test_rotate_deactivated_user_raises(service, mocker):
    mocker.patch.object(
        service.tokens, "get_by_hash", return_value=_record()
    )
    mocker.patch.object(
        service.users, "get_by_id", return_value=_user(is_active=False)
    )

    with pytest.raises(TokenRevokedError):
        await service.rotate_refresh("OLD")


@pytest.mark.asyncio
async def test_logout_revokes_session(service, mocker):
    record = _record()
    mocker.patch.object(
        service.tokens, "get_by_hash", return_value=record
    )
    revoke = mocker.patch.object(service.tokens, "revoke")

    await service.logout("TOKEN")

    revoke.assert_called_once_with(record)


@pytest.mark.asyncio
async def test_logout_unknown_token_is_silent(service, mocker):
    mocker.patch.object(
        service.tokens, "get_by_hash", return_value=None
    )
    revoke = mocker.patch.object(service.tokens, "revoke")

    await service.logout("NOPE")

    revoke.assert_not_called()


@pytest.mark.asyncio
async def test_logout_all_revokes_everything(service, mocker):
    revoke_all = mocker.patch.object(
        service.tokens, "revoke_all_for_user", return_value=3
    )

    count = await service.logout_all(_user())

    revoke_all.assert_called_once_with(1)
    assert count == 3
