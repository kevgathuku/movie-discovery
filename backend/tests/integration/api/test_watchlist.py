from datetime import date

import pytest

from app.models.movie import Movie, MovieSource
from app.models.watchlist import Watchlist, WatchlistEntry, WatchlistStatus


@pytest.fixture
async def sample_watchlist(db_session):
    watchlist = Watchlist(name="To Watch")
    db_session.add(watchlist)
    await db_session.commit()
    return watchlist


@pytest.fixture
async def sample_movie(db_session):
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
async def watchlist_with_entry(db_session, sample_watchlist, sample_movie):
    entry = WatchlistEntry(
        watchlist_id=sample_watchlist.id,
        movie_id=sample_movie.id,
        status=WatchlistStatus.to_watch,
    )
    db_session.add(entry)
    await db_session.commit()
    return entry


@pytest.mark.asyncio
async def test_create_watchlist(client):
    response = await client.post(
        "/api/v1/watchlists",
        json={"name": "Upcoming"},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Upcoming"
    assert "id" in data
    assert "created_at" in data


@pytest.mark.asyncio
async def test_list_watchlists(client, sample_watchlist):
    response = await client.get("/api/v1/watchlists")

    assert response.status_code == 200
    data = response.json()
    assert len(data["watchlists"]) == 1
    assert data["watchlists"][0]["name"] == "To Watch"


@pytest.mark.asyncio
async def test_rename_watchlist(client, sample_watchlist):
    response = await client.patch(
        f"/api/v1/watchlists/{sample_watchlist.id}",
        json={"name": "Must Watch"},
    )

    assert response.status_code == 200
    assert response.json()["name"] == "Must Watch"


@pytest.mark.asyncio
async def test_rename_watchlist_not_found(client):
    response = await client.patch(
        "/api/v1/watchlists/99999",
        json={"name": "New Name"},
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_watchlist(client, sample_watchlist):
    response = await client.delete(f"/api/v1/watchlists/{sample_watchlist.id}")

    assert response.status_code == 204

    list_response = await client.get("/api/v1/watchlists")
    assert len(list_response.json()["watchlists"]) == 0


@pytest.mark.asyncio
async def test_delete_watchlist_not_found(client):
    response = await client.delete("/api/v1/watchlists/99999")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_add_to_watchlist(client, sample_watchlist, sample_movie):
    response = await client.post(
        f"/api/v1/watchlists/{sample_watchlist.id}/entries",
        json={"movie_id": sample_movie.id},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["watchlist_id"] == sample_watchlist.id
    assert data["movie_id"] == sample_movie.id
    assert data["status"] == "to_watch"
    assert data["watched_at"] is None


@pytest.mark.asyncio
async def test_add_to_watchlist_duplicate(
    client, watchlist_with_entry, sample_watchlist, sample_movie
):
    response = await client.post(
        f"/api/v1/watchlists/{sample_watchlist.id}/entries",
        json={"movie_id": sample_movie.id},
    )

    assert response.status_code == 409
    assert "already in this watchlist" in response.json()["detail"]


@pytest.mark.asyncio
async def test_add_to_watchlist_movie_not_found(client, sample_watchlist):
    response = await client.post(
        f"/api/v1/watchlists/{sample_watchlist.id}/entries",
        json={"movie_id": 99999},
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_add_to_watchlist_not_found(client, sample_movie):
    response = await client.post(
        "/api/v1/watchlists/99999/entries",
        json={"movie_id": sample_movie.id},
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_list_watchlist_entries(client, watchlist_with_entry, sample_watchlist):
    response = await client.get(f"/api/v1/watchlists/{sample_watchlist.id}/entries")

    assert response.status_code == 200
    data = response.json()
    assert len(data["entries"]) == 1
    assert data["entries"][0]["movie"]["title"] == "Fight Club"
    assert data["total"] == 1


@pytest.mark.asyncio
async def test_list_watchlist_entries_empty(client, sample_watchlist):
    response = await client.get(f"/api/v1/watchlists/{sample_watchlist.id}/entries")

    assert response.status_code == 200
    assert response.json()["total"] == 0


@pytest.mark.asyncio
async def test_mark_watched(client, watchlist_with_entry):
    response = await client.patch(
        f"/api/v1/watchlists/1/entries/{watchlist_with_entry.id}",
        json={"status": "watched"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "watched"
    assert data["watched_at"] is not None


@pytest.mark.asyncio
async def test_mark_watched_not_found(client):
    response = await client.patch(
        "/api/v1/watchlists/1/entries/99999",
        json={"status": "watched"},
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_remove_from_watchlist(client, watchlist_with_entry, sample_watchlist):
    response = await client.delete(
        f"/api/v1/watchlists/{sample_watchlist.id}/entries/{watchlist_with_entry.id}"
    )

    assert response.status_code == 204

    list_response = await client.get(
        f"/api/v1/watchlists/{sample_watchlist.id}/entries"
    )
    assert list_response.json()["total"] == 0


@pytest.mark.asyncio
async def test_remove_from_watchlist_not_found(client, sample_watchlist):
    response = await client.delete(
        f"/api/v1/watchlists/{sample_watchlist.id}/entries/99999"
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_remove_from_watchlist_does_not_delete_movie(
    client, watchlist_with_entry, sample_watchlist, sample_movie
):
    await client.delete(
        f"/api/v1/watchlists/{sample_watchlist.id}/entries/{watchlist_with_entry.id}"
    )

    response = await client.get(f"/api/v1/movies/{sample_movie.id}")
    assert response.status_code == 200
    assert response.json()["title"] == "Fight Club"


@pytest.mark.asyncio
async def test_list_entries_filter_by_status(
    client, watchlist_with_entry, sample_watchlist, sample_movie
):
    response = await client.get(
        f"/api/v1/watchlists/{sample_watchlist.id}/entries?status=to_watch"
    )
    assert response.status_code == 200
    assert response.json()["total"] == 1

    response = await client.get(
        f"/api/v1/watchlists/{sample_watchlist.id}/entries?status=watched"
    )
    assert response.status_code == 200
    assert response.json()["total"] == 0
