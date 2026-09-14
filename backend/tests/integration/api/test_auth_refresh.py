import asyncio

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


@pytest.mark.asyncio
async def test_concurrent_rotation_single_winner(db_session, session_factory, mocker):
    """Two simultaneous rotations of one token: exactly one succeeds.

    A holds the refresh row (SELECT FOR UPDATE) while paused mid-rotation;
    B must block on the lock instead of minting a second pair. After A
    commits, B sees the revoked record and the family dies (reuse policy).
    """
    from app.exceptions import TokenRevokedError
    from app.security.tokens import hash_token
    from app.services.auth_service import AuthService

    svc_a = AuthService(db_session)
    user = await svc_a.register(email="race@example.com", password="s3cure-pass")
    await db_session.commit()
    _, r1 = await svc_a.issue_pair(user)
    await db_session.commit()

    factory = session_factory
    locked = asyncio.Event()
    release = asyncio.Event()

    original_revoke = svc_a.tokens.revoke

    async def pausing_revoke(record):
        locked.set()
        await release.wait()
        await original_revoke(record)

    mocker.patch.object(
        svc_a.tokens, "revoke", new=mocker.AsyncMock(side_effect=pausing_revoke)
    )

    task_a = asyncio.create_task(svc_a.rotate_refresh(r1))
    task_b = None
    try:
        await asyncio.wait_for(locked.wait(), timeout=10)

        async with factory() as session_b:
            svc_b = AuthService(session_b)
            task_b = asyncio.create_task(svc_b.rotate_refresh(r1))
            await asyncio.sleep(1.0)
            assert not task_b.done(), "concurrent rotation minted a second pair"

            release.set()
            _, _, r2 = await asyncio.wait_for(task_a, timeout=10)
            await db_session.commit()

            with pytest.raises(TokenRevokedError):
                await asyncio.wait_for(task_b, timeout=10)
            await session_b.commit()  # persist family revocation, like the route
    finally:
        release.set()
        pending = [t for t in (task_a, task_b) if t is not None and not t.done()]
        for t in pending:
            t.cancel()
        if pending:
            await asyncio.gather(*pending, return_exceptions=True)

    db_session.expire_all()
    r2_record = await svc_a.tokens.get_by_hash(hash_token(r2))
    assert r2_record is not None and r2_record.revoked_at is not None
