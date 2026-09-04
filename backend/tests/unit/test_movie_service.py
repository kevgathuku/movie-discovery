from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.movie import Movie
from app.services.movie_service import MovieService


@pytest.fixture
def mock_db():
    session = AsyncMock(spec=AsyncSession)
    return session


@pytest.mark.asyncio
async def test_list_movies(mock_db):
    mock_movie = MagicMock(spec=Movie)
    mock_movie.id = 1
    mock_movie.title = "Fight Club"

    repo = AsyncMock()
    repo.list_movies.return_value = ([mock_movie], 1)

    with patch(
        "app.services.movie_service.MovieRepository", return_value=repo
    ):
        service = MovieService(mock_db)
        movies, total = await service.list_movies(page=1, per_page=20)

        assert len(movies) == 1
        assert movies[0].title == "Fight Club"
        assert total == 1
        repo.list_movies.assert_called_once_with(page=1, per_page=20)


@pytest.mark.asyncio
async def test_list_movies_empty(mock_db):
    repo = AsyncMock()
    repo.list_movies.return_value = ([], 0)

    with patch(
        "app.services.movie_service.MovieRepository", return_value=repo
    ):
        service = MovieService(mock_db)
        movies, total = await service.list_movies()

        assert movies == []
        assert total == 0


@pytest.mark.asyncio
async def test_list_movies_pagination(mock_db):
    repo = AsyncMock()
    repo.list_movies.return_value = ([], 50)

    with patch(
        "app.services.movie_service.MovieRepository", return_value=repo
    ):
        service = MovieService(mock_db)
        await service.list_movies(page=3, per_page=10)

        repo.list_movies.assert_called_once_with(page=3, per_page=10)


@pytest.mark.asyncio
async def test_get_movie_detail(mock_db):
    mock_movie = MagicMock(spec=Movie)
    mock_movie.id = 1

    repo = AsyncMock()
    repo.get_by_id.return_value = mock_movie

    with patch(
        "app.services.movie_service.MovieRepository", return_value=repo
    ):
        service = MovieService(mock_db)
        result = await service.get_movie_detail(1)

        assert result == mock_movie
        repo.get_by_id.assert_called_once_with(1)


@pytest.mark.asyncio
async def test_get_movie_detail_not_found(mock_db):
    repo = AsyncMock()
    repo.get_by_id.return_value = None

    with patch(
        "app.services.movie_service.MovieRepository", return_value=repo
    ):
        service = MovieService(mock_db)
        result = await service.get_movie_detail(999)

        assert result is None


@pytest.mark.asyncio
async def test_delete_movie(mock_db):
    mock_movie = MagicMock(spec=Movie)
    mock_movie.id = 1

    repo = AsyncMock()
    repo.get_by_id.return_value = mock_movie

    with patch(
        "app.services.movie_service.MovieRepository", return_value=repo
    ):
        service = MovieService(mock_db)
        await service.delete_movie(1)

        repo.get_by_id.assert_called_once_with(1)
        repo.delete.assert_called_once_with(mock_movie)


@pytest.mark.asyncio
async def test_delete_movie_not_found(mock_db):
    from app.exceptions import MovieNotFoundError

    repo = AsyncMock()
    repo.get_by_id.return_value = None

    with patch(
        "app.services.movie_service.MovieRepository", return_value=repo
    ):
        service = MovieService(mock_db)
        with pytest.raises(MovieNotFoundError):
            await service.delete_movie(999)

        repo.delete.assert_not_called()
