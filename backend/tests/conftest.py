import os

os.environ.setdefault("TMDB_API_KEY", "test-api-key")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-for-pytest-only-32c")

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.dependencies import get_db
from app.models.base import Base

TEST_DB_URL = os.environ.get(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@postgres:5432/moviediscovery_test",
)
ADMIN_URL = os.environ.get(
    "ADMIN_DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@postgres:5432/postgres",
)


@pytest.fixture(scope="session", autouse=True)
async def _create_test_db():
    admin = create_async_engine(ADMIN_URL)
    async with admin.connect() as conn:
        await conn.execution_options(isolation_level="AUTOCOMMIT")
        await conn.execute(text("DROP DATABASE IF EXISTS moviediscovery_test"))
        await conn.execute(text("CREATE DATABASE moviediscovery_test"))
    await admin.dispose()


@pytest.fixture
async def db_session():
    engine = create_async_engine(TEST_DB_URL)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    async with session_factory() as session:
        yield session

    async with engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            await conn.execute(text(f"TRUNCATE TABLE {table.name} CASCADE"))
    await engine.dispose()


@pytest.fixture(autouse=True)
def _reset_rate_limits():
    # slowapi buckets are process-global; reset per test so login/register
    # limits don't leak across tests (limits still enforced within a test).
    from app.api.auth import limiter

    limiter.reset()


@pytest.fixture
def make_user_headers(client):
    """Register+login through the real API; return Authorization headers."""

    async def _make(email: str, password: str = "password123"):
        register = await client.post(
            "/api/v1/auth/register",
            json={"email": email, "password": password},
        )
        assert register.status_code == 201
        login = await client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": password},
        )
        assert login.status_code == 200
        return {
            "Authorization": f"Bearer {login.json()['access_token']}"
        }

    return _make


@pytest.fixture
async def client(db_session, mocker):
    from app.main import create_app

    async def override_get_db():
        try:
            yield db_session
            await db_session.commit()
        except Exception:
            await db_session.rollback()
            raise

    app = create_app()
    app.dependency_overrides[get_db] = override_get_db

    mock_tmdb = mocker.MagicMock()
    mock_tmdb.close = mocker.MagicMock()
    app.state.tmdb_client = mock_tmdb

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
