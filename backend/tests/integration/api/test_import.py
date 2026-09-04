import pytest
from sqlalchemy import select

from app.dependencies import get_tmdb_client
from app.models.movie import Movie


def _mock_tmdb_client(
    mocker, find_return=None, poster_url="https://image.tmdb.org/t/p/w500/poster.jpg"
):
    mock = mocker.MagicMock()
    mock.find_by_imdb_id = mocker.AsyncMock(return_value=find_return)
    mock.get_poster_url = mocker.MagicMock(return_value=poster_url)
    return mock


@pytest.mark.asyncio
async def test_import_movie_success(client, db_session, mocker):
    tmdb_data = {
        "id": 550,
        "title": "Fight Club",
        "overview": "An insomniac office worker...",
        "release_date": "1999-10-15",
        "vote_average": 8.4,
        "poster_path": "/poster.jpg",
    }
    mock_client = _mock_tmdb_client(mocker, find_return=tmdb_data)
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
async def test_import_movie_persists_to_database(client, db_session, mocker):
    """Imported movie must be retrievable from the database afterward."""
    tmdb_data = {
        "id": 550,
        "title": "Fight Club",
        "overview": "An insomniac office worker...",
        "release_date": "1999-10-15",
        "vote_average": 8.4,
        "poster_path": "/poster.jpg",
    }
    mock_client = _mock_tmdb_client(mocker, find_return=tmdb_data)
    client._transport.app.dependency_overrides[get_tmdb_client] = lambda: mock_client

    await client.post("/api/v1/movies/import", json={"imdb_id": "tt0137566"})

    result = await db_session.execute(select(Movie).where(Movie.tmdb_id == 550))
    movie = result.scalar_one_or_none()
    assert movie is not None
    assert movie.title == "Fight Club"
    assert movie.imdb_id == "tt0137566"
    assert movie.source.value == "sync"


@pytest.mark.asyncio
async def test_import_movie_response_contains_all_detail_fields(
    client, db_session, mocker
):
    """Response must include all detail fields for the frontend."""
    tmdb_data = {
        "id": 550,
        "title": "Fight Club",
        "overview": "An insomniac office worker...",
        "release_date": "1999-10-15",
        "vote_average": 8.4,
        "poster_path": "/poster.jpg",
    }
    mock_client = _mock_tmdb_client(mocker, find_return=tmdb_data)
    client._transport.app.dependency_overrides[get_tmdb_client] = lambda: mock_client

    response = await client.post(
        "/api/v1/movies/import", json={"imdb_id": "tt0137566"}
    )
    data = response.json()

    required_fields = [
        "id", "tmdb_id", "imdb_id", "title", "release_date",
        "synopsis", "rating", "poster_url", "created_at", "updated_at",
    ]
    for field in required_fields:
        assert field in data, f"Missing field: {field}"


@pytest.mark.asyncio
async def test_import_movie_invalid_imdb_format(client):
    response = await client.post(
        "/api/v1/movies/import",
        json={"imdb_id": "invalid"},
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_import_movie_empty_imdb_id(client):
    """Empty string should be rejected by format validation."""
    response = await client.post(
        "/api/v1/movies/import",
        json={"imdb_id": ""},
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_import_movie_not_found(client, mocker):
    mock_client = _mock_tmdb_client(mocker, find_return=None)
    client._transport.app.dependency_overrides[get_tmdb_client] = lambda: mock_client

    response = await client.post(
        "/api/v1/movies/import",
        json={"imdb_id": "tt9999999"},
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_import_movie_duplicate(client, mocker):
    tmdb_data = {
        "id": 550,
        "title": "Fight Club",
        "overview": "An insomniac office worker...",
        "release_date": "1999-10-15",
        "vote_average": 8.4,
        "poster_path": "/poster.jpg",
    }
    mock_client = _mock_tmdb_client(mocker, find_return=tmdb_data)
    client._transport.app.dependency_overrides[get_tmdb_client] = lambda: mock_client

    response1 = await client.post(
        "/api/v1/movies/import",
        json={"imdb_id": "tt0137566"},
    )
    assert response1.status_code == 201

    mock_client.find_by_imdb_id = mocker.AsyncMock(return_value=tmdb_data)

    response2 = await client.post(
        "/api/v1/movies/import",
        json={"imdb_id": "tt0137566"},
    )
    assert response2.status_code == 409


@pytest.mark.asyncio
async def test_import_movie_tmdb_api_error(client, mocker):
    from app.exceptions import ExternalAPIError

    mock_client = mocker.MagicMock()
    mock_client.find_by_imdb_id = mocker.AsyncMock(
        side_effect=ExternalAPIError("TMDB", "timeout")
    )
    client._transport.app.dependency_overrides[get_tmdb_client] = lambda: mock_client

    response = await client.post(
        "/api/v1/movies/import",
        json={"imdb_id": "tt0137566"},
    )

    assert response.status_code == 502
    assert "TMDB API is currently unavailable" in response.json()["detail"]
