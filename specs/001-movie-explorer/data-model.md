# Data Model: Movie Explorer

**Date**: 2026-09-02
**Feature**: 001-movie-explorer

## Entities

### Movie

Represents a film with metadata imported from TMDB.

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| `id` | BigInteger | PK, auto-increment | Internal identity |
| `tmdb_id` | Integer | UNIQUE, NOT NULL | TMDB identity |
| `imdb_id` | String(20) | UNIQUE, nullable | IMDB identity (e.g., `tt1375666`) |
| `title` | String(500) | NOT NULL | |
| `release_date` | Date | nullable | |
| `synopsis` | Text | nullable | |
| `genres` | JSON | nullable | Array of genre strings |
| `rating` | Float | nullable | TMDB average rating (0-10) |
| `poster_url` | String(500) | nullable | Full URL to poster image |
| `source` | Enum(`manual`, `sync`) | NOT NULL, default `manual` | Internal only — not exposed via API |
| `created_at` | DateTime | NOT NULL, default `now()` | |
| `updated_at` | DateTime | NOT NULL, default `now()`, on update `now()` | |

**Indexes**:
- `ix_movies_tmdb_id` on `tmdb_id` (unique)
- `ix_movies_imdb_id` on `imdb_id` (unique, partial where `imdb_id IS NOT NULL`)
- `ix_movies_title` on `title` (for local search)
- `ix_movies_source` on `source`

**Validation rules** (from spec R13):
- `tmdb_id` must be positive integer
- `title` must be non-empty
- `rating` must be between 0 and 10 if present

### WatchlistEntry

Represents a user's intent to watch a movie.

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| `id` | BigInteger | PK, auto-increment | |
| `movie_id` | BigInteger | FK → `movies.id`, NOT NULL, ON DELETE CASCADE | |
| `status` | Enum(`to_watch`, `watched`) | NOT NULL, default `to_watch` | |
| `added_at` | DateTime | NOT NULL, default `now()` | |
| `watched_at` | DateTime | nullable | Set when status changes to `watched` |

**Indexes**:
- `ix_watchlist_entries_movie_id` on `movie_id`
- `ix_watchlist_entries_status` on `status`

**Unique constraint**:
- `uq_watchlist_entries_movie_id` on `movie_id` — prevents duplicate watchlist entries (Principle IX: idempotency)

**State transitions**:
```
to_watch → watched (one-way; no revert defined in spec)
```

### Job

Tracks background task lifecycle (Principle X: Reliable Background Jobs).

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| `id` | String(20) | PK | Sqids-generated short URL-safe ID (sqids.org/python) |
| `job_type` | String(100) | NOT NULL | e.g., `sync_trending`, `import_movie` |
| `status` | Enum(`queued`, `processing`, `completed`, `failed`) | NOT NULL, default `queued` | Lifecycle state |
| `progress` | Integer | nullable, default 0 | 0-100 percentage |
| `created_at` | DateTime | NOT NULL, default `now()` | |
| `started_at` | DateTime | nullable | |
| `completed_at` | DateTime | nullable | |
| `error_info` | JSON | nullable | Error message and traceback on failure |
| `celery_task_id` | String(255) | UNIQUE, nullable | Celery's task ID for tracking |

**Indexes**:
- `ix_jobs_status` on `status`
- `ix_jobs_job_type` on `job_type`
- `ix_jobs_celery_task_id` on `celery_task_id` (unique)

## Relationships

```
Movie 1 ──── N WatchlistEntry
  (one movie can have many watchlist entries — but unique constraint
   means at most one per movie in single-user setup)
```

No foreign keys between Job and Movie — jobs reference movie data via `tmdb_id` or `movie_id` in their task arguments, not as a database relationship.

## Enums

```python
class MovieSource(str, enum.Enum):
    manual = "manual"    # User imported via IMDB ID fallback
    sync = "sync"        # Added by background trending sync

class WatchlistStatus(str, enum.Enum):
    to_watch = "to_watch"
    watched = "watched"

class JobStatus(str, enum.Enum):
    queued = "queued"
    processing = "processing"
    completed = "completed"
    failed = "failed"
```

## Design Decisions

1. **BIGINT auto-increment PKs for Movie and WatchlistEntry**: Simple, fast, sufficient for single-user application. Sequential IDs are acceptable at this scale.

2. **Sqids-generated string PKs for Job**: Short, URL-safe IDs suitable for API exposure. Generated application-side using the `sqids` Python library before insert.

3. **`source` field on Movie**: Distinguishes user-imported movies from sync'd trending movies. Internal only — not exposed via API response.

4. **Separate `imdb_id` field**: Required for the IMDB ID import fallback flow (spec R7). Indexed for lookup.

5. **`genres` as JSON**: TMDB genres are simple string arrays. No need for a separate genres table at this scale (Principle XVII: Simplicity Over Abstraction).

6. **Job table for lifecycle tracking**: Satisfies Principle X requirements (job ID, type, progress, timestamps, error info). Celery's built-in result backend supplements this but the Job table is the authoritative source for the API.

7. **ON DELETE CASCADE on watchlist.movie_id**: When a movie is deleted from the local database (spec R15), its watchlist entries are automatically removed (spec acceptance scenario).
