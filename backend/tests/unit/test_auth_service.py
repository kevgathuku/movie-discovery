import uuid
from datetime import datetime

import pytest

from app.exceptions import InvalidCredentialsError, UserAlreadyExistsError
from app.models.user import User, UserRole
from app.services.auth_service import AuthService


def _user(**kwargs):
    defaults = {
        "id": 1,
        "email": "ana@example.com",
        "password_hash": "hashed",
        "role": UserRole.user,
        "is_active": True,
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
    }
    defaults.update(kwargs)
    return User(**defaults)


@pytest.fixture
def service(mock_db):
    return AuthService(mock_db)


@pytest.fixture
def mock_db(mocker):
    return mocker.AsyncMock()


@pytest.mark.asyncio
async def test_register_creates_user_with_hashed_password(service, mocker):
    mocker.patch.object(
        service.users, "get_by_email", return_value=None
    )
    created = _user()
    create_mock = mocker.patch.object(
        service.users, "create", return_value=created
    )
    hash_mock = mocker.patch(
        "app.services.auth_service.hash_password", return_value="HASHED"
    )

    result = await service.register("  ANA@Example.com ", "s3cure-pass")

    hash_mock.assert_called_once_with("s3cure-pass")
    assert create_mock.call_args.kwargs["password_hash"] == "HASHED"
    assert result is created


@pytest.mark.asyncio
async def test_register_duplicate_email_raises(service, mocker):
    mocker.patch.object(
        service.users, "get_by_email", return_value=_user()
    )

    with pytest.raises(UserAlreadyExistsError):
        await service.register("ana@example.com", "s3cure-pass")


@pytest.mark.asyncio
async def test_register_short_password_raises(service, mocker):
    mocker.patch.object(
        service.users, "get_by_email", return_value=None
    )

    with pytest.raises(ValueError, match="8 characters"):
        await service.register("ana@example.com", "short")


@pytest.mark.asyncio
async def test_authenticate_ok(service, mocker):
    mocker.patch.object(
        service.users, "get_by_email",
        return_value=_user(password_hash="HASHED"),
    )
    mocker.patch(
        "app.services.auth_service.verify_password", return_value=True
    )

    result = await service.authenticate("ana@example.com", "s3cure-pass")

    assert result.email == "ana@example.com"


@pytest.mark.asyncio
async def test_authenticate_unknown_email_raises(service, mocker):
    mocker.patch.object(
        service.users, "get_by_email", return_value=None
    )
    verify = mocker.patch("app.services.auth_service.verify_password")

    with pytest.raises(InvalidCredentialsError):
        await service.authenticate("nobody@example.com", "whatever")
    verify.assert_not_called()


@pytest.mark.asyncio
async def test_authenticate_wrong_password_raises(service, mocker):
    mocker.patch.object(
        service.users, "get_by_email",
        return_value=_user(password_hash="HASHED"),
    )
    mocker.patch(
        "app.services.auth_service.verify_password", return_value=False
    )

    with pytest.raises(InvalidCredentialsError):
        await service.authenticate("ana@example.com", "wrong")


@pytest.mark.asyncio
async def test_authenticate_inactive_user_raises(service, mocker):
    mocker.patch.object(
        service.users, "get_by_email", return_value=_user(is_active=False)
    )
    verify = mocker.patch("app.services.auth_service.verify_password")

    with pytest.raises(InvalidCredentialsError):
        await service.authenticate("ana@example.com", "s3cure-pass")
    verify.assert_not_called()


@pytest.mark.asyncio
async def test_issue_pair_stores_hashed_refresh(service, mocker):
    store_mock = mocker.patch.object(service.tokens, "store")
    user = _user()

    access, refresh = await service.issue_pair(user)

    assert access and refresh and access != refresh
    store_mock.assert_called_once()
    _, kwargs = store_mock.call_args
    assert kwargs["user_id"] == 1
    assert isinstance(kwargs["family_id"], uuid.UUID)
    assert kwargs["token_hash"] != refresh  # hash at rest, never the token
    assert (kwargs["expires_at"] - datetime.now(
        kwargs["expires_at"].tzinfo)).days == 29
