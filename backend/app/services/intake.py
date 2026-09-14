import asyncio
import logging
from datetime import date

from sqlalchemy import Text, cast, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.clients.tmdb_client import TMDBClient
from app.exceptions import MovieAlreadyExistsError, MovieNotFoundError
from app.models.genre import Genre
from app.models.movie import Movie, MovieSource
from app.repositories.movie_repo import MovieRepository

logger = logging.getLogger(__name__)


class IntakeService:
    """Owns every path that brings TMDB data into the catalog.

    Callers express intent (import one, sync popular, backfill one,
    refresh genres, refresh IMDb IDs); TMDB payload shapes never leave
    this module.
    """

    # ponytail: cap so one run's backfill can't stall the scheduled job
    BACKFILL_BATCH_LIMIT = 500

    # ponytail: TMDB sits ~40 req/s; 10/s max keeps 4x headroom. The
    # IMDb-ID job caps rows per run too, so a big backlog drains safely.
    IMDB_SYNC_BATCH_LIMIT = 40
    IMDB_SYNC_MIN_INTERVAL = 0.1

    def __init__(self, db: AsyncSession, tmdb: TMDBClient) -> None:
        self.db = db
        self.tmdb = tmdb
        self.repo = MovieRepository(db)

    async def import_by_imdb(self, imdb_id: str) -> Movie:
        existing = await self.repo.get_by_imdb_id(imdb_id)
        if existing:
            raise MovieAlreadyExistsError(existing.tmdb_id)

        tmdb_data = await self.tmdb.find_by_imdb_id(imdb_id)
        if not tmdb_data:
            raise MovieNotFoundError(imdb_id)

        tmdb_id = tmdb_data["id"]
        if await self.repo.get_by_tmdb_id(tmdb_id):
            raise MovieAlreadyExistsError(tmdb_id)

        genre_map = await self._genre_map()
        movie = Movie(
            tmdb_id=tmdb_id,
            imdb_id=imdb_id,
            title=tmdb_data.get("title", ""),
            synopsis=tmdb_data.get("overview"),
            release_date=self._parse_date(tmdb_data.get("release_date"), tmdb_id),
            genres=self._names_for(tmdb_data.get("genre_ids", []), genre_map),
            rating=tmdb_data.get("vote_average"),
            poster_url=self.tmdb.get_poster_url(tmdb_data.get("poster_path")),
            source=MovieSource.manual,
        )

        self.db.add(movie)
        await self.db.flush()

        logger.info("Imported movie: %s (tmdb_id=%d)", movie.title, tmdb_id)
        return movie

    async def sync_popular(self) -> list[Movie]:
        genre_map = await self._genre_map()
        movies = []
        for item in await self.tmdb.get_popular():
            tmdb_id = item["id"]
            if await self.repo.get_by_tmdb_id(tmdb_id):
                continue

            movie = Movie(
                tmdb_id=tmdb_id,
                title=item.get("title", ""),
                release_date=self._parse_date(item.get("release_date"), tmdb_id),
                synopsis=item.get("overview"),
                genres=self._names_for(item.get("genre_ids", []), genre_map),
                rating=item.get("vote_average"),
                poster_url=self.tmdb.get_poster_url(item.get("poster_path")),
                source=MovieSource.sync,
            )
            await self.repo.create(movie)
            movies.append(movie)

        return movies

    async def backfill_imdb(self, movie: Movie) -> bool:
        """Fill a missing IMDb ID from TMDB. True when the row changed."""
        if movie.imdb_id:
            return False

        details = await self.tmdb.get_movie_details(movie.tmdb_id)
        imdb_id = details.get("external_ids", {}).get("imdb_id")
        if not imdb_id:
            return False

        movie.imdb_id = imdb_id
        await self.db.flush()
        return True

    async def sync_genres(self) -> int:
        """Refresh the genre cache and fill genre-less rows. Returns fills."""
        remote = await self.tmdb.get_genre_map()
        stored = {g.id: g for g in (await self.db.execute(select(Genre))).scalars()}
        for tmdb_id, name in remote.items():
            if tmdb_id in stored:
                stored[tmdb_id].name = name
            else:
                self.db.add(Genre(id=tmdb_id, name=name))
        await self.db.flush()

        # Match SQL NULL and the JSON literal null: legacy rows carry the
        # latter, and `IS NULL` alone misses them.
        result = await self.db.execute(
            select(Movie)
            .where(or_(Movie.genres.is_(None), cast(Movie.genres, Text) == "null"))
            .limit(self.BACKFILL_BATCH_LIMIT)
        )
        filled = 0
        for movie in result.scalars():
            details = await self.tmdb.get_movie_details(movie.tmdb_id)
            names = [g["name"] for g in details.get("genres", [])]
            if not names:
                names = self._names_for(details.get("genre_ids", []), remote)
            movie.genres = names or None
            if names:
                filled += 1
        await self.db.flush()
        return filled

    async def sync_imdb_ids(
        self, limit: int = IMDB_SYNC_BATCH_LIMIT, on_progress=None
    ) -> int:
        """Fill missing IMDb IDs, paced under the TMDB rate limit.

        `on_progress` is an optional async callback taking
        (attempted, total) for the caller to report progress.
        """
        total = (
            await self.db.execute(
                select(func.count())
                .select_from(Movie)
                .where(or_(Movie.imdb_id.is_(None), Movie.imdb_id == ""))
            )
        ).scalar() or 0
        result = await self.db.execute(
            select(Movie)
            .where(or_(Movie.imdb_id.is_(None), Movie.imdb_id == ""))
            .limit(limit)
        )
        filled = 0
        for attempted, movie in enumerate(result.scalars(), 1):
            if await self.backfill_imdb(movie):
                filled += 1
            await asyncio.sleep(self.IMDB_SYNC_MIN_INTERVAL)
            if on_progress is not None:
                await on_progress(attempted, total)
        await self.db.flush()
        return filled

    async def _genre_map(self) -> dict[int, str]:
        result = await self.db.execute(select(Genre))
        return {g.id: g.name for g in result.scalars()}

    def _names_for(
        self, genre_ids: list[int], genre_map: dict[int, str]
    ) -> list[str] | None:
        names = [genre_map[gid] for gid in genre_ids if gid in genre_map]
        return names or None

    def _parse_date(self, raw: str | None, tmdb_id: int) -> date | None:
        if not raw:
            return None
        try:
            return date.fromisoformat(raw)
        except ValueError:
            logger.warning("Bad release_date %r for tmdb_id=%d", raw, tmdb_id)
            return None
