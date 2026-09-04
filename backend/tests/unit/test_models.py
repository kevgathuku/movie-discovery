from app.models.job import Job, JobStatus
from app.models.movie import Movie, MovieSource
from app.models.watchlist import Watchlist, WatchlistEntry, WatchlistStatus


def test_movie_source_enum():
    assert MovieSource.manual == "manual"
    assert MovieSource.sync == "sync"


def test_watchlist_status_enum():
    assert WatchlistStatus.to_watch == "to_watch"
    assert WatchlistStatus.watched == "watched"


def test_job_status_enum():
    assert JobStatus.queued == "queued"
    assert JobStatus.processing == "processing"
    assert JobStatus.completed == "completed"
    assert JobStatus.failed == "failed"


def test_movie_table_name():
    assert Movie.__tablename__ == "movies"


def test_watchlist_table_name():
    assert Watchlist.__tablename__ == "watchlists"


def test_watchlist_entry_table_name():
    assert WatchlistEntry.__tablename__ == "watchlist_entries"


def test_job_table_name():
    assert Job.__tablename__ == "jobs"
