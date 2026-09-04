# Movie Explorer

FastAPI backend for discovering, searching, importing, and tracking movies. Uses The Movie Database (TMDB) as the external data source, with a local PostgreSQL cache for offline browsing and watchlist management.

## Tech Stack

- **Python 3.14** / **FastAPI** — async API layer
- **SQLAlchemy** (async) + **Alembic** — ORM and migrations
- **Celery** + **Redis** — background task queue and scheduler
- **PostgreSQL** — persistence
- **Docker Compose** — local development environment
- **TMDB API** — external movie data source

## Getting Started

### Prerequisites

- Docker and Docker Compose
- A [TMDB API key](https://www.themoviedb.org/settings/api)

### Setup

```bash
git clone <repo-url> && cd movie-discovery

# Create environment file
cat > .env <<EOF
TMDB_API_KEY=your_tmdb_api_key_here
EOF

# Start all services (migrations run automatically on startup)
docker compose up -d
```

The API is available at `http://localhost:8000`. Interactive docs at `http://localhost:8000/docs`.

### Trigger Initial Data Sync

```bash
docker compose exec worker uv run celery -A app.tasks call app.tasks.tasks.sync_trending_movies
```

This fetches trending movies from TMDB into the local database. The scheduler also runs this automatically every 6 hours.

## Docker Services

| Service    | Description                              | Port  |
|------------|------------------------------------------|-------|
| `api`      | FastAPI application (uvicorn)            | 8000  |
| `worker`   | Celery worker for background tasks       | —     |
| `scheduler`| Celery beat scheduler                    | —     |
| `postgres` | PostgreSQL 16                            | 5433  |
| `redis`    | Redis 7 (Celery broker)                  | 6379  |

## Environment Variables

| Variable        | Required | Default                                                           | Description       |
|-----------------|----------|-------------------------------------------------------------------|-------------------|
| `TMDB_API_KEY`  | Yes      | —                                                                 | TMDB API key      |
| `DATABASE_URL`  | No       | `postgresql+asyncpg://postgres:postgres@localhost:5433/moviediscovery` | Database URL      |
| `REDIS_URL`     | No       | `redis://localhost:6379/0`                                        | Redis/Celery broker |

## API Endpoints

### Health

| Method | Path      | Description       |
|--------|-----------|-------------------|
| GET    | `/health` | Health check      |

### Movies

| Method | Path                     | Description          | Status      |
|--------|--------------------------|----------------------|-------------|
| GET    | `/api/v1/movies`         | List movies (paginated) | Implemented |
| GET    | `/api/v1/movies/{id}`    | Get movie details    | Implemented |
| DELETE | `/api/v1/movies/{id}`    | Delete a movie       | Stub        |
| POST   | `/api/v1/movies/import`  | Import from TMDB by IMDB ID | Implemented |

### Search

| Method | Path              | Description              | Status |
|--------|-------------------|--------------------------|--------|
| GET    | `/api/v1/search`  | Search movies locally, fallback to TMDB | Implemented |

### Watchlists

| Method | Path                                        | Description           | Status |
|--------|---------------------------------------------|-----------------------|--------|
| GET    | `/api/v1/watchlists`                        | List watchlists       | Implemented |
| POST   | `/api/v1/watchlists`                        | Create watchlist      | Implemented |
| PATCH  | `/api/v1/watchlists/{id}`                   | Rename watchlist      | Implemented |
| DELETE | `/api/v1/watchlists/{id}`                   | Delete watchlist      | Implemented |
| GET    | `/api/v1/watchlists/{id}/entries`           | List entries (filterable, sortable) | Implemented |
| POST   | `/api/v1/watchlists/{id}/entries`           | Add movie to watchlist| Implemented |
| PATCH  | `/api/v1/watchlists/{id}/entries/{entry_id}`| Mark entry as watched | Implemented |
| DELETE | `/api/v1/watchlists/{id}/entries/{entry_id}`| Remove entry          | Implemented |

### Jobs

| Method | Path              | Description       | Status |
|--------|-------------------|-------------------|--------|
| GET    | `/api/v1/jobs/{id}` | Get job status  | Stub   |

## Data Model

- **Movie** — TMDB-sourced movie metadata (tmdb_id, imdb_id, title, release_date, synopsis, genres, rating, poster_url, source, created_at, updated_at)
- **Watchlist** — Named collection of movies (id, name, created_at)
- **WatchlistEntry** — Movie-to-watchlist association with status (`to_watch` / `watched`), timestamps (added_at, watched_at)
- **Job** — Background task tracking (id, job_type, status, progress, created_at, started_at, completed_at, error_info, celery_task_id)

## Project Structure

```
backend/
├── app/
│   ├── api/            # FastAPI route handlers
│   ├── clients/        # External API clients (TMDB)
│   ├── models/         # SQLAlchemy ORM models
│   ├── repositories/   # Data access layer
│   ├── schemas/        # Pydantic request/response schemas
│   ├── services/       # Business logic
│   ├── tasks/          # Celery task definitions
│   ├── config.py       # Settings (pydantic-settings)
│   ├── dependencies.py # FastAPI dependency injection
│   ├── exceptions.py   # Domain exceptions
│   └── main.py         # App factory
├── alembic/            # Database migrations
├── tests/              # Test suite
├── Dockerfile
├── docker-entrypoint.sh
└── pyproject.toml
```

## Development

### Linting

```bash
uv run ruff check app/ tests/
```

### Running Tests

```bash
# On host (requires TEST_DATABASE_URL and ADMIN_DATABASE_URL pointing to a running PostgreSQL)
uv run pytest

# Inside Docker
docker compose exec api uv run pytest
```

### CI

Tests and linting run automatically via GitHub Actions on every push and pull request.
