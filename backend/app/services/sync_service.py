import logging
from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

from app.clients.tmdb_client import TMDBClient
from app.exceptions import ExternalAPIError
from app.models.movie import Movie, MovieSource
from app.repositories.movie_repo import MovieRepository

logger = logging.getLogger(__name__)


class SyncService:
    def __init__(self, session: AsyncSession, tmdb_client: TMDBClient) -> None:
        self.repo = MovieRepository(session)
        self.tmdb = tmdb_client

    async def sync_trending(self) -> list[Movie]:
        try:
            data = await self.tmdb._request("GET", "/movie/popular")
            results = data.get("results", [])
        except ExternalAPIError:
            logger.exception("Failed to fetch trending movies from TMDB")
            raise

        movies = []
        for item in results:
            tmdb_id = item["id"]
            existing = await self.repo.get_by_tmdb_id(tmdb_id)
            if existing:
                continue

            raw_date = item.get("release_date")
            parsed_date = date.fromisoformat(raw_date) if raw_date else None

            movie = Movie(
                tmdb_id=tmdb_id,
                title=item.get("title", ""),
                release_date=parsed_date,
                synopsis=item.get("overview"),
                genres=None,
                rating=item.get("vote_average"),
                poster_url=self.tmdb.get_poster_url(item.get("poster_path")),
                source=MovieSource.sync,
            )
            await self.repo.create(movie)
            movies.append(movie)

        return movies
