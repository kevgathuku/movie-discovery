# Movie Discovery

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

# Start all services
docker compose up -d

# Run database migrations
docker compose exec api alembic upgrade head
```

The API is available at `http://localhost:8000`. Interactive docs at `http://localhost:8000/docs`.

### Trigger Initial Data Sync

```bash
docker compose exec worker uv run celery -A app.tasks call app.tasks.sync_tasks.sync_trending_movies
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

| Method | Path      | Description       | Status      |
|--------|-----------|-------------------|-------------|
| GET    | `/health` | Health check      | Implemented |

### Movies

| Method | Path                     | Description          | Status      |
|--------|--------------------------|----------------------|-------------|
| GET    | `/api/v1/movies`         | List movies (paginated) | Implemented |
| GET    | `/api/v1/movies/{id}`    | Get movie details    | Stub        |
| DELETE | `/api/v1/movies/{id}`    | Delete a movie       | Stub        |
| POST   | `/api/v1/movies/import`  | Import from TMDB     | Stub        |

### Search

| Method | Path              | Description              | Status |
|--------|-------------------|--------------------------|--------|
| GET    | `/api/v1/search`  | Search movies locally, fallback to TMDB | Stub   |

### Watchlists

| Method | Path                                        | Description           | Status |
|--------|---------------------------------------------|-----------------------|--------|
| GET    | `/api/v1/watchlists`                        | List watchlists       | Stub   |
| POST   | `/api/v1/watchlists`                        | Create watchlist      | Stub   |
| GET    | `/api/v1/watchlists/{id}`                   | Get watchlist         | Stub   |
| PATCH  | `/api/v1/watchlists/{id}`                   | Update watchlist      | Stub   |
| DELETE | `/api/v1/watchlists/{id}`                   | Delete watchlist      | Stub   |
| GET    | `/api/v1/watchlists/{id}/entries`           | List entries          | Stub   |
| POST   | `/api/v1/watchlists/{id}/entries`           | Add movie to watchlist| Stub   |
| PATCH  | `/api/v1/watchlists/{id}/entries/{entry_id}`| Update entry status   | Stub   |
| DELETE | `/api/v1/watchlists/{id}/entries/{entry_id}`| Remove entry          | Stub   |

### Jobs

| Method | Path              | Description       | Status |
|--------|-------------------|-------------------|--------|
| GET    | `/api/v1/jobs/{id}` | Get job status  | Stub   |

## Data Model

- **Movie** — TMDB-sourced movie metadata (tmdb_id, imdb_id, title, release_date, synopsis, genres, rating, poster_url, source)
- **Watchlist** — Named collection of movies
- **WatchlistEntry** — Movie-to-watchlist association with status (`to_watch` / `watched`)
- **Job** — Background task tracking (status, progress, error info)

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
└── pyproject.toml
```

## Running Tests

```bash
docker compose exec api uv run pytest
```
