from datetime import UTC

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.watchlist import Watchlist, WatchlistEntry, WatchlistStatus


class WatchlistRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_watchlists(self) -> list[Watchlist]:
        result = await self.session.execute(select(Watchlist))
        return list(result.scalars().all())

    async def get_by_id(self, watchlist_id: int) -> Watchlist | None:
        return await self.session.get(Watchlist, watchlist_id)

    async def create(self, name: str) -> Watchlist:
        watchlist = Watchlist(name=name)
        self.session.add(watchlist)
        await self.session.flush()
        return watchlist

    async def update_name(self, watchlist: Watchlist, name: str) -> Watchlist:
        watchlist.name = name
        await self.session.flush()
        return watchlist

    async def delete(self, watchlist: Watchlist) -> None:
        await self.session.delete(watchlist)
        await self.session.flush()


class WatchlistEntryRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, entry_id: int) -> WatchlistEntry | None:
        return await self.session.get(WatchlistEntry, entry_id)

    async def get_by_watchlist_and_movie(
        self, watchlist_id: int, movie_id: int
    ) -> WatchlistEntry | None:
        result = await self.session.execute(
            select(WatchlistEntry).where(
                WatchlistEntry.watchlist_id == watchlist_id,
                WatchlistEntry.movie_id == movie_id,
            )
        )
        return result.scalar_one_or_none()

    async def list_entries(
        self,
        watchlist_id: int,
        status: WatchlistStatus | None = None,
        sort: str = "added_at",
        order: str = "desc",
        page: int = 1,
        per_page: int = 20,
    ) -> tuple[list[WatchlistEntry], int]:
        query = select(WatchlistEntry).where(
            WatchlistEntry.watchlist_id == watchlist_id
        )

        if status:
            query = query.where(WatchlistEntry.status == status)

        count_query = select(func.count(WatchlistEntry.id)).where(
            WatchlistEntry.watchlist_id == watchlist_id
        )
        if status:
            count_query = count_query.where(WatchlistEntry.status == status)

        count_result = await self.session.execute(count_query)
        total = count_result.scalar() or 0

        sort_column = getattr(WatchlistEntry, sort, WatchlistEntry.added_at)
        if order == "desc":
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())

        query = query.options(selectinload(WatchlistEntry.watchlist))
        query = query.offset((page - 1) * per_page).limit(per_page)

        result = await self.session.execute(query)
        entries = list(result.scalars().all())
        return entries, total

    async def create(
        self, watchlist_id: int, movie_id: int
    ) -> WatchlistEntry:
        entry = WatchlistEntry(watchlist_id=watchlist_id, movie_id=movie_id)
        self.session.add(entry)
        await self.session.flush()
        return entry

    async def update_status(
        self, entry: WatchlistEntry, status: WatchlistStatus
    ) -> WatchlistEntry:
        from datetime import datetime

        entry.status = status
        if status == WatchlistStatus.watched:
            entry.watched_at = datetime.now(UTC)
        await self.session.flush()
        return entry

    async def delete(self, entry: WatchlistEntry) -> None:
        await self.session.delete(entry)
        await self.session.flush()
