from sqlalchemy.ext.asyncio import AsyncSession

from app.models.movie import Movie
from app.repositories.movie_repo import MovieRepository


class SearchService:
    def __init__(self, session: AsyncSession) -> None:
        self.repo = MovieRepository(session)

    async def search_movies(
        self, query: str, page: int = 1, per_page: int = 20
    ) -> tuple[list[Movie], int]:
        return await self.repo.search_by_title(query, page=page, per_page=per_page)
