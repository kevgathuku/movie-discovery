import logging
from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.clients.tmdb_client import TMDBClient
from app.exceptions import (
    ExternalAPIError,
    MovieAlreadyExistsError,
    MovieNotFoundError,
)
from app.models.movie import Movie, MovieSource

logger = logging.getLogger(__name__)


class ImportService:
    def __init__(self, db: AsyncSession, tmdb_client: TMDBClient) -> None:
        self.db = db
        self.tmdb = tmdb_client

    async def import_movie_by_imdb(self, imdb_id: str) -> Movie:
        stmt = select(Movie).where(Movie.imdb_id == imdb_id)
        result = await self.db.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing:
            raise MovieAlreadyExistsError(existing.tmdb_id)

        try:
            tmdb_data = await self.tmdb.find_by_imdb_id(imdb_id)
        except ExternalAPIError:
            raise

        if not tmdb_data:
            raise MovieNotFoundError(imdb_id)

        tmdb_id = tmdb_data["id"]
        stmt = select(Movie).where(Movie.tmdb_id == tmdb_id)
        result = await self.db.execute(stmt)
        existing_tmdb = result.scalar_one_or_none()

        if existing_tmdb:
            raise MovieAlreadyExistsError(tmdb_id)

        poster_path = tmdb_data.get("poster_path")
        release_date_str = tmdb_data.get("release_date")
        release_date = None
        if release_date_str:
            try:
                release_date = date.fromisoformat(release_date_str)
            except ValueError:
                pass

        movie = Movie(
            tmdb_id=tmdb_id,
            imdb_id=imdb_id,
            title=tmdb_data.get("title", ""),
            synopsis=tmdb_data.get("overview"),
            release_date=release_date,
            rating=tmdb_data.get("vote_average"),
            poster_url=self.tmdb.get_poster_url(poster_path),
            source=MovieSource.sync,
        )

        self.db.add(movie)
        await self.db.flush()

        logger.info("Imported movie: %s (tmdb_id=%d)", movie.title, tmdb_id)
        return movie
