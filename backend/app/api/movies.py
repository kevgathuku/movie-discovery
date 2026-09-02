from fastapi import APIRouter

router = APIRouter(tags=["movies"])


@router.get("/movies")
async def list_movies():
    return {"movies": [], "total": 0, "page": 1, "per_page": 20}


@router.get("/movies/{movie_id}")
async def get_movie(movie_id: int):
    return {"detail": "Not implemented yet"}


@router.delete("/movies/{movie_id}")
async def delete_movie(movie_id: int):
    return {"detail": "Not implemented yet"}


@router.post("/movies/import")
async def import_movie():
    return {"detail": "Not implemented yet"}
