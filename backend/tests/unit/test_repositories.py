from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.movie import Movie
from app.models.watchlist import Watchlist, WatchlistEntry, WatchlistStatus
from app.repositories.movie_repo import MovieRepository
from app.repositories.watchlist_repo import (
    WatchlistEntryRepository,
    WatchlistRepository,
)


@pytest.fixture
def mock_db():
    session = AsyncMock(spec=AsyncSession)
    return session


# --- MovieRepository ---


@pytest.mark.asyncio
async def test_movie_repo_get_by_id(mock_db):
    mock_movie = MagicMock(spec=Movie)
    mock_movie.id = 1
    mock_db.get.return_value = mock_movie

    repo = MovieRepository(mock_db)
    result = await repo.get_by_id(1)

    assert result == mock_movie
    mock_db.get.assert_called_once_with(Movie, 1)


@pytest.mark.asyncio
async def test_movie_repo_get_by_id_not_found(mock_db):
    mock_db.get.return_value = None

    repo = MovieRepository(mock_db)
    result = await repo.get_by_id(999)

    assert result is None


@pytest.mark.asyncio
async def test_movie_repo_get_by_tmdb_id(mock_db):
    mock_movie = MagicMock(spec=Movie)
    mock_movie.tmdb_id = 550
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_movie
    mock_db.execute.return_value = mock_result

    repo = MovieRepository(mock_db)
    result = await repo.get_by_tmdb_id(550)

    assert result == mock_movie


@pytest.mark.asyncio
async def test_movie_repo_get_by_tmdb_id_not_found(mock_db):
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db.execute.return_value = mock_result

    repo = MovieRepository(mock_db)
    result = await repo.get_by_tmdb_id(999)

    assert result is None


@pytest.mark.asyncio
async def test_movie_repo_get_by_imdb_id(mock_db):
    mock_movie = MagicMock(spec=Movie)
    mock_movie.imdb_id = "tt0137566"
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_movie
    mock_db.execute.return_value = mock_result

    repo = MovieRepository(mock_db)
    result = await repo.get_by_imdb_id("tt0137566")

    assert result == mock_movie


@pytest.mark.asyncio
async def test_movie_repo_get_by_imdb_id_not_found(mock_db):
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db.execute.return_value = mock_result

    repo = MovieRepository(mock_db)
    result = await repo.get_by_imdb_id("tt9999999")

    assert result is None


@pytest.mark.asyncio
async def test_movie_repo_search_by_title(mock_db):
    mock_movie = MagicMock(spec=Movie)
    mock_movie.title = "Fight Club"

    count_result = MagicMock()
    count_result.all.return_value = [MagicMock()]

    data_result = MagicMock()
    data_result.scalars.return_value.all.return_value = [mock_movie]

    mock_db.execute.side_effect = [count_result, data_result]

    repo = MovieRepository(mock_db)
    movies, total = await repo.search_by_title("fight")

    assert len(movies) == 1
    assert movies[0].title == "Fight Club"
    assert total == 1


@pytest.mark.asyncio
async def test_movie_repo_search_by_title_no_results(mock_db):
    count_result = MagicMock()
    count_result.all.return_value = []

    data_result = MagicMock()
    data_result.scalars.return_value.all.return_value = []

    mock_db.execute.side_effect = [count_result, data_result]

    repo = MovieRepository(mock_db)
    movies, total = await repo.search_by_title("nonexistent")

    assert movies == []
    assert total == 0


@pytest.mark.asyncio
async def test_movie_repo_list_movies(mock_db):
    mock_movie = MagicMock(spec=Movie)

    count_result = MagicMock()
    count_result.scalar.return_value = 1

    data_result = MagicMock()
    data_result.scalars.return_value.all.return_value = [mock_movie]

    mock_db.execute.side_effect = [count_result, data_result]

    repo = MovieRepository(mock_db)
    movies, total = await repo.list_movies(page=1, per_page=20)

    assert len(movies) == 1
    assert total == 1


@pytest.mark.asyncio
async def test_movie_repo_list_movies_empty(mock_db):
    count_result = MagicMock()
    count_result.scalar.return_value = 0

    data_result = MagicMock()
    data_result.scalars.return_value.all.return_value = []

    mock_db.execute.side_effect = [count_result, data_result]

    repo = MovieRepository(mock_db)
    movies, total = await repo.list_movies()

    assert movies == []
    assert total == 0


@pytest.mark.asyncio
async def test_movie_repo_create(mock_db):
    mock_movie = MagicMock(spec=Movie)

    repo = MovieRepository(mock_db)
    result = await repo.create(mock_movie)

    assert result == mock_movie
    mock_db.add.assert_called_once_with(mock_movie)
    mock_db.flush.assert_called_once()


@pytest.mark.asyncio
async def test_movie_repo_delete(mock_db):
    mock_movie = MagicMock(spec=Movie)

    repo = MovieRepository(mock_db)
    await repo.delete(mock_movie)

    mock_db.delete.assert_called_once_with(mock_movie)
    mock_db.flush.assert_called_once()


# --- WatchlistRepository ---


@pytest.mark.asyncio
async def test_watchlist_repo_list(mock_db):
    mock_watchlist = MagicMock(spec=Watchlist)
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [mock_watchlist]
    mock_db.execute.return_value = mock_result

    repo = WatchlistRepository(mock_db)
    result = await repo.list_watchlists()

    assert len(result) == 1
    assert result[0] == mock_watchlist


@pytest.mark.asyncio
async def test_watchlist_repo_get_by_id(mock_db):
    mock_watchlist = MagicMock(spec=Watchlist)
    mock_db.get.return_value = mock_watchlist

    repo = WatchlistRepository(mock_db)
    result = await repo.get_by_id(1)

    assert result == mock_watchlist
    mock_db.get.assert_called_once_with(Watchlist, 1)


@pytest.mark.asyncio
async def test_watchlist_repo_get_by_id_not_found(mock_db):
    mock_db.get.return_value = None

    repo = WatchlistRepository(mock_db)
    result = await repo.get_by_id(999)

    assert result is None


@pytest.mark.asyncio
async def test_watchlist_repo_create(mock_db):
    repo = WatchlistRepository(mock_db)
    result = await repo.create("To Watch")

    assert result.name == "To Watch"
    mock_db.add.assert_called_once()
    mock_db.flush.assert_called_once()


@pytest.mark.asyncio
async def test_watchlist_repo_update_name(mock_db):
    mock_watchlist = MagicMock(spec=Watchlist)
    mock_watchlist.name = "Old Name"

    repo = WatchlistRepository(mock_db)
    result = await repo.update_name(mock_watchlist, "New Name")

    assert result.name == "New Name"
    mock_db.flush.assert_called_once()


@pytest.mark.asyncio
async def test_watchlist_repo_delete(mock_db):
    mock_watchlist = MagicMock(spec=Watchlist)

    repo = WatchlistRepository(mock_db)
    await repo.delete(mock_watchlist)

    mock_db.delete.assert_called_once_with(mock_watchlist)
    mock_db.flush.assert_called_once()


# --- WatchlistEntryRepository ---


@pytest.mark.asyncio
async def test_watchlist_entry_repo_get_by_id(mock_db):
    mock_entry = MagicMock(spec=WatchlistEntry)
    mock_db.get.return_value = mock_entry

    repo = WatchlistEntryRepository(mock_db)
    result = await repo.get_by_id(1)

    assert result == mock_entry
    mock_db.get.assert_called_once_with(WatchlistEntry, 1)


@pytest.mark.asyncio
async def test_watchlist_entry_repo_get_by_id_not_found(mock_db):
    mock_db.get.return_value = None

    repo = WatchlistEntryRepository(mock_db)
    result = await repo.get_by_id(999)

    assert result is None


@pytest.mark.asyncio
async def test_watchlist_entry_repo_get_by_watchlist_and_movie(mock_db):
    mock_entry = MagicMock(spec=WatchlistEntry)
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_entry
    mock_db.execute.return_value = mock_result

    repo = WatchlistEntryRepository(mock_db)
    result = await repo.get_by_watchlist_and_movie(1, 100)

    assert result == mock_entry


@pytest.mark.asyncio
async def test_watchlist_entry_repo_get_by_watchlist_and_movie_not_found(
    mock_db,
):
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db.execute.return_value = mock_result

    repo = WatchlistEntryRepository(mock_db)
    result = await repo.get_by_watchlist_and_movie(1, 999)

    assert result is None


@pytest.mark.asyncio
async def test_watchlist_entry_repo_list_entries(mock_db):
    mock_entry = MagicMock(spec=WatchlistEntry)

    count_result = MagicMock()
    count_result.scalar.return_value = 1

    data_result = MagicMock()
    data_result.scalars.return_value.all.return_value = [mock_entry]

    mock_db.execute.side_effect = [count_result, data_result]

    repo = WatchlistEntryRepository(mock_db)
    entries, total = await repo.list_entries(watchlist_id=1)

    assert len(entries) == 1
    assert total == 1


@pytest.mark.asyncio
async def test_watchlist_entry_repo_list_entries_with_status_filter(mock_db):
    mock_entry = MagicMock(spec=WatchlistEntry)

    count_result = MagicMock()
    count_result.scalar.return_value = 1

    data_result = MagicMock()
    data_result.scalars.return_value.all.return_value = [mock_entry]

    mock_db.execute.side_effect = [count_result, data_result]

    repo = WatchlistEntryRepository(mock_db)
    entries, total = await repo.list_entries(
        watchlist_id=1, status=WatchlistStatus.watched
    )

    assert len(entries) == 1
    assert total == 1


@pytest.mark.asyncio
async def test_watchlist_entry_repo_create(mock_db):
    repo = WatchlistEntryRepository(mock_db)
    result = await repo.create(watchlist_id=1, movie_id=100)

    assert result.watchlist_id == 1
    assert result.movie_id == 100
    mock_db.add.assert_called_once()
    mock_db.flush.assert_called_once()


@pytest.mark.asyncio
async def test_watchlist_entry_repo_update_status(mock_db):
    mock_entry = MagicMock(spec=WatchlistEntry)
    mock_entry.status = WatchlistStatus.to_watch
    mock_entry.watched_at = None

    repo = WatchlistEntryRepository(mock_db)
    result = await repo.update_status(mock_entry, WatchlistStatus.watched)

    assert result.status == WatchlistStatus.watched
    assert result.watched_at is not None
    mock_db.flush.assert_called_once()


@pytest.mark.asyncio
async def test_watchlist_entry_repo_update_status_stays_to_watch(mock_db):
    mock_entry = MagicMock(spec=WatchlistEntry)
    mock_entry.status = WatchlistStatus.to_watch
    mock_entry.watched_at = None

    repo = WatchlistEntryRepository(mock_db)
    result = await repo.update_status(mock_entry, WatchlistStatus.to_watch)

    assert result.status == WatchlistStatus.to_watch
    assert result.watched_at is None
    mock_db.flush.assert_called_once()


@pytest.mark.asyncio
async def test_watchlist_entry_repo_delete(mock_db):
    mock_entry = MagicMock(spec=WatchlistEntry)

    repo = WatchlistEntryRepository(mock_db)
    await repo.delete(mock_entry)

    mock_db.delete.assert_called_once_with(mock_entry)
    mock_db.flush.assert_called_once()


# --- JobRepository ---


@pytest.mark.asyncio
async def test_job_repo_get_by_id(mock_db):
    from app.models.job import Job

    mock_job = MagicMock(spec=Job)
    mock_db.get.return_value = mock_job

    from app.repositories.job_repo import JobRepository

    repo = JobRepository(mock_db)
    result = await repo.get_by_id("abc123")

    assert result == mock_job
    mock_db.get.assert_called_once_with(Job, "abc123")


@pytest.mark.asyncio
async def test_job_repo_get_by_id_not_found(mock_db):
    mock_db.get.return_value = None

    from app.repositories.job_repo import JobRepository

    repo = JobRepository(mock_db)
    result = await repo.get_by_id("nonexistent")

    assert result is None


@pytest.mark.asyncio
async def test_job_repo_create(mock_db):
    from app.repositories.job_repo import JobRepository

    repo = JobRepository(mock_db)
    job = await repo.create("sync_trending")

    assert job.job_type == "sync_trending"
    assert job.id is not None
    mock_db.add.assert_called_once()
    mock_db.flush.assert_called_once()


@pytest.mark.asyncio
async def test_job_repo_update_status(mock_db):
    from app.models.job import JobStatus

    mock_job = MagicMock()
    mock_job.status = JobStatus.queued
    mock_job.started_at = None
    mock_job.completed_at = None

    from app.repositories.job_repo import JobRepository

    repo = JobRepository(mock_db)
    result = await repo.update_status(mock_job, JobStatus.processing)

    assert result.status == JobStatus.processing
    assert result.started_at is not None
    mock_db.flush.assert_called_once()


@pytest.mark.asyncio
async def test_job_repo_update_status_completed(mock_db):
    from app.models.job import JobStatus

    mock_job = MagicMock()
    mock_job.status = JobStatus.processing
    mock_job.started_at = MagicMock()
    mock_job.completed_at = None

    from app.repositories.job_repo import JobRepository

    repo = JobRepository(mock_db)
    result = await repo.update_status(mock_job, JobStatus.completed, progress=100)

    assert result.status == JobStatus.completed
    assert result.progress == 100
    assert result.completed_at is not None
    mock_db.flush.assert_called_once()


@pytest.mark.asyncio
async def test_job_repo_update_status_failed_with_error(mock_db):
    from app.models.job import JobStatus

    mock_job = MagicMock()
    mock_job.status = JobStatus.processing
    mock_job.started_at = MagicMock()
    mock_job.completed_at = None

    error_info = {"message": "TMDB API timeout"}

    from app.repositories.job_repo import JobRepository

    repo = JobRepository(mock_db)
    result = await repo.update_status(
        mock_job, JobStatus.failed, error_info=error_info
    )

    assert result.status == JobStatus.failed
    assert result.error_info == error_info
    assert result.completed_at is not None
    mock_db.flush.assert_called_once()
