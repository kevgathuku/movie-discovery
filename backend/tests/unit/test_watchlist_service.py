from unittest.mock import AsyncMock, MagicMock

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
def mock_db():
    session = AsyncMock(spec=AsyncSession)
    return session


def _mock_scalar_result(value):
    result = MagicMock()
    result.scalar_one_or_none.return_value = value
    return result


def _mock_scalars_result(values):
    result = MagicMock()
    result.scalars.return_value.all.return_value = values
    return result


# --- create_watchlist ---


@pytest.mark.asyncio
async def test_create_watchlist(mock_db):
    service = WatchlistService(mock_db)
    result = await service.create_watchlist("To Watch")

    assert result.name == "To Watch"
    mock_db.add.assert_called_once()
    mock_db.flush.assert_called_once()


# --- list_watchlists ---


@pytest.mark.asyncio
async def test_list_watchlists(mock_db):
    mock_watchlist = MagicMock(spec=Watchlist)
    mock_db.execute.return_value = _mock_scalars_result([mock_watchlist])

    service = WatchlistService(mock_db)
    result = await service.list_watchlists()

    assert len(result) == 1
    assert result[0] == mock_watchlist


@pytest.mark.asyncio
async def test_list_watchlists_empty(mock_db):
    mock_db.execute.return_value = _mock_scalars_result([])

    service = WatchlistService(mock_db)
    result = await service.list_watchlists()

    assert result == []


# --- get_watchlist ---


@pytest.mark.asyncio
async def test_get_watchlist(mock_db):
    mock_watchlist = MagicMock(spec=Watchlist)
    mock_db.execute.return_value = _mock_scalar_result(mock_watchlist)

    service = WatchlistService(mock_db)
    result = await service.get_watchlist(1)

    assert result == mock_watchlist


@pytest.mark.asyncio
async def test_get_watchlist_not_found(mock_db):
    mock_db.execute.return_value = _mock_scalar_result(None)

    service = WatchlistService(mock_db)
    with pytest.raises(WatchlistNotFoundError):
        await service.get_watchlist(999)


# --- rename_watchlist ---


@pytest.mark.asyncio
async def test_rename_watchlist(mock_db):
    mock_watchlist = MagicMock(spec=Watchlist)
    mock_watchlist.name = "Old Name"
    mock_db.execute.return_value = _mock_scalar_result(mock_watchlist)

    service = WatchlistService(mock_db)
    result = await service.rename_watchlist(1, "New Name")

    assert result.name == "New Name"
    mock_db.flush.assert_called()


@pytest.mark.asyncio
async def test_rename_watchlist_not_found(mock_db):
    mock_db.execute.return_value = _mock_scalar_result(None)

    service = WatchlistService(mock_db)
    with pytest.raises(WatchlistNotFoundError):
        await service.rename_watchlist(999, "New Name")


# --- delete_watchlist ---


@pytest.mark.asyncio
async def test_delete_watchlist(mock_db):
    mock_watchlist = MagicMock(spec=Watchlist)
    mock_db.execute.return_value = _mock_scalar_result(mock_watchlist)

    service = WatchlistService(mock_db)
    await service.delete_watchlist(1)

    mock_db.delete.assert_called_once_with(mock_watchlist)
    mock_db.flush.assert_called()


@pytest.mark.asyncio
async def test_delete_watchlist_not_found(mock_db):
    mock_db.execute.return_value = _mock_scalar_result(None)

    service = WatchlistService(mock_db)
    with pytest.raises(WatchlistNotFoundError):
        await service.delete_watchlist(999)


# --- add_to_watchlist ---


@pytest.mark.asyncio
async def test_add_to_watchlist(mock_db):
    mock_watchlist = MagicMock(spec=Watchlist)
    mock_movie = MagicMock(spec=Movie)
    mock_movie.id = 100

    watchlist_result = _mock_scalar_result(mock_watchlist)
    movie_result = _mock_scalar_result(mock_movie)
    duplicate_result = _mock_scalar_result(None)

    mock_db.execute.side_effect = [watchlist_result, movie_result, duplicate_result]

    service = WatchlistService(mock_db)
    result = await service.add_to_watchlist(watchlist_id=1, movie_id=100)

    assert result.watchlist_id == 1
    assert result.movie_id == 100
    assert result.status == WatchlistStatus.to_watch
    mock_db.add.assert_called_once()
    mock_db.flush.assert_called()


@pytest.mark.asyncio
async def test_add_to_watchlist_watchlist_not_found(mock_db):
    mock_db.execute.return_value = _mock_scalar_result(None)

    service = WatchlistService(mock_db)
    with pytest.raises(WatchlistNotFoundError):
        await service.add_to_watchlist(watchlist_id=999, movie_id=100)


@pytest.mark.asyncio
async def test_add_to_watchlist_movie_not_found(mock_db):
    mock_watchlist = MagicMock(spec=Watchlist)
    watchlist_result = _mock_scalar_result(mock_watchlist)
    movie_result = _mock_scalar_result(None)

    mock_db.execute.side_effect = [watchlist_result, movie_result]

    service = WatchlistService(mock_db)
    with pytest.raises(MovieNotFoundError):
        await service.add_to_watchlist(watchlist_id=1, movie_id=999)


@pytest.mark.asyncio
async def test_add_to_watchlist_duplicate(mock_db):
    mock_watchlist = MagicMock(spec=Watchlist)
    mock_movie = MagicMock(spec=Movie)
    mock_entry = MagicMock(spec=WatchlistEntry)

    watchlist_result = _mock_scalar_result(mock_watchlist)
    movie_result = _mock_scalar_result(mock_movie)
    duplicate_result = _mock_scalar_result(mock_entry)

    mock_db.execute.side_effect = [watchlist_result, movie_result, duplicate_result]

    service = WatchlistService(mock_db)
    with pytest.raises(WatchlistDuplicateError):
        await service.add_to_watchlist(watchlist_id=1, movie_id=100)


# --- list_watchlist_entries ---


@pytest.mark.asyncio
async def test_list_watchlist_entries(mock_db):
    mock_watchlist = MagicMock(spec=Watchlist)
    mock_entry = MagicMock(spec=WatchlistEntry)

    watchlist_result = _mock_scalar_result(mock_watchlist)
    count_result = MagicMock()
    count_result.scalar.return_value = 1
    entries_result = _mock_scalars_result([mock_entry])

    mock_db.execute.side_effect = [watchlist_result, count_result, entries_result]

    service = WatchlistService(mock_db)
    entries, total = await service.list_watchlist_entries(watchlist_id=1)

    assert len(entries) == 1
    assert total == 1


@pytest.mark.asyncio
async def test_list_watchlist_entries_with_status_filter(mock_db):
    mock_watchlist = MagicMock(spec=Watchlist)
    mock_entry = MagicMock(spec=WatchlistEntry)

    watchlist_result = _mock_scalar_result(mock_watchlist)
    count_result = MagicMock()
    count_result.scalar.return_value = 1
    entries_result = _mock_scalars_result([mock_entry])

    mock_db.execute.side_effect = [watchlist_result, count_result, entries_result]

    service = WatchlistService(mock_db)
    entries, total = await service.list_watchlist_entries(
        watchlist_id=1, status=WatchlistStatus.watched
    )

    assert len(entries) == 1
    assert total == 1


@pytest.mark.asyncio
async def test_list_watchlist_entries_empty(mock_db):
    mock_watchlist = MagicMock(spec=Watchlist)

    watchlist_result = _mock_scalar_result(mock_watchlist)
    count_result = MagicMock()
    count_result.scalar.return_value = 0
    entries_result = _mock_scalars_result([])

    mock_db.execute.side_effect = [watchlist_result, count_result, entries_result]

    service = WatchlistService(mock_db)
    entries, total = await service.list_watchlist_entries(watchlist_id=1)

    assert entries == []
    assert total == 0


@pytest.mark.asyncio
async def test_list_watchlist_entries_watchlist_not_found(mock_db):
    mock_db.execute.return_value = _mock_scalar_result(None)

    service = WatchlistService(mock_db)
    with pytest.raises(WatchlistNotFoundError):
        await service.list_watchlist_entries(watchlist_id=999)


# --- mark_watched ---


@pytest.mark.asyncio
async def test_mark_watched(mock_db):
    mock_entry = MagicMock(spec=WatchlistEntry)
    mock_entry.status = WatchlistStatus.to_watch
    mock_entry.watched_at = None
    mock_db.execute.return_value = _mock_scalar_result(mock_entry)

    service = WatchlistService(mock_db)
    result = await service.mark_watched(entry_id=1)

    assert result.status == WatchlistStatus.watched
    assert result.watched_at is not None
    mock_db.flush.assert_called()


@pytest.mark.asyncio
async def test_mark_watched_not_found(mock_db):
    mock_db.execute.return_value = _mock_scalar_result(None)

    service = WatchlistService(mock_db)
    with pytest.raises(WatchlistEntryNotFoundError):
        await service.mark_watched(entry_id=999)


# --- remove_from_watchlist ---


@pytest.mark.asyncio
async def test_remove_from_watchlist(mock_db):
    mock_entry = MagicMock(spec=WatchlistEntry)
    mock_db.execute.return_value = _mock_scalar_result(mock_entry)

    service = WatchlistService(mock_db)
    await service.remove_from_watchlist(entry_id=1)

    mock_db.delete.assert_called_once_with(mock_entry)
    mock_db.flush.assert_called()


@pytest.mark.asyncio
async def test_remove_from_watchlist_not_found(mock_db):
    mock_db.execute.return_value = _mock_scalar_result(None)

    service = WatchlistService(mock_db)
    with pytest.raises(WatchlistEntryNotFoundError):
        await service.remove_from_watchlist(entry_id=999)
