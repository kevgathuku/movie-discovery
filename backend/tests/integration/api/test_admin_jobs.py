import pytest

from app.models.job import Job, JobStatus
from app.models.user import User, UserRole
from app.security.passwords import hash_password
from app.security.tokens import mint_access_token


@pytest.fixture
async def admin_headers(client, db_session):
    admin = User(
        email="admin@example.com",
        password_hash=hash_password("password123"),
        role=UserRole.admin,
    )
    db_session.add(admin)
    await db_session.commit()
    token = mint_access_token(admin.id, admin.role.value)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
async def user_headers(client, make_user_headers):
    return await make_user_headers("user@example.com")


@pytest.fixture
async def sample_job(db_session):
    job = Job(id="Xb3nK9", job_type="sync_trending", status=JobStatus.completed,
              progress=100)
    db_session.add(job)
    await db_session.commit()
    return job


@pytest.mark.asyncio
async def test_admin_jobs_anonymous_returns_401(client):
    assert (await client.get("/admin/jobs")).status_code == 401
    assert (await client.get("/admin/jobs/Xb3nK9")).status_code == 401


@pytest.mark.asyncio
async def test_admin_jobs_user_returns_403(client, user_headers):
    assert (
        await client.get("/admin/jobs", headers=user_headers)
    ).status_code == 403
    assert (
        await client.get("/admin/jobs/Xb3nK9", headers=user_headers)
    ).status_code == 403


@pytest.mark.asyncio
async def test_admin_lists_jobs(
    client, admin_headers, sample_job
):
    response = await client.get("/admin/jobs", headers=admin_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["jobs"][0]["id"] == "Xb3nK9"
    assert data["jobs"][0]["status"] == "completed"


@pytest.mark.asyncio
async def test_admin_filters_jobs_by_status(
    client, admin_headers, sample_job
):
    match = await client.get(
        "/admin/jobs", params={"status": "completed"}, headers=admin_headers
    )
    assert match.json()["total"] == 1

    miss = await client.get(
        "/admin/jobs", params={"status": "failed"}, headers=admin_headers
    )
    assert miss.json()["total"] == 0


@pytest.mark.asyncio
async def test_admin_get_job_detail(client, admin_headers, sample_job):
    response = await client.get(
        "/admin/jobs/Xb3nK9", headers=admin_headers
    )

    assert response.status_code == 200
    assert response.json()["job_type"] == "sync_trending"


@pytest.mark.asyncio
async def test_admin_get_missing_job_returns_404(client, admin_headers):
    response = await client.get(
        "/admin/jobs/doesnotexist", headers=admin_headers
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_admin_routes_hidden_from_openapi(client):
    schema = (await client.get("/openapi.json")).json()

    assert not any(
        path.startswith("/admin") for path in schema["paths"]
    )


@pytest.mark.asyncio
async def test_public_jobs_stub_is_gone(client):
    response = await client.get("/api/v1/jobs/anything")

    assert response.status_code == 404
