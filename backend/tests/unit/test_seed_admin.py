import contextlib

import pytest

from app.models.user import UserRole
from app.repositories.user_repo import UserRepository
from app.seed_admin import seed_admin


@pytest.fixture
def factory(db_session):
    @contextlib.asynccontextmanager
    async def _factory():
        yield db_session
        await db_session.commit()

    return _factory


@pytest.mark.asyncio
async def test_seed_creates_first_admin(factory, monkeypatch, db_session):
    monkeypatch.setenv("ADMIN_EMAIL", "Root@Example.com")
    monkeypatch.setenv("ADMIN_PASSWORD", "sup3r-secret")

    assert await seed_admin(session_factory=factory) == 0

    user = await UserRepository(db_session).get_by_email("root@example.com")
    assert user is not None
    assert user.role == UserRole.admin
    assert user.password_hash != "sup3r-secret"


@pytest.mark.asyncio
async def test_seed_refuses_second_admin(factory, monkeypatch):
    monkeypatch.setenv("ADMIN_EMAIL", "one@example.com")
    monkeypatch.setenv("ADMIN_PASSWORD", "sup3r-secret")
    assert await seed_admin(session_factory=factory) == 0

    monkeypatch.setenv("ADMIN_EMAIL", "two@example.com")
    assert await seed_admin(session_factory=factory) == 1


@pytest.mark.asyncio
async def test_seed_force_creates_another(factory, monkeypatch, db_session):
    monkeypatch.setenv("ADMIN_EMAIL", "one@example.com")
    monkeypatch.setenv("ADMIN_PASSWORD", "sup3r-secret")
    assert await seed_admin(session_factory=factory) == 0

    monkeypatch.setenv("ADMIN_EMAIL", "two@example.com")
    assert await seed_admin(force=True, session_factory=factory) == 0
    assert (
        await UserRepository(db_session).get_by_email("two@example.com")
    ) is not None


@pytest.mark.asyncio
async def test_seed_missing_env_returns_2(factory, monkeypatch):
    monkeypatch.delenv("ADMIN_EMAIL", raising=False)
    monkeypatch.delenv("ADMIN_PASSWORD", raising=False)

    assert await seed_admin(session_factory=factory) == 2


@pytest.mark.asyncio
async def test_seed_short_password_returns_2(factory, monkeypatch):
    monkeypatch.setenv("ADMIN_EMAIL", "x@example.com")
    monkeypatch.setenv("ADMIN_PASSWORD", "short")

    assert await seed_admin(session_factory=factory) == 2
