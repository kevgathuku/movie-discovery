from app.schemas.job import JobResponse
from app.schemas.movie import (
    MovieBase,
    MovieDetailResponse,
    MovieImportRequest,
    MovieListResponse,
    PaginatedMovieResponse,
)
from app.schemas.watchlist import (
    PaginatedWatchlistEntryResponse,
    WatchlistCreateRequest,
    WatchlistEntryCreateRequest,
    WatchlistEntryResponse,
    WatchlistEntryUpdateRequest,
    WatchlistEntryWithMovieResponse,
    WatchlistResponse,
    WatchlistUpdateRequest,
)

__all__ = [
    "MovieBase",
    "MovieDetailResponse",
    "MovieImportRequest",
    "MovieListResponse",
    "PaginatedMovieResponse",
    "WatchlistCreateRequest",
    "WatchlistEntryCreateRequest",
    "WatchlistEntryResponse",
    "WatchlistEntryUpdateRequest",
    "WatchlistEntryWithMovieResponse",
    "WatchlistResponse",
    "WatchlistUpdateRequest",
    "PaginatedWatchlistEntryResponse",
    "JobResponse",
]
