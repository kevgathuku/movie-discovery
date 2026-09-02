from unittest.mock import AsyncMock, MagicMock

import pytest

from app.dependencies import get_tmdb_client
from app.models.movie import Movie
from sqlalchemy import select


def _mock_tmdb_client(find_return=None, poster_url="https://image.tmdb.org/t/p/w500/poster.jpg"):
    mock = MagicMock()
    mock.find_by_imdb_id = AsyncMock(return_value=find_return)
    mock.get_poster_url = MagicMock(return_value=poster_url)
    return mock


@pytest.mark.asyncio
async def test_import_movie_success(client, db_session):
    tmdb_data = {
        "id": 550,
        "title": "Fight Club",
        "overview": "An insomniac office worker...",
        "release_date": "1999-10-15",
        "vote_average": 8.4,
        "poster_path": "/poster.jpg",
    }
    mock_client = _mock_tmdb_client(find_return=tmdb_data)
    client._transport.app.dependency_overrides[get_tmdb_client] = lambda: mock_client

    response = await client.post(
        "/api/v1/movies/import",
        json={"imdb_id": "tt0137566"},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["tmdb_id"] == 550
    assert data["imdb_id"] == "tt0137566"
    assert data["title"] == "Fight Club"
    assert data["rating"] == 8.4


@pytest.mark.asyncio
async def test_import_movie_invalid_imdb_format(client):
    response = await client.post(
        "/api/v1/movies/import",
        json={"imdb_id": "invalid"},
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_import_movie_not_found(client):
    mock_client = _mock_tmdb_client(find_return=None)
    client._transport.app.dependency_overrides[get_tmdb_client] = lambda: mock_client

    response = await client.post(
        "/api/v1/movies/import",
        json={"imdb_id": "tt9999999"},
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_import_movie_duplicate(client):
    tmdb_data = {
        "id": 550,
        "title": "Fight Club",
        "overview": "An insomniac office worker...",
        "release_date": "1999-10-15",
        "vote_average": 8.4,
        "poster_path": "/poster.jpg",
    }
    mock_client = _mock_tmdb_client(find_return=tmdb_data)
    client._transport.app.dependency_overrides[get_tmdb_client] = lambda: mock_client

    response1 = await client.post(
        "/api/v1/movies/import",
        json={"imdb_id": "tt0137566"},
    )
    assert response1.status_code == 201

    mock_client.find_by_imdb_id = AsyncMock(return_value=tmdb_data)

    response2 = await client.post(
        "/api/v1/movies/import",
        json={"imdb_id": "tt0137566"},
    )
    assert response2.status_code == 409


@pytest.mark.asyncio
async def test_import_movie_tmdb_api_error(client):
    from app.exceptions import ExternalAPIError

    mock_client = MagicMock()
    mock_client.find_by_imdb_id = AsyncMock(
        side_effect=ExternalAPIError("TMDB", "timeout")
    )
    client._transport.app.dependency_overrides[get_tmdb_client] = lambda: mock_client

    response = await client.post(
        "/api/v1/movies/import",
        json={"imdb_id": "tt0137566"},
    )

    assert response.status_code == 502
    assert "TMDB API is currently unavailable" in response.json()["detail"]
