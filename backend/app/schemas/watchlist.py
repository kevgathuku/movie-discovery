from pydantic import BaseModel, ConfigDict


class WatchlistResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    created_at: str


class WatchlistCreateRequest(BaseModel):
    name: str


class WatchlistUpdateRequest(BaseModel):
    name: str


class WatchlistEntryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    watchlist_id: int
    movie_id: int
    status: str
    added_at: str
    watched_at: str | None = None


class WatchlistEntryCreateRequest(BaseModel):
    movie_id: int


class WatchlistEntryUpdateRequest(BaseModel):
    status: str


class WatchlistEntryWithMovieResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    watchlist_id: int
    movie_id: int
    status: str
    added_at: str
    watched_at: str | None = None
    movie: dict | None = None


class PaginatedWatchlistEntryResponse(BaseModel):
    entries: list[WatchlistEntryWithMovieResponse]
    total: int
    page: int
    per_page: int
