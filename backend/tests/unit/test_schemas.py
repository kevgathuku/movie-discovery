from app.schemas.job import JobResponse
from app.schemas.movie import MovieDetailResponse, MovieImportRequest, MovieListResponse
from app.schemas.watchlist import (
    WatchlistCreate,
    WatchlistEntryCreate,
    WatchlistEntryResponse,
    WatchlistResponse,
)


def test_movie_list_response_schema():
    data = {
        "id": 1,
        "tmdb_id": 550,
        "imdb_id": "tt0137566",
        "title": "Fight Club",
        "release_date": "1999-10-15",
        "rating": 8.4,
        "poster_url": "https://image.tmdb.org/t/p/w500/poster.jpg",
    }
    response = MovieListResponse(**data)
    assert response.id == 1
    assert response.tmdb_id == 550
    assert response.title == "Fight Club"


def test_movie_detail_response_schema():
    data = {
        "id": 1,
        "tmdb_id": 550,
        "imdb_id": "tt0137566",
        "title": "Fight Club",
        "release_date": "1999-10-15",
        "synopsis": "An insomniac office worker...",
        "genres": ["Drama", "Thriller"],
        "rating": 8.4,
        "poster_url": "https://image.tmdb.org/t/p/w500/poster.jpg",
        "created_at": "2026-09-02T10:00:00Z",
        "updated_at": "2026-09-02T10:00:00Z",
    }
    response = MovieDetailResponse(**data)
    assert response.synopsis == "An insomniac office worker..."
    assert response.genres == ["Drama", "Thriller"]


def test_movie_import_request_schema():
    request = MovieImportRequest(imdb_id="tt0137566")
    assert request.imdb_id == "tt0137566"


def test_watchlist_response_schema():
    data = {
        "id": 1,
        "name": "To Watch",
        "created_at": "2026-09-02T10:00:00Z",
    }
    response = WatchlistResponse(**data)
    assert response.name == "To Watch"


def test_watchlist_create_request_schema():
    request = WatchlistCreate(name="Upcoming")
    assert request.name == "Upcoming"


def test_watchlist_entry_response_schema():
    data = {
        "id": 1,
        "watchlist_id": 1,
        "movie_id": 1,
        "status": "to_watch",
        "added_at": "2026-09-02T10:00:00Z",
        "watched_at": None,
    }
    response = WatchlistEntryResponse(**data)
    assert response.watchlist_id == 1
    assert response.status == "to_watch"


def test_watchlist_entry_create_request_schema():
    request = WatchlistEntryCreate(movie_id=1)
    assert request.movie_id == 1


def test_job_response_schema():
    data = {
        "id": "Xb3nK9",
        "job_type": "sync_trending",
        "status": "completed",
        "progress": 100,
        "created_at": "2026-09-02T10:00:00Z",
        "started_at": "2026-09-02T10:00:01Z",
        "completed_at": "2026-09-02T10:02:30Z",
        "error_info": None,
    }
    response = JobResponse(**data)
    assert response.id == "Xb3nK9"
    assert response.status == "completed"
