import re

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.clients.tmdb_client import TMDBClient
from app.dependencies import get_db, get_tmdb_client
from app.exceptions import (
    ExternalAPIError,
    MovieAlreadyExistsError,
    MovieNotFoundError,
)
from app.schemas.movie import (
    MovieDetailResponse,
    MovieImportRequest,
    MovieListResponse,
    PaginatedMovieResponse,
)
from app.services.import_service import ImportService
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


@router.post(
    "/movies/import",
    response_model=MovieDetailResponse,
    status_code=status.HTTP_201_CREATED,
)
async def import_movie(
    request: MovieImportRequest,
    db: AsyncSession = Depends(get_db),
    tmdb_client: TMDBClient = Depends(get_tmdb_client),
):
    imdb_id = request.imdb_id.strip()

    if not re.match(r"^tt\d{7,}$", imdb_id):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid IMDB ID format: {imdb_id}. Must be like tt0137566",
        )

    service = ImportService(db, tmdb_client)
    try:
        movie = await service.import_movie_by_imdb(imdb_id)
        await db.commit()
        return MovieDetailResponse.model_validate(movie)
    except MovieAlreadyExistsError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Movie already exists in local database",
        ) from e
    except MovieNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No movie found for IMDB ID {imdb_id}",
        ) from e
    except ExternalAPIError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="TMDB API is currently unavailable. Please try again later.",
        ) from e
