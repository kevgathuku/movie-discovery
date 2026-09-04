from datetime import date

import pytest

from app.dependencies import get_tmdb_client
from app.models.movie import Movie, MovieSource


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
async def movie_without_imdb(db_session):
    movie = Movie(
        tmdb_id=550,
        title="Fight Club",
        synopsis="An insomniac office worker...",
        release_date=date(1999, 10, 15),
        rating=8.4,
        source=MovieSource.sync,
    )
    db_session.add(movie)
    await db_session.commit()
    return movie


@pytest.mark.asyncio
async def test_get_movie_detail_success(client, sample_movie):
    response = await client.get(f"/api/v1/movies/{sample_movie.id}")

    assert response.status_code == 200
    data = response.json()
    assert data["tmdb_id"] == 550
    assert data["imdb_id"] == "tt0137566"
    assert data["title"] == "Fight Club"
    assert data["synopsis"] == "An insomniac office worker..."
    assert data["rating"] == 8.4
    assert data["poster_url"] == "https://image.tmdb.org/t/p/w500/poster.jpg"
    assert "created_at" in data
    assert "updated_at" in data


@pytest.mark.asyncio
async def test_get_movie_detail_not_found(client):
    response = await client.get("/api/v1/movies/99999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Movie not found"


@pytest.mark.asyncio
async def test_get_movie_detail_includes_genres(client, db_session):
    movie = Movie(
        tmdb_id=550,
        imdb_id="tt0137566",
        title="Fight Club",
        release_date=date(1999, 10, 15),
        genres=["Drama", "Thriller"],
        rating=8.4,
        source=MovieSource.sync,
    )
    db_session.add(movie)
    await db_session.commit()
    await db_session.refresh(movie)

    response = await client.get(f"/api/v1/movies/{movie.id}")

    assert response.status_code == 200
    data = response.json()
    assert data["genres"] == ["Drama", "Thriller"]


@pytest.mark.asyncio
async def test_lazy_enrichment_fetches_imdb_id(client, movie_without_imdb, mocker):
    mock_client = mocker.MagicMock()
    mock_client.get_movie_details = mocker.AsyncMock(return_value={
        "external_ids": {"imdb_id": "tt0137566"}
    })
    client._transport.app.dependency_overrides[get_tmdb_client] = lambda: mock_client

    response = await client.get(f"/api/v1/movies/{movie_without_imdb.id}")

    assert response.status_code == 200
    data = response.json()
    assert data["imdb_id"] == "tt0137566"
    mock_client.get_movie_details.assert_called_once_with(550)


@pytest.mark.asyncio
async def test_lazy_enrichment_skips_when_imdb_id_exists(client, sample_movie, mocker):
    mock_client = mocker.MagicMock()
    mock_client.get_movie_details = mocker.AsyncMock()
    client._transport.app.dependency_overrides[get_tmdb_client] = lambda: mock_client

    response = await client.get(f"/api/v1/movies/{sample_movie.id}")

    assert response.status_code == 200
    assert response.json()["imdb_id"] == "tt0137566"
    mock_client.get_movie_details.assert_not_called()


@pytest.mark.asyncio
async def test_lazy_enrichment_handles_tmdb_failure(client, movie_without_imdb, mocker):
    from app.exceptions import ExternalAPIError

    mock_client = mocker.MagicMock()
    mock_client.get_movie_details = mocker.AsyncMock(
        side_effect=ExternalAPIError("TMDB", "timeout")
    )
    client._transport.app.dependency_overrides[get_tmdb_client] = lambda: mock_client

    response = await client.get(f"/api/v1/movies/{movie_without_imdb.id}")

    assert response.status_code == 200
    assert response.json()["imdb_id"] is None


@pytest.mark.asyncio
async def test_movie_detail_null_genres(client, db_session):
    """Null genres must not cause a serialization error."""
    movie = Movie(
        tmdb_id=550,
        imdb_id="tt0137566",
        title="Fight Club",
        source=MovieSource.sync,
    )
    db_session.add(movie)
    await db_session.commit()
    await db_session.refresh(movie)

    response = await client.get(f"/api/v1/movies/{movie.id}")

    assert response.status_code == 200
    assert response.json()["genres"] is None


@pytest.mark.asyncio
async def test_movie_detail_null_optional_fields(client, db_session):
    """Movie with only required fields must still serialize correctly."""
    movie = Movie(
        tmdb_id=550,
        imdb_id="tt0137566",
        title="Minimal Movie",
        source=MovieSource.sync,
    )
    db_session.add(movie)
    await db_session.commit()
    await db_session.refresh(movie)

    response = await client.get(f"/api/v1/movies/{movie.id}")

    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Minimal Movie"
    assert data["synopsis"] is None
    assert data["release_date"] is None
    assert data["rating"] is None
    assert data["poster_url"] is None
    assert data["genres"] is None


@pytest.mark.asyncio
async def test_movie_detail_response_shape(client, sample_movie):
    """Response must contain all fields the frontend detail page needs."""
    response = await client.get(f"/api/v1/movies/{sample_movie.id}")
    data = response.json()

    required_fields = [
        "id", "tmdb_id", "imdb_id", "title", "release_date",
        "synopsis", "genres", "rating", "poster_url", "created_at", "updated_at",
    ]
    for field in required_fields:
        assert field in data, f"Missing field: {field}"
