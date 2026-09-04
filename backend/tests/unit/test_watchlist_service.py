import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import (
    MovieNotFoundError,
    WatchlistDuplicateError,
    WatchlistEntryNotFoundError,
    WatchlistNotFoundError,
)
from app.models.movie import Movie
from app.models.watchlist import Watchlist, WatchlistEntry, WatchlistStatus
from app.services.watchlist_service import WatchlistService


@pytest.fixture
def mock_db(mocker):
    session = mocker.AsyncMock(spec=AsyncSession)
    return session


def _mock_scalar_result(mocker, value):
    result = mocker.MagicMock()
    result.scalar_one_or_none.return_value = value
    return result


def _mock_scalars_result(mocker, values):
    result = mocker.MagicMock()
    result.scalars.return_value.all.return_value = values
    return result


# --- add_to_watchlist: core business rules ---


@pytest.mark.asyncio
async def test_add_to_watchlist_sets_default_status(mock_db, mocker):
    """Verify new entries default to to_watch and link correct IDs."""
    mock_watchlist = mocker.MagicMock(spec=Watchlist)
    mock_movie = mocker.MagicMock(spec=Movie)
    mock_movie.id = 100

    mock_db.execute.side_effect = [
        _mock_scalar_result(mocker, mock_watchlist),   # get_watchlist
        _mock_scalar_result(mocker, None),             # duplicate check
    ]
    mock_db.get.return_value = mock_movie  # movie_repo.get_by_id

    service = WatchlistService(mock_db)
    result = await service.add_to_watchlist(watchlist_id=1, movie_id=100)

    assert result.watchlist_id == 1
    assert result.movie_id == 100
    assert result.status == WatchlistStatus.to_watch


@pytest.mark.asyncio
async def test_add_to_watchlist_watchlist_not_found(mock_db, mocker):
    mock_db.execute.return_value = _mock_scalar_result(mocker, None)

    service = WatchlistService(mock_db)
    with pytest.raises(WatchlistNotFoundError):
        await service.add_to_watchlist(watchlist_id=999, movie_id=100)


@pytest.mark.asyncio
async def test_add_to_watchlist_movie_not_found(mock_db, mocker):
    mock_db.execute.return_value = _mock_scalar_result(
        mocker, mocker.MagicMock(spec=Watchlist)
    )
    mock_db.get.return_value = None  # movie_repo.get_by_id returns None

    service = WatchlistService(mock_db)
    with pytest.raises(MovieNotFoundError):
        await service.add_to_watchlist(watchlist_id=1, movie_id=999)


@pytest.mark.asyncio
async def test_add_to_watchlist_duplicate_raises(mock_db, mocker):
    """Duplicate movie in same watchlist must raise, not silently succeed."""
    mock_watchlist = mocker.MagicMock(spec=Watchlist)
    mock_movie = mocker.MagicMock(spec=Movie)
    mock_movie.id = 100
    mock_entry = mocker.MagicMock(spec=WatchlistEntry)

    mock_db.execute.side_effect = [
        _mock_scalar_result(mocker, mock_watchlist),  # get_watchlist
        _mock_scalar_result(mocker, mock_entry),     # duplicate check
    ]
    mock_db.get.return_value = mock_movie  # movie_repo.get_by_id

    service = WatchlistService(mock_db)
    with pytest.raises(WatchlistDuplicateError):
        await service.add_to_watchlist(watchlist_id=1, movie_id=100)


# --- mark_watched: timestamp side effect ---


@pytest.mark.asyncio
async def test_mark_watched_sets_timestamp(mock_db, mocker):
    """Verify watched_at is populated when marking as watched."""
    mock_entry = mocker.MagicMock(spec=WatchlistEntry)
    mock_entry.status = WatchlistStatus.to_watch
    mock_entry.watched_at = None
    mock_db.execute.return_value = _mock_scalar_result(mocker, mock_entry)

    service = WatchlistService(mock_db)
    result = await service.mark_watched(entry_id=1)

    assert result.status == WatchlistStatus.watched
    assert result.watched_at is not None


@pytest.mark.asyncio
async def test_mark_watched_not_found(mock_db, mocker):
    mock_db.execute.return_value = _mock_scalar_result(mocker, None)

    service = WatchlistService(mock_db)
    with pytest.raises(WatchlistEntryNotFoundError):
        await service.mark_watched(entry_id=999)


# --- remove_from_watchlist: error path ---


@pytest.mark.asyncio
async def test_remove_from_watchlist_not_found(mock_db, mocker):
    mock_db.execute.return_value = _mock_scalar_result(mocker, None)

    service = WatchlistService(mock_db)
    with pytest.raises(WatchlistEntryNotFoundError):
        await service.remove_from_watchlist(entry_id=999)
