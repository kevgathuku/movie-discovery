from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import ExternalAPIError, MovieAlreadyExistsError, MovieNotFoundError
from app.models.movie import Movie
from app.services.import_service import ImportService


@pytest.fixture
def mock_tmdb():
    client = MagicMock()
    client.find_by_imdb_id = AsyncMock()
    client.get_poster_url = MagicMock(return_value="https://image.tmdb.org/t/p/w500/poster.jpg")
    return client


@pytest.fixture
def mock_db():
    session = AsyncMock(spec=AsyncSession)
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    session.execute.return_value = mock_result
    return session


@pytest.mark.asyncio
async def test_import_movie_by_imdb(mock_db, mock_tmdb):
    mock_tmdb.find_by_imdb_id.return_value = {
        "id": 550,
        "title": "Fight Club",
        "overview": "An insomniac office worker...",
        "release_date": "1999-10-15",
        "vote_average": 8.4,
        "poster_path": "/poster.jpg",
    }

    service = ImportService(mock_db, mock_tmdb)
    movie = await service.import_movie_by_imdb("tt0137566")

    assert movie.tmdb_id == 550
    assert movie.imdb_id == "tt0137566"
    assert movie.title == "Fight Club"
    assert movie.rating == 8.4
    mock_db.add.assert_called_once()
    mock_db.flush.assert_called_once()


@pytest.mark.asyncio
async def test_import_movie_already_exists_by_imdb(mock_db, mock_tmdb):
    existing = MagicMock(spec=Movie)
    existing.tmdb_id = 550
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = existing
    mock_db.execute.return_value = mock_result

    service = ImportService(mock_db, mock_tmdb)
    with pytest.raises(MovieAlreadyExistsError):
        await service.import_movie_by_imdb("tt0137566")

    mock_tmdb.find_by_imdb_id.assert_not_called()


@pytest.mark.asyncio
async def test_import_movie_not_found_on_tmdb(mock_db, mock_tmdb):
    mock_tmdb.find_by_imdb_id.return_value = None

    service = ImportService(mock_db, mock_tmdb)
    with pytest.raises(MovieNotFoundError):
        await service.import_movie_by_imdb("tt9999999")


@pytest.mark.asyncio
async def test_import_movie_tmdb_api_error(mock_db, mock_tmdb):
    mock_tmdb.find_by_imdb_id.side_effect = ExternalAPIError("TMDB", "timeout")

    service = ImportService(mock_db, mock_tmdb)
    with pytest.raises(ExternalAPIError):
        await service.import_movie_by_imdb("tt0137566")
