import pytest


async def _login(client, email="ana@example.com", password="s3cure-pass"):
    await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password},
    )
    response = await client.post(
        "/api/v1/auth/login", json={"email": email, "password": password}
    )
    assert response.status_code == 200
    return response.json()


@pytest.mark.asyncio
async def test_refresh_rotates_and_kills_old_token(client):
    pair = await _login(client)

    rotated = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": pair["refresh_token"]},
    )

    assert rotated.status_code == 200
    new_pair = rotated.json()
    assert new_pair["refresh_token"] != pair["refresh_token"]

    reuse = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": pair["refresh_token"]},
    )
    assert reuse.status_code == 401


@pytest.mark.asyncio
async def test_reuse_triggers_family_revocation(client):
    pair = await _login(client)
    rotated = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": pair["refresh_token"]},
    )
    r2 = rotated.json()["refresh_token"]
    # Reuse the spent R1: family dies, so even the live R2 is rejected.
    await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": pair["refresh_token"]},
    )
    dead = await client.post(
        "/api/v1/auth/refresh", json={"refresh_token": r2}
    )

    assert dead.status_code == 401


@pytest.mark.asyncio
async def test_refresh_unknown_token_returns_401(client):
    response = await client.post(
        "/api/v1/auth/refresh", json={"refresh_token": "bogus"}
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_logout_kills_session(client):
    pair = await _login(client)

    logout = await client.post(
        "/api/v1/auth/logout",
        json={"refresh_token": pair["refresh_token"]},
        headers={"Authorization": f"Bearer {pair['access_token']}"},
    )
    assert logout.status_code == 204

    gone = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": pair["refresh_token"]},
    )
    assert gone.status_code == 401


@pytest.mark.asyncio
async def test_logout_requires_auth(client):
    response = await client.post(
        "/api/v1/auth/logout", json={"refresh_token": "whatever"}
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_logout_all_kills_every_session(client):
    pair1 = await _login(client)
    # Second session for the same user.
    login2 = await client.post(
        "/api/v1/auth/login",
        json={"email": "ana@example.com", "password": "s3cure-pass"},
    )
    pair2 = login2.json()

    everywhere = await client.post(
        "/api/v1/auth/logout-all",
        headers={"Authorization": f"Bearer {pair1['access_token']}"},
    )
    assert everywhere.status_code == 204

    for token in (pair1["refresh_token"], pair2["refresh_token"]):
        dead = await client.post(
            "/api/v1/auth/refresh", json={"refresh_token": token}
        )
        assert dead.status_code == 401
