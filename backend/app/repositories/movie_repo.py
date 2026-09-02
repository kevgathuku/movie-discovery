from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.movie import Movie


class MovieRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, movie_id: int) -> Movie | None:
        return await self.session.get(Movie, movie_id)

    async def get_by_tmdb_id(self, tmdb_id: int) -> Movie | None:
        result = await self.session.execute(
            select(Movie).where(Movie.tmdb_id == tmdb_id)
        )
        return result.scalar_one_or_none()

    async def get_by_imdb_id(self, imdb_id: str) -> Movie | None:
        result = await self.session.execute(
            select(Movie).where(Movie.imdb_id == imdb_id)
        )
        return result.scalar_one_or_none()

    async def search_by_title(
        self, query: str, page: int = 1, per_page: int = 20
    ) -> tuple[list[Movie], int]:
        base_query = select(Movie).where(Movie.title.ilike(f"%{query}%"))
        count_result = await self.session.execute(
            select(Movie.id).where(Movie.title.ilike(f"%{query}%"))
        )
        total = len(count_result.all())

        result = await self.session.execute(
            base_query.offset((page - 1) * per_page).limit(per_page)
        )
        movies = list(result.scalars().all())
        return movies, total

    async def list_movies(
        self, page: int = 1, per_page: int = 20
    ) -> tuple[list[Movie], int]:
        from sqlalchemy import func

        count_result = await self.session.execute(select(func.count(Movie.id)))
        total = count_result.scalar() or 0

        result = await self.session.execute(
            select(Movie).order_by(Movie.created_at.desc())
            .offset((page - 1) * per_page)
            .limit(per_page)
        )
        movies = list(result.scalars().all())
        return movies, total

    async def create(self, movie: Movie) -> Movie:
        self.session.add(movie)
        await self.session.flush()
        return movie

    async def delete(self, movie: Movie) -> None:
        await self.session.delete(movie)
        await self.session.flush()
