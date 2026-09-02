from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db
from app.schemas.movie import MovieListResponse, SearchResponse
from app.services.search_service import SearchService

router = APIRouter(tags=["search"])


@router.get("/search", response_model=SearchResponse)
async def search_movies(
    q: str = Query(..., min_length=2),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=50),
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> SearchResponse:
    service = SearchService(db)
    movies, total = await service.search_movies(q, page=page, per_page=per_page)

    suggestion = None
    if total == 0:
        suggestion = "No local results. Import from TMDB by IMDB ID."

    return SearchResponse(
        results=[MovieListResponse.model_validate(m) for m in movies],
        total=total,
        page=page,
        per_page=per_page,
        suggestion=suggestion,
    )
