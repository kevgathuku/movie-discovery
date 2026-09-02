from unittest.mock import AsyncMock, patch

import pytest

from app.models.movie import Movie, MovieSource
from app.services.search_service import SearchService


@pytest.fixture
def mock_session():
    return AsyncMock()


@pytest.fixture
def service(mock_session):
    return SearchService(mock_session)


@pytest.mark.asyncio
async def test_search_movies_returns_results(service):
    movie = Movie(
        id=1,
        tmdb_id=550,
        title="Fight Club",
        source=MovieSource.sync,
    )
    with patch.object(service.repo, "search_by_title", return_value=([movie], 1)):
        movies, total = await service.search_movies("fight")

    assert len(movies) == 1
    assert movies[0].title == "Fight Club"
    assert total == 1


@pytest.mark.asyncio
async def test_search_movies_empty(service):
    with patch.object(service.repo, "search_by_title", return_value=([], 0)):
        movies, total = await service.search_movies("nonexistent")

    assert movies == []
    assert total == 0


@pytest.mark.asyncio
async def test_search_movies_passes_pagination(service):
    with patch.object(service.repo, "search_by_title", return_value=([], 0)) as mock:
        await service.search_movies("test", page=2, per_page=10)

    mock.assert_called_once_with("test", page=2, per_page=10)
