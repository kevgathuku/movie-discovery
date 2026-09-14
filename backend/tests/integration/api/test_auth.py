import pytest


@pytest.mark.asyncio
async def test_register_returns_user_without_password_material(client):
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": "ana@example.com", "password": "s3cure-pass"},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "ana@example.com"
    assert data["role"] == "user"
    assert "password" not in data
    assert "password_hash" not in data


@pytest.mark.asyncio
async def test_register_duplicate_email_returns_409(client):
    await client.post(
        "/api/v1/auth/register",
        json={"email": "ana@example.com", "password": "s3cure-pass"},
    )
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": "ANA@example.com", "password": "other-pass"},
    )

    assert response.status_code == 409


@pytest.mark.asyncio
async def test_register_invalid_input_returns_422(client):
    bad_email = await client.post(
        "/api/v1/auth/register",
        json={"email": "not-an-email", "password": "s3cure-pass"},
    )
    short_pw = await client.post(
        "/api/v1/auth/register",
        json={"email": "ana@example.com", "password": "short"},
    )

    assert bad_email.status_code == 422
    assert short_pw.status_code == 422


@pytest.mark.asyncio
async def test_login_returns_token_pair(client):
    await client.post(
        "/api/v1/auth/register",
        json={"email": "ana@example.com", "password": "s3cure-pass"},
    )
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "ana@example.com", "password": "s3cure-pass"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["token_type"] == "bearer"
    assert data["access_token"]
    assert data["refresh_token"]
    assert "password" not in data


@pytest.mark.asyncio
async def test_login_wrong_password_returns_generic_401(client):
    await client.post(
        "/api/v1/auth/register",
        json={"email": "ana@example.com", "password": "s3cure-pass"},
    )
    wrong_pw = await client.post(
        "/api/v1/auth/login",
        json={"email": "ana@example.com", "password": "wrong-pass"},
    )
    unknown = await client.post(
        "/api/v1/auth/login",
        json={"email": "nobody@example.com", "password": "whatever"},
    )

    assert wrong_pw.status_code == 401
    assert unknown.status_code == 401
    assert wrong_pw.json() == unknown.json()  # no email oracle


@pytest.mark.asyncio
async def test_me_returns_current_user(client):
    await client.post(
        "/api/v1/auth/register",
        json={"email": "ana@example.com", "password": "s3cure-pass"},
    )
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": "ana@example.com", "password": "s3cure-pass"},
    )
    access = login.json()["access_token"]

    response = await client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {access}"}
    )

    assert response.status_code == 200
    assert response.json()["email"] == "ana@example.com"


@pytest.mark.asyncio
async def test_me_without_token_returns_401(client):
    response = await client.get("/api/v1/auth/me")

    assert response.status_code == 401
