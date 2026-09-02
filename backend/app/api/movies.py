from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db
from app.schemas.movie import MovieListResponse, PaginatedMovieResponse
from app.services.movie_service import MovieService

router = APIRouter(tags=["movies"])


@router.get("/movies", response_model=PaginatedMovieResponse)
async def list_movies(
    page: int = 1,
    per_page: int = 20,
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> PaginatedMovieResponse:
    service = MovieService(db)
    movies, total = await service.list_movies(page=page, per_page=per_page)
    return PaginatedMovieResponse(
        movies=[MovieListResponse.model_validate(m) for m in movies],
        total=total,
        page=page,
        per_page=per_page,
    )


@router.get("/movies/{movie_id}")
async def get_movie(movie_id: int):
    return {"detail": "Not implemented yet"}


@router.delete("/movies/{movie_id}")
async def delete_movie(movie_id: int):
    return {"detail": "Not implemented yet"}


@router.post("/movies/import")
async def import_movie():
    return {"detail": "Not implemented yet"}
