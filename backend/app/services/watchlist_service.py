import logging
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.exceptions import (
    MovieNotFoundError,
    WatchlistDuplicateError,
    WatchlistEntryNotFoundError,
    WatchlistNotFoundError,
)
from app.models.movie import Movie
from app.models.watchlist import Watchlist, WatchlistEntry, WatchlistStatus
from app.repositories.movie_repo import MovieRepository

logger = logging.getLogger(__name__)


class WatchlistService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.movie_repo = MovieRepository(db)

    async def create_watchlist(self, name: str) -> Watchlist:
        watchlist = Watchlist(name=name)
        self.db.add(watchlist)
        await self.db.flush()
        logger.info("Created watchlist: %s", name)
        return watchlist

    async def list_watchlists(self) -> list[Watchlist]:
        result = await self.db.execute(select(Watchlist))
        return list(result.scalars().all())

    async def get_watchlist(self, watchlist_id: int) -> Watchlist:
        result = await self.db.execute(
            select(Watchlist).where(Watchlist.id == watchlist_id)
        )
        watchlist = result.scalar_one_or_none()
        if not watchlist:
            raise WatchlistNotFoundError(watchlist_id)
        return watchlist

    async def rename_watchlist(self, watchlist_id: int, name: str) -> Watchlist:
        watchlist = await self.get_watchlist(watchlist_id)
        watchlist.name = name
        await self.db.flush()
        logger.info("Renamed watchlist %d to %s", watchlist_id, name)
        return watchlist

    async def delete_watchlist(self, watchlist_id: int) -> None:
        watchlist = await self.get_watchlist(watchlist_id)
        await self.db.delete(watchlist)
        await self.db.flush()
        logger.info("Deleted watchlist %d", watchlist_id)

    async def add_to_watchlist(
        self, watchlist_id: int, movie_id: int
    ) -> WatchlistEntry:
        await self.get_watchlist(watchlist_id)

        movie = await self.movie_repo.get_by_id(movie_id)
        if not movie:
            raise MovieNotFoundError(movie_id)

        stmt = select(WatchlistEntry).where(
            WatchlistEntry.watchlist_id == watchlist_id,
            WatchlistEntry.movie_id == movie_id,
        )
        result = await self.db.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing:
            raise WatchlistDuplicateError(watchlist_id, movie_id)

        entry = WatchlistEntry(
            watchlist_id=watchlist_id,
            movie_id=movie_id,
            status=WatchlistStatus.to_watch,
        )
        self.db.add(entry)
        await self.db.flush()
        logger.info("Added movie %d to watchlist %d", movie_id, watchlist_id)
        return entry

    async def list_watchlist_entries(
        self,
        watchlist_id: int,
        status: WatchlistStatus | None = None,
        sort: str = "added_at",
        order: str = "desc",
        page: int = 1,
        per_page: int = 20,
    ) -> tuple[list[WatchlistEntry], int]:
        await self.get_watchlist(watchlist_id)

        query = select(WatchlistEntry).where(
            WatchlistEntry.watchlist_id == watchlist_id
        )

        if status:
            query = query.where(WatchlistEntry.status == status)

        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar() or 0

        sort_column = {
            "added_at": WatchlistEntry.added_at,
            "status": WatchlistEntry.status,
        }.get(sort, WatchlistEntry.added_at)

        if order == "asc":
            query = query.order_by(sort_column.asc())
        else:
            query = query.order_by(sort_column.desc())

        query = query.offset((page - 1) * per_page).limit(per_page)
        query = query.options(selectinload(WatchlistEntry.movie))

        result = await self.db.execute(query)
        entries = list(result.scalars().all())

        return entries, total

    async def mark_watched(self, entry_id: int) -> WatchlistEntry:
        result = await self.db.execute(
            select(WatchlistEntry).where(WatchlistEntry.id == entry_id)
        )
        entry = result.scalar_one_or_none()
        if not entry:
            raise WatchlistEntryNotFoundError(entry_id)

        entry.status = WatchlistStatus.watched
        entry.watched_at = datetime.now(UTC)
        await self.db.flush()
        logger.info("Marked entry %d as watched", entry_id)
        return entry

    async def remove_from_watchlist(self, entry_id: int) -> None:
        result = await self.db.execute(
            select(WatchlistEntry).where(WatchlistEntry.id == entry_id)
        )
        entry = result.scalar_one_or_none()
        if not entry:
            raise WatchlistEntryNotFoundError(entry_id)

        await self.db.delete(entry)
        await self.db.flush()
        logger.info("Removed entry %d from watchlist", entry_id)
