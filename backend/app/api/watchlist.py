from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db
from app.exceptions import (
    MovieNotFoundError,
    WatchlistDuplicateError,
    WatchlistEntryNotFoundError,
    WatchlistNotFoundError,
)
from app.models.watchlist import WatchlistStatus
from app.schemas.watchlist import (
    PaginatedWatchlistEntriesResponse,
    WatchlistCreate,
    WatchlistEntryCreate,
    WatchlistEntryDetailResponse,
    WatchlistEntryResponse,
    WatchlistEntryUpdate,
    WatchlistListResponse,
    WatchlistRename,
    WatchlistResponse,
)
from app.services.watchlist_service import WatchlistService

router = APIRouter(tags=["watchlist"])


@router.get("/watchlists", response_model=WatchlistListResponse)
async def list_watchlists(
    db: AsyncSession = Depends(get_db),
):
    service = WatchlistService(db)
    watchlists = await service.list_watchlists()
    return WatchlistListResponse(
        watchlists=[WatchlistResponse.model_validate(w) for w in watchlists]
    )


@router.post(
    "/watchlists",
    response_model=WatchlistResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_watchlist(
    request: WatchlistCreate,
    db: AsyncSession = Depends(get_db),
):
    service = WatchlistService(db)
    watchlist = await service.create_watchlist(name=request.name)
    await db.commit()
    return WatchlistResponse.model_validate(watchlist)


@router.patch("/watchlists/{watchlist_id}", response_model=WatchlistResponse)
async def rename_watchlist(
    watchlist_id: int,
    request: WatchlistRename,
    db: AsyncSession = Depends(get_db),
):
    service = WatchlistService(db)
    try:
        watchlist = await service.rename_watchlist(watchlist_id, name=request.name)
        await db.commit()
        return WatchlistResponse.model_validate(watchlist)
    except WatchlistNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Watchlist not found",
        ) from e


@router.delete("/watchlists/{watchlist_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_watchlist(
    watchlist_id: int,
    db: AsyncSession = Depends(get_db),
):
    service = WatchlistService(db)
    try:
        await service.delete_watchlist(watchlist_id)
        await db.commit()
    except WatchlistNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Watchlist not found",
        ) from e


@router.get(
    "/watchlists/{watchlist_id}/entries",
    response_model=PaginatedWatchlistEntriesResponse,
)
async def list_watchlist_entries(
    watchlist_id: int,
    status_filter: WatchlistStatus | None = Query(None, alias="status"),
    sort: str = "added_at",
    order: str = "desc",
    page: int = 1,
    per_page: int = 20,
    db: AsyncSession = Depends(get_db),
):
    service = WatchlistService(db)
    try:
        entries, total = await service.list_watchlist_entries(
            watchlist_id,
            status=status_filter,
            sort=sort,
            order=order,
            page=page,
            per_page=per_page,
        )
        return PaginatedWatchlistEntriesResponse(
            entries=[
                WatchlistEntryDetailResponse.model_validate(e) for e in entries
            ],
            total=total,
            page=page,
            per_page=per_page,
        )
    except WatchlistNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Watchlist not found",
        ) from e


@router.post(
    "/watchlists/{watchlist_id}/entries",
    response_model=WatchlistEntryResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_to_watchlist(
    watchlist_id: int,
    request: WatchlistEntryCreate,
    db: AsyncSession = Depends(get_db),
):
    service = WatchlistService(db)
    try:
        entry = await service.add_to_watchlist(watchlist_id, request.movie_id)
        await db.commit()
        return WatchlistEntryResponse.model_validate(entry)
    except WatchlistNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Watchlist not found",
        ) from e
    except MovieNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie not found",
        ) from e
    except WatchlistDuplicateError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Movie is already in this watchlist",
        ) from e


@router.patch(
    "/watchlists/{watchlist_id}/entries/{entry_id}",
    response_model=WatchlistEntryResponse,
)
async def update_watchlist_entry(
    watchlist_id: int,
    entry_id: int,
    request: WatchlistEntryUpdate,
    db: AsyncSession = Depends(get_db),
):
    service = WatchlistService(db)
    try:
        entry = await service.mark_watched(entry_id)
        await db.commit()
        return WatchlistEntryResponse.model_validate(entry)
    except WatchlistEntryNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Watchlist entry not found",
        ) from e


@router.delete(
    "/watchlists/{watchlist_id}/entries/{entry_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_watchlist_entry(
    watchlist_id: int,
    entry_id: int,
    db: AsyncSession = Depends(get_db),
):
    service = WatchlistService(db)
    try:
        await service.remove_from_watchlist(entry_id)
        await db.commit()
    except WatchlistEntryNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Watchlist entry not found",
        ) from e
