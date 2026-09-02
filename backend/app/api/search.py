from fastapi import APIRouter

router = APIRouter(tags=["search"])


@router.get("/search")
async def search_movies():
    return {"results": [], "total": 0, "page": 1, "per_page": 20}
