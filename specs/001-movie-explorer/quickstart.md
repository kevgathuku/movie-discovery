# Quickstart Validation Guide: Movie Explorer

**Date**: 2026-09-02
**Feature**: 001-movie-explorer

## Prerequisites

- Docker and Docker Compose installed
- TMDB API key (obtain from https://www.themoviedb.org/settings/api)
- Git

## Setup

```bash
# Clone and enter the project
git clone <repo-url> && cd movie-discovery

# Create environment file
cat > .env <<EOF
TMDB_API_KEY=your_tmdb_api_key_here
DATABASE_URL=postgresql+asyncpg://postgres:postgres@postgres:5432/movie_discovery
REDIS_URL=redis://redis:6379/0
EOF

# Start all services
docker compose up -d

# Run database migrations
docker compose exec api alembic upgrade head
```

## Validation Scenarios

### 1. Home Page Discovery (Offline)

**Prerequisite**: Background sync must have run at least once.

```bash
# Trigger a sync manually
docker compose exec api celery -A app.core.celery_app call app.tasks.sync_tasks.sync_trending_movies

# Wait for job to complete, then check
curl http://localhost:8000/api/v1/movies
```

**Expected**: Array of trending movies with titles, posters, and release dates. No network request to TMDB from the API layer.

---

### 2. Local Search

```bash
# Search for a movie that exists locally
curl "http://localhost:8000/api/v1/search?q=fight"
```

**Expected**: Matching movies from local database with poster, title, release year.

```bash
# Search for something that doesn't exist locally
curl "http://localhost:8000/api/v1/search?q=zzzznonexistent"
```

**Expected**: Empty results array with `"suggestion"` field indicating IMDB ID import option.

---

### 3. Import by IMDB ID (TMDB Fallback)

```bash
# Import a movie by IMDB ID
curl -X POST http://localhost:8000/api/v1/movies/import \
  -H "Content-Type: application/json" \
  -d '{"imdb_id": "tt0137566"}'
```

**Expected**: 201 response with full movie metadata (title: "Fight Club", genres, rating, poster, etc.).

```bash
# Try importing the same movie again
curl -X POST http://localhost:8000/api/v1/movies/import \
  -H "Content-Type: application/json" \
  -d '{"imdb_id": "tt0137566"}'
```

**Expected**: 409 response with `"Movie already exists in local database"`.

---

### 4. Movie Details

```bash
# Get details for an imported movie (use ID from step 3)
curl http://localhost:8000/api/v1/movies/{movie_id}
```

**Expected**: Full metadata including synopsis, genres, rating, cast info.

---

### 5. Watchlist Management

```bash
# Add movie to watchlist
curl -X POST http://localhost:8000/api/v1/watchlist \
  -H "Content-Type: application/json" \
  -d '{"movie_id": "{movie_id}"}'

# View watchlist
curl http://localhost:8000/api/v1/watchlist

# Mark as watched
curl -X PATCH http://localhost:8000/api/v1/watchlist/{entry_id} \
  -H "Content-Type: application/json" \
  -d '{"status": "watched"}'

# Remove from watchlist
curl -X DELETE http://localhost:8000/api/v1/watchlist/{entry_id}
```

**Expected**: Watchlist reflects additions, status changes, and removals. Movie remains in local database after watchlist removal.

---

### 6. Remove Movie from Local Database

```bash
curl -X DELETE http://localhost:8000/api/v1/movies/{movie_id}
```

**Expected**: 204 No Content. Movie and its watchlist entry are deleted.

---

### 7. Background Job Lifecycle

```bash
# Check job status
curl http://localhost:8000/api/v1/jobs/{job_id}
```

**Expected**: Job transitions through `queued` → `processing` → `completed` (or `failed` with error info).

---

### 8. Error Handling

```bash
# Invalid IMDB ID
curl -X POST http://localhost:8000/api/v1/movies/import \
  -H "Content-Type: application/json" \
  -d '{"imdb_id": "tt9999999"}'
```

**Expected**: 404 with `"No movie found for IMDB ID tt9999999"`.

```bash
# Invalid watchlist entry
curl -X PATCH http://localhost:8000/api/v1/watchlist/99999 \
  -H "Content-Type: application/json" \
  -d '{"status": "watched"}'
```

**Expected**: 404 with `"Watchlist entry not found"`.

---

### 9. API Contract Validation

```bash
# Verify OpenAPI docs are available
curl http://localhost:8000/docs
```

**Expected**: Swagger UI loads with all endpoints documented.

---

## Teardown

```bash
docker compose down -v   # Stops containers and removes data
```
