"""US3: watchlists are per-user. Cross-user access behaves as 404."""

from datetime import date

import pytest

from app.models.movie import Movie, MovieSource


@pytest.fixture
async def movie(db_session):
    movie = Movie(
        tmdb_id=550,
        imdb_id="tt0137566",
        title="Fight Club",
        synopsis="An insomniac office worker...",
        release_date=date(1999, 10, 15),
        rating=8.4,
        poster_url="https://image.tmdb.org/t/p/w500/poster.jpg",
        source=MovieSource.sync,
    )
    db_session.add(movie)
    await db_session.commit()
    return movie


@pytest.fixture
async def user_a(client, make_user_headers):
    return await make_user_headers("a@example.com")


@pytest.fixture
async def user_b(client, make_user_headers):
    return await make_user_headers("b@example.com")


@pytest.fixture
async def a_watchlist(client, user_a):
    response = await client.post(
        "/api/v1/watchlists", json={"name": "A's list"}, headers=user_a
    )
    assert response.status_code == 201
    return response.json()


@pytest.mark.asyncio
async def test_user_b_sees_empty_list(client, user_a, user_b, a_watchlist):
    response = await client.get("/api/v1/watchlists", headers=user_b)

    assert response.status_code == 200
    assert response.json()["watchlists"] == []


@pytest.mark.asyncio
async def test_user_b_cannot_read_a_watchlist(client, user_b, a_watchlist):
    response = await client.get(
        f"/api/v1/watchlists/{a_watchlist['id']}/entries", headers=user_b
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_user_b_cannot_rename_a_watchlist(client, user_b, a_watchlist):
    response = await client.patch(
        f"/api/v1/watchlists/{a_watchlist['id']}",
        json={"name": "Hijacked"},
        headers=user_b,
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_user_b_cannot_delete_a_watchlist(client, user_b, a_watchlist):
    response = await client.delete(
        f"/api/v1/watchlists/{a_watchlist['id']}", headers=user_b
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_user_b_cannot_add_to_a_watchlist(
    client, user_b, a_watchlist, movie
):
    response = await client.post(
        f"/api/v1/watchlists/{a_watchlist['id']}/entries",
        json={"movie_id": movie.id},
        headers=user_b,
    )

    assert response.status_code == 404


@pytest.fixture
async def a_entry(client, user_a, a_watchlist, movie):
    response = await client.post(
        f"/api/v1/watchlists/{a_watchlist['id']}/entries",
        json={"movie_id": movie.id},
        headers=user_a,
    )
    assert response.status_code == 201
    return response.json()


@pytest.mark.asyncio
async def test_user_b_cannot_mark_a_entry_watched(
    client, user_b, a_watchlist, a_entry
):
    response = await client.patch(
        f"/api/v1/watchlists/{a_watchlist['id']}/entries/{a_entry['id']}",
        json={"status": "watched"},
        headers=user_b,
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_user_b_cannot_remove_a_entry(
    client, user_b, a_watchlist, a_entry
):
    response = await client.delete(
        f"/api/v1/watchlists/{a_watchlist['id']}/entries/{a_entry['id']}",
        headers=user_b,
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_anonymous_watchlist_access_returns_401(client, a_watchlist):
    assert (await client.get("/api/v1/watchlists")).status_code == 401
    assert (
        await client.get(
            f"/api/v1/watchlists/{a_watchlist['id']}/entries"
        )
    ).status_code == 401
    assert (
        await client.post("/api/v1/watchlists", json={"name": "X"})
    ).status_code == 401
