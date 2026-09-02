from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.watchlist import WatchlistStatus
from app.schemas.movie import MovieListResponse


class WatchlistCreate(BaseModel):
    name: str


class WatchlistRename(BaseModel):
    name: str


class WatchlistResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    created_at: datetime


class WatchlistListResponse(BaseModel):
    watchlists: list[WatchlistResponse]


class WatchlistEntryCreate(BaseModel):
    movie_id: int


class WatchlistEntryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    watchlist_id: int
    movie_id: int
    status: WatchlistStatus
    added_at: datetime
    watched_at: datetime | None = None


class WatchlistEntryDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    watchlist_id: int
    movie_id: int
    status: WatchlistStatus
    added_at: datetime
    watched_at: datetime | None = None
    movie: MovieListResponse


class WatchlistEntryUpdate(BaseModel):
    status: WatchlistStatus


class PaginatedWatchlistEntriesResponse(BaseModel):
    entries: list[WatchlistEntryDetailResponse]
    total: int
    page: int
    per_page: int
