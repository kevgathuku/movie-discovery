from sqlalchemy.ext.asyncio import AsyncSession

from app.models.movie import Movie
from app.repositories.movie_repo import MovieRepository


class MovieService:
    def __init__(self, session: AsyncSession) -> None:
        self.repo = MovieRepository(session)

    async def list_movies(
        self, page: int = 1, per_page: int = 20
    ) -> tuple[list[Movie], int]:
        return await self.repo.list_movies(page=page, per_page=per_page)

    async def get_movie_detail(self, movie_id: int) -> Movie | None:
        return await self.repo.get_by_id(movie_id)

    async def delete_movie(self, movie_id: int) -> None:
        movie = await self.repo.get_by_id(movie_id)
        if not movie:
            from app.exceptions import MovieNotFoundError

            raise MovieNotFoundError(movie_id)
        await self.repo.delete(movie)
