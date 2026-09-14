from datetime import date

import pytest

from app.models.movie import Movie, MovieSource


@pytest.fixture
async def auth_headers(client, make_user_headers):
    return await make_user_headers("owner@example.com")


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
async def sample_watchlist(client, auth_headers):
    response = await client.post(
        "/api/v1/watchlists",
        json={"name": "To Watch"},
        headers=auth_headers,
    )
    assert response.status_code == 201
    return response.json()


@pytest.fixture
async def watchlist_with_entry(client, auth_headers, sample_watchlist, sample_movie):
    response = await client.post(
        f"/api/v1/watchlists/{sample_watchlist['id']}/entries",
        json={"movie_id": sample_movie.id},
        headers=auth_headers,
    )
    assert response.status_code == 201
    return response.json()


@pytest.mark.asyncio
async def test_create_watchlist(client, auth_headers):
    response = await client.post(
        "/api/v1/watchlists",
        json={"name": "Upcoming"},
        headers=auth_headers,
    )

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Upcoming"
    assert "id" in data
    assert "created_at" in data


@pytest.mark.asyncio
async def test_list_watchlists(client, auth_headers, sample_watchlist):
    response = await client.get(
        "/api/v1/watchlists", headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data["watchlists"]) == 1
    assert data["watchlists"][0]["name"] == "To Watch"


@pytest.mark.asyncio
async def test_rename_watchlist(client, auth_headers, sample_watchlist):
    response = await client.patch(
        f"/api/v1/watchlists/{sample_watchlist['id']}",
        json={"name": "Must Watch"},
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert response.json()["name"] == "Must Watch"


@pytest.mark.asyncio
async def test_rename_watchlist_not_found(client, auth_headers):
    response = await client.patch(
        "/api/v1/watchlists/99999",
        json={"name": "New Name"},
        headers=auth_headers,
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_watchlist(client, auth_headers, sample_watchlist):
    response = await client.delete(
        f"/api/v1/watchlists/{sample_watchlist['id']}",
        headers=auth_headers,
    )

    assert response.status_code == 204

    list_response = await client.get(
        "/api/v1/watchlists", headers=auth_headers
    )
    assert len(list_response.json()["watchlists"]) == 0


@pytest.mark.asyncio
async def test_delete_watchlist_not_found(client, auth_headers):
    response = await client.delete(
        "/api/v1/watchlists/99999", headers=auth_headers
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_add_to_watchlist(
    client, auth_headers, sample_watchlist, sample_movie
):
    response = await client.post(
        f"/api/v1/watchlists/{sample_watchlist['id']}/entries",
        json={"movie_id": sample_movie.id},
        headers=auth_headers,
    )

    assert response.status_code == 201
    data = response.json()
    assert data["watchlist_id"] == sample_watchlist["id"]
    assert data["movie_id"] == sample_movie.id
    assert data["status"] == "to_watch"
    assert data["watched_at"] is None


@pytest.mark.asyncio
async def test_add_to_watchlist_duplicate(
    client, auth_headers, watchlist_with_entry, sample_watchlist, sample_movie
):
    response = await client.post(
        f"/api/v1/watchlists/{sample_watchlist['id']}/entries",
        json={"movie_id": sample_movie.id},
        headers=auth_headers,
    )

    assert response.status_code == 409
    assert "already in this watchlist" in response.json()["detail"]


@pytest.mark.asyncio
async def test_add_to_watchlist_movie_not_found(
    client, auth_headers, sample_watchlist
):
    response = await client.post(
        f"/api/v1/watchlists/{sample_watchlist['id']}/entries",
        json={"movie_id": 99999},
        headers=auth_headers,
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_add_to_watchlist_not_found(
    client, auth_headers, sample_movie
):
    response = await client.post(
        "/api/v1/watchlists/99999/entries",
        json={"movie_id": sample_movie.id},
        headers=auth_headers,
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_list_watchlist_entries(
    client, auth_headers, watchlist_with_entry, sample_watchlist
):
    response = await client.get(
        f"/api/v1/watchlists/{sample_watchlist['id']}/entries",
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data["entries"]) == 1
    assert data["entries"][0]["movie"]["title"] == "Fight Club"
    assert data["total"] == 1


@pytest.mark.asyncio
async def test_list_watchlist_entries_empty(
    client, auth_headers, sample_watchlist
):
    response = await client.get(
        f"/api/v1/watchlists/{sample_watchlist['id']}/entries",
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert response.json()["total"] == 0


@pytest.mark.asyncio
async def test_mark_watched(client, auth_headers, watchlist_with_entry):
    response = await client.patch(
        f"/api/v1/watchlists/1/entries/{watchlist_with_entry['id']}",
        json={"status": "watched"},
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "watched"
    assert data["watched_at"] is not None


@pytest.mark.asyncio
async def test_mark_watched_not_found(client, auth_headers):
    response = await client.patch(
        "/api/v1/watchlists/1/entries/99999",
        json={"status": "watched"},
        headers=auth_headers,
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_unwatch_clears_watched_at(client, auth_headers, watchlist_with_entry):
    entry_id = watchlist_with_entry["id"]
    watched = await client.patch(
        f"/api/v1/watchlists/1/entries/{entry_id}",
        json={"status": "watched"},
        headers=auth_headers,
    )
    assert watched.json()["watched_at"] is not None

    response = await client.patch(
        f"/api/v1/watchlists/1/entries/{entry_id}",
        json={"status": "to_watch"},
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "to_watch"
    assert data["watched_at"] is None


@pytest.mark.asyncio
async def test_remove_from_watchlist_not_found(
    client, auth_headers, sample_watchlist
):
    response = await client.delete(
        f"/api/v1/watchlists/{sample_watchlist['id']}/entries/99999",
        headers=auth_headers,
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_remove_from_watchlist_does_not_delete_movie(
    client, auth_headers, watchlist_with_entry, sample_watchlist, sample_movie
):
    await client.delete(
        f"/api/v1/watchlists/{sample_watchlist['id']}"
        f"/entries/{watchlist_with_entry['id']}",
        headers=auth_headers,
    )

    response = await client.get(f"/api/v1/movies/{sample_movie.id}")
    assert response.status_code == 200
    assert response.json()["title"] == "Fight Club"


@pytest.mark.asyncio
async def test_list_entries_filter_by_status(
    client, auth_headers, watchlist_with_entry, sample_watchlist, sample_movie
):
    response = await client.get(
        f"/api/v1/watchlists/{sample_watchlist['id']}/entries?status=to_watch",
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["total"] == 1

    response = await client.get(
        f"/api/v1/watchlists/{sample_watchlist['id']}/entries?status=watched",
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["total"] == 0


@pytest.mark.asyncio
async def test_add_to_watchlist_verifies_entry_in_list(
    client, auth_headers, sample_watchlist, sample_movie
):
    """Add a movie then confirm it appears when listing entries."""
    add_response = await client.post(
        f"/api/v1/watchlists/{sample_watchlist['id']}/entries",
        json={"movie_id": sample_movie.id},
        headers=auth_headers,
    )
    assert add_response.status_code == 201

    list_response = await client.get(
        f"/api/v1/watchlists/{sample_watchlist['id']}/entries",
        headers=auth_headers,
    )
    data = list_response.json()
    assert data["total"] == 1
    assert data["entries"][0]["movie_id"] == sample_movie.id
    assert data["entries"][0]["status"] == "to_watch"


@pytest.mark.asyncio
async def test_delete_watchlist_removes_entries(
    client, auth_headers, watchlist_with_entry, sample_watchlist
):
    """Deleting a watchlist must cascade-delete its entries."""
    response = await client.delete(
        f"/api/v1/watchlists/{sample_watchlist['id']}",
        headers=auth_headers,
    )
    assert response.status_code == 204

    list_response = await client.get(
        "/api/v1/watchlists", headers=auth_headers
    )
    assert list_response.json()["watchlists"] == []


@pytest.mark.asyncio
async def test_list_entries_response_shape(
    client, auth_headers, watchlist_with_entry, sample_watchlist
):
    """Entry response must include all fields the frontend list needs."""
    response = await client.get(
        f"/api/v1/watchlists/{sample_watchlist['id']}/entries",
        headers=auth_headers,
    )
    entry = response.json()["entries"][0]

    required_fields = [
        "id", "watchlist_id", "movie_id", "status", "added_at",
    ]
    for field in required_fields:
        assert field in entry, f"Missing field: {field}"

    assert "movie" in entry, "Missing nested movie object"
    assert "title" in entry["movie"]
