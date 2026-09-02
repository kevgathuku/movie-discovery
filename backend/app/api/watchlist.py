from fastapi import APIRouter

router = APIRouter(tags=["watchlist"])


@router.get("/watchlists")
async def list_watchlists():
    return {"watchlists": []}


@router.post("/watchlists")
async def create_watchlist():
    return {"detail": "Not implemented yet"}


@router.get("/watchlists/{watchlist_id}")
async def get_watchlist(watchlist_id: int):
    return {"detail": "Not implemented yet"}


@router.patch("/watchlists/{watchlist_id}")
async def update_watchlist(watchlist_id: int):
    return {"detail": "Not implemented yet"}


@router.delete("/watchlists/{watchlist_id}")
async def delete_watchlist(watchlist_id: int):
    return {"detail": "Not implemented yet"}


@router.get("/watchlists/{watchlist_id}/entries")
async def list_watchlist_entries(watchlist_id: int):
    return {"entries": [], "total": 0, "page": 1, "per_page": 20}


@router.post("/watchlists/{watchlist_id}/entries")
async def add_to_watchlist(watchlist_id: int):
    return {"detail": "Not implemented yet"}


@router.patch("/watchlists/{watchlist_id}/entries/{entry_id}")
async def update_watchlist_entry(watchlist_id: int, entry_id: int):
    return {"detail": "Not implemented yet"}


@router.delete("/watchlists/{watchlist_id}/entries/{entry_id}")
async def delete_watchlist_entry(watchlist_id: int, entry_id: int):
    return {"detail": "Not implemented yet"}
