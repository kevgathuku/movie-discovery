# Research: Movie Explorer

**Date**: 2026-09-02
**Feature**: 001-movie-explorer

## Technology Decisions

### 1. FastAPI Application Pattern

**Decision**: `create_app()` factory + `lifespan` context manager + `app.state` resource bridge

**Rationale**: Fresh app instances per test, no shared mutable state, deterministic routing, clean resource lifecycle. Factory is synchronous and I/O-free — callable from pytest without an event loop.

**Alternatives considered**:
- Module-level `app = FastAPI()` — rejected: hard to create isolated test instances
- Startup events — deprecated in FastAPI 0.93+; lifespan is the replacement

### 2. Celery Integration with FastAPI

**Decision**: Shared `pydantic-settings` config + services as pure functions (no framework coupling) + Celery tasks open their own DB sessions

**Rationale**: Services are testable without FastAPI or Celery. Celery tasks are synchronous (`def`) and use `asyncio.run()` to drive async code. Each task opens its own `AsyncSession` and `httpx.AsyncClient` since the request's resources are closed when the task runs.

**Alternatives considered**:
- Celery autodiscover with shared app — rejected: tighter coupling
- Sync SQLAlchemy in workers — rejected: would require separate model/session code

### 3. SQLAlchemy Session Strategy

**Decision**: `AsyncSession` with `asyncpg` everywhere; `expire_on_commit=False`; per-request yield dependency

**Rationale**: Async sessions align with FastAPI's event loop. `expire_on_commit=False` prevents `MissingGreenlet` errors. One engine per process, `async_sessionmaker` at module scope.

**Alternatives considered**:
- Sync sessions with thread pool — rejected: hidden bottleneck, separate code path
- `scoped_session` — rejected: keys on thread identity; wrong for single-threaded event loop

### 4. TMDB Client Pattern

**Decision**: Shared `httpx.AsyncClient` on `app.state` + dedicated `TMDBClient` class wrapping all TMDB interactions

**Rationale**: Connection reuse (saves 50-200ms per request), centralized error handling, Pydantic response validation, retry logic in one place. Client is mockable for tests.

**Alternatives considered**:
- `requests` — rejected: synchronous, blocks event loop
- New `httpx.AsyncClient` per request — rejected: wastes connections, adds latency

### 5. Alembic Migration Strategy

**Decision**: Code-first with `target_metadata = Base.metadata`, naming conventions on `Base` from day one, reviewed autogenerate drafts

**Rationale**: Deterministic constraint names, migrations ship in same PR as code, full rollback capability. Naming conventions prevent "constraint rename diff storm."

**Alternatives considered**:
- `create_all()` — rejected: constitution forbids it (Principle XIII)
- Manual SQL migrations — rejected: no autogenerate, error-prone

### 6. Celery Beat for Periodic Sync

**Decision**: Separate Beat process + `crontab(hour="*/6")` schedule + Redis distributed lock to prevent overlap

**Rationale**: Beat and workers have different resource profiles. `crontab` aligns to clock boundaries. Redis lock prevents duplicate execution if sync takes longer than the interval.

**Alternatives considered**:
- `--beat` flag on worker — rejected: couples scheduling to worker lifecycle
- APScheduler — rejected: adds dependency with no benefit over Celery Beat

### 7. Frontend

**Decision**: Deferred — leaning toward ReScript over React with compatible bundler

**Rationale**: Backend is the priority. Frontend framework choice does not affect backend architecture. The API contract (Pydantic schemas) is the integration boundary.

**Alternatives considered**:
- React/TypeScript — would work but user prefers ReScript
- Vue/Svelte — not mentioned by user

## TMDB API Notes

- Base URL: `https://api.themoviedb.org/3`
- Authentication: Bearer token via `Authorization` header
- Rate limit: ~40 requests per 10 seconds
- Key endpoints needed:
  - `GET /movie/popular` — trending sync
  - `GET /movie/{id}` — movie details
  - `GET /movie/{id}/credits` — cast info
  - `GET /search/movie` — search (used only if local search returns empty, per clarification)
  - `GET /find/{external_id}` — import by IMDB ID (`external_source=imdb_id`)

### 8. Job Primary Keys (Sqids)

**Decision**: Use `sqids` Python library (sqids.org/python) to generate short, URL-safe string IDs for Job records.

**Rationale**: Job IDs are exposed via the API (e.g., polling job status). Sqids produce compact, non-sequential, human-friendly IDs (e.g., `Xb3nK9`) that are safe to expose without leaking internal count or structure.

**Alternatives considered**:
- UUID — rejected: too long for URL exposure, user wants simplicity
- BIGINT — rejected: sequential IDs leak implementation details for externally-facing job IDs
- ULID — rejected: still 26 characters, no benefit over Sqids for this use case
