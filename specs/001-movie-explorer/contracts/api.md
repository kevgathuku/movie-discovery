# API Contracts: Movie Explorer

**Date**: 2026-09-02
**Feature**: 001-movie-explorer

All endpoints use JSON request/response bodies. Pydantic schemas validate input and shape output. Database models are NOT exposed directly (Principle XIV).

## Base URL

```
http://localhost:8000/api/v1
```

---

## Movies

### GET /api/v1/movies

List movies from the local database (used for home page discovery and search).

**Query Parameters**:
| Parameter | Type | Default | Notes |
|-----------|------|---------|-------|
| `q` | string | — | Title search (case-insensitive LIKE) |
| `page` | int | 1 | Page number |
| `per_page` | int | 20 | Results per page (max 100) |

**Response 200**:
```json
{
  "movies": [
    {
      "id": 1,
      "tmdb_id": 550,
      "imdb_id": "tt0137566",
      "title": "Fight Club",
      "release_date": "1999-10-15",
      "rating": 8.4,
      "poster_url": "https://image.tmdb.org/t/p/w500/..."
    }
  ],
  "total": 142,
  "page": 1,
  "per_page": 20
}
```

---

### GET /api/v1/movies/{movie_id}

Get full details for a single movie.

**Response 200**:
```json
{
  "id": 1,
  "tmdb_id": 550,
  "imdb_id": "tt0137566",
  "title": "Fight Club",
  "release_date": "1999-10-15",
  "synopsis": "An insomniac office worker...",
  "genres": ["Drama", "Thriller"],
  "rating": 8.4,
  "poster_url": "https://image.tmdb.org/t/p/w500/...",
  "created_at": "2026-09-02T10:00:00Z",
  "updated_at": "2026-09-02T10:00:00Z"
}
```

**Response 404**:
```json
{
  "detail": "Movie not found"
}
```

---

### DELETE /api/v1/movies/{movie_id}

Remove a movie from the local database. Associated watchlist entries are cascade-deleted.

**Response 204**: No content

**Response 404**:
```json
{
  "detail": "Movie not found"
}
```

---

## Search

### GET /api/v1/search

Search the local database for movies by title.

**Query Parameters**:
| Parameter | Type | Required | Notes |
|-----------|------|----------|-------|
| `q` | string | Yes | Search query (min 2 chars) |
| `page` | int | No | Default 1 |
| `per_page` | int | No | Default 20, max 50 |

**Response 200**:
```json
{
  "results": [
    {
      "id": 1,
      "tmdb_id": 550,
      "title": "Fight Club",
      "release_date": "1999-10-15",
      "poster_url": "https://image.tmdb.org/t/p/w500/..."
    }
  ],
  "total": 3,
  "page": 1,
  "per_page": 20
}
```

**Response 200 (empty)**:
```json
{
  "results": [],
  "total": 0,
  "page": 1,
  "per_page": 20,
  "suggestion": "No local results. Import from TMDB by IMDB ID."
}
```

---

## Import

### POST /api/v1/movies/import

Import a movie from TMDB by IMDB ID (fallback when local search returns empty).

**Request Body**:
```json
{
  "imdb_id": "tt0137566"
}
```

**Response 201**:
```json
{
  "id": 1,
  "tmdb_id": 550,
  "imdb_id": "tt0137566",
  "title": "Fight Club",
  "release_date": "1999-10-15",
  "synopsis": "An insomniac office worker...",
  "genres": ["Drama", "Thriller"],
  "rating": 8.4,
  "poster_url": "https://image.tmdb.org/t/p/w500/..."
}
```

**Response 409**:
```json
{
  "detail": "Movie already exists in local database"
}
```

**Response 404**:
```json
{
  "detail": "No movie found for IMDB ID tt0137566"
}
```

**Response 502**:
```json
{
  "detail": "TMDB API is currently unavailable. Please try again later."
}
```

---

## Watchlists

### GET /api/v1/watchlists

List all watchlists.

**Response 200**:
```json
{
  "watchlists": [
    {
      "id": 1,
      "name": "To Watch",
      "created_at": "2026-09-02T10:00:00Z"
    }
  ]
}
```

---

### POST /api/v1/watchlists

Create a new watchlist.

**Request Body**:
```json
{
  "name": "Upcoming"
}
```

**Response 201**:
```json
{
  "id": 2,
  "name": "Upcoming",
  "created_at": "2026-09-02T10:00:00Z"
}
```

---

### PATCH /api/v1/watchlists/{watchlist_id}

Rename a watchlist.

**Request Body**:
```json
{
  "name": "Must Watch"
}
```

**Response 200**:
```json
{
  "id": 1,
  "name": "Must Watch",
  "created_at": "2026-09-02T10:00:00Z"
}
```

---

### DELETE /api/v1/watchlists/{watchlist_id}

Delete a watchlist and all its entries.

**Response 204**: No content

---

## Watchlist Entries

### GET /api/v1/watchlists/{watchlist_id}/entries

List all movies in a specific watchlist.

**Query Parameters**:
| Parameter | Type | Default | Notes |
|-----------|------|---------|-------|
| `status` | string | — | Filter by `to_watch` or `watched` |
| `sort` | string | `added_at` | Sort by `added_at`, `title`, or `status` |
| `order` | string | `desc` | `asc` or `desc` |
| `page` | int | 1 | |
| `per_page` | int | 20 | |

**Response 200**:
```json
{
  "entries": [
    {
      "id": 1,
      "watchlist_id": 1,
      "movie_id": 1,
      "status": "to_watch",
      "added_at": "2026-09-02T10:00:00Z",
      "watched_at": null,
      "movie": {
        "id": 1,
        "tmdb_id": 550,
        "title": "Fight Club",
        "release_date": "1999-10-15",
        "poster_url": "https://image.tmdb.org/t/p/w500/..."
      }
    }
  ],
  "total": 5,
  "page": 1,
  "per_page": 20
}
```

---

### POST /api/v1/watchlists/{watchlist_id}/entries

Add a movie to a specific watchlist.

**Request Body**:
```json
{
  "movie_id": 1
}
```

**Response 201**:
```json
{
  "id": 1,
  "watchlist_id": 1,
  "movie_id": 1,
  "status": "to_watch",
  "added_at": "2026-09-02T10:00:00Z",
  "watched_at": null
}
```

**Response 409**:
```json
{
  "detail": "Movie is already in this watchlist"
}
```

---

### PATCH /api/v1/watchlists/{watchlist_id}/entries/{entry_id}

Update a watchlist entry (mark as watched).

**Request Body**:
```json
{
  "status": "watched"
}
```

**Response 200**:
```json
{
  "id": 1,
  "watchlist_id": 1,
  "movie_id": 1,
  "status": "watched",
  "added_at": "2026-09-02T10:00:00Z",
  "watched_at": "2026-09-03T14:30:00Z"
}
```

---

### DELETE /api/v1/watchlists/{watchlist_id}/entries/{entry_id}

Remove a movie from the watchlist (does not delete the movie from local database).

**Response 204**: No content

---

## Jobs

### GET /api/v1/jobs/{job_id}

Check the status of a background job (e.g., trending sync, import).

**Response 200**:
```json
{
  "id": "Xb3nK9",
  "job_type": "sync_trending",
  "status": "completed",
  "progress": 100,
  "created_at": "2026-09-02T10:00:00Z",
  "started_at": "2026-09-02T10:00:01Z",
  "completed_at": "2026-09-02T10:02:30Z",
  "error_info": null
}
```

---

## Error Response Schema

All error responses follow a consistent shape:

```json
{
  "detail": "Human-readable error message"
}
```

The API layer maps domain exceptions (Principle XX) to HTTP status codes:

| Domain Exception | HTTP Status |
|-----------------|-------------|
| `MovieNotFoundError` | 404 |
| `MovieAlreadyExistsError` | 409 |
| `WatchlistNotFoundError` | 404 |
| `WatchlistEntryNotFoundError` | 404 |
| `WatchlistDuplicateError` | 409 |
| `JobNotFoundError` | 404 |
| `ExternalAPIError` | 502 |
| `ValidationError` | 422 |
