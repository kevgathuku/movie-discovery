"""Rate limits are enforced (buckets reset per test in conftest)."""

import pytest


@pytest.mark.asyncio
async def test_login_rate_limited_after_5_per_minute(client):
    await client.post(
        "/api/v1/auth/register",
        json={"email": "rl@example.com", "password": "s3cure-pass"},
    )
    statuses = [
        (await client.post(
            "/api/v1/auth/login",
            json={"email": "rl@example.com", "password": "s3cure-pass"},
        )).status_code
        for _ in range(6)
    ]

    assert statuses[:5] == [200] * 5
    assert statuses[5] == 429


@pytest.mark.asyncio
async def test_register_rate_limited_after_10_per_minute(client):
    statuses = [
        (await client.post(
            "/api/v1/auth/register",
            json={"email": f"rl{i}@example.com", "password": "s3cure-pass"},
        )).status_code
        for i in range(11)
    ]

    assert statuses[:10] == [201] * 10
    assert statuses[10] == 429
