"""Full user journey in one test: the E2E script's core path, in-suite."""

from datetime import date

import pytest

from app.models.movie import Movie, MovieSource


@pytest.mark.asyncio
async def test_full_user_journey(client, db_session):
    # register → login
    assert (await client.post(
        "/api/v1/auth/register",
        json={"email": "journey@example.com", "password": "s3cure-pass"},
    )).status_code == 201
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": "journey@example.com", "password": "s3cure-pass"},
    )
    assert login.status_code == 200
    access, refresh = (
        login.json()["access_token"], login.json()["refresh_token"]
    )
    headers = {"Authorization": f"Bearer {access}"}

    # watchlist CRUD
    created = await client.post(
        "/api/v1/watchlists", json={"name": "Journey"}, headers=headers
    )
    assert created.status_code == 201
    wid = created.json()["id"]

    db_session.add(movie := Movie(
        tmdb_id=1, title="J", release_date=date(2000, 1, 1),
        source=MovieSource.sync,
    ))
    await db_session.commit()

    added = await client.post(
        f"/api/v1/watchlists/{wid}/entries",
        json={"movie_id": movie.id},
        headers=headers,
    )
    assert added.status_code == 201
    eid = added.json()["id"]

    watched = await client.patch(
        f"/api/v1/watchlists/{wid}/entries/{eid}",
        json={"status": "watched"},
        headers=headers,
    )
    assert watched.json()["status"] == "watched"

    # logout → session dead
    assert (await client.post(
        "/api/v1/auth/logout",
        json={"refresh_token": refresh},
        headers=headers,
    )).status_code == 204
    assert (await client.post(
        "/api/v1/auth/refresh", json={"refresh_token": refresh}
    )).status_code == 401
