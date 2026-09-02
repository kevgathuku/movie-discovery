from sqlalchemy.orm import DeclarativeBase

from app.models.job import Job, JobStatus
from app.models.movie import Movie, MovieSource
from app.models.watchlist import Watchlist, WatchlistEntry, WatchlistStatus


class Base(DeclarativeBase):
    pass


__all__ = [
    "Base",
    "Movie",
    "MovieSource",
    "Watchlist",
    "WatchlistEntry",
    "WatchlistStatus",
    "Job",
    "JobStatus",
]
