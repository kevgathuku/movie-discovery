# Architecture Decisions

## 2026-09-02: PostgreSQL for test database instead of SQLite

**Decision**: Use a dedicated PostgreSQL database (`moviediscovery_test`) for tests instead of SQLite.

**Reason**: SQLite doesn't support PostgreSQL-specific features (enums, JSON, `ON DELETE CASCADE`). Tests passing on SQLite could fail on production. A separate test database ensures parity with production while keeping test data isolated.

---

## 2026-09-02: Docker venv at `/opt/venv` instead of `/app/.venv`

**Decision**: Move Python virtual environment to `/opt/venv` in the Docker container.

**Reason**: The `.venv` directory was being mounted over by the volume bind mount, causing the container to fail on startup. `/opt/venv` avoids the conflict.

---

## 2026-09-02: Auto-create test database via session-scoped fixture

**Decision**: Create and drop the `moviediscovery_test` database using a session-scoped pytest fixture with `AUTOCOMMIT` isolation.

**Reason**: `DROP DATABASE` and `CREATE DATABASE` cannot run inside a transaction block. Using `isolation_level="AUTOCOMMIT"` on the connection allows these DDL statements to execute.

---

## 2026-09-02: Lazy IMDB ID enrichment on movie detail

**Decision**: Fetch `imdb_id` from TMDB on-demand when `GET /movies/{id}` is called, rather than during sync.

**Reason**: The `/movie/popular` endpoint doesn't return IMDB IDs. Getting them requires individual `/movie/{id}?append_to_response=external_ids` calls (20+ per sync). Lazy enrichment avoids the upfront API cost while still populating the field when users view movie details.

---

## 2026-09-02: MovieSource enum values

**Decision**: Use `MovieSource.sync` for movies from TMDB sync/import, not `MovieSource.tmdb`.

**Reason**: The enum was defined with `manual` and `sync` values. Using an undefined value (`"tmdb"`) caused PostgreSQL `DataError`. Synced movies are `sync`, manually entered movies are `manual`.

---

## 2026-09-02: Celery task naming convention

**Decision**: Rename `sync_tasks.py` to `tasks.py` for Celery autodiscovery.

**Reason**: Celery's `autodiscover_tasks` looks for a `tasks.py` file by default. Renaming avoids manual task registration and follows the convention.

---

## 2026-09-02: Remove User Story 7 (Job Status Tracking) from scope

**Decision**: Remove the job status tracking API and service from scope. Background sync runs via Celery scheduler without public API polling.

**Reason**: Simplifies the API surface and eliminates unnecessary job state tracking endpoints for MVP.

---

## 2026-09-04: Use pytest-mock instead of unittest.mock

**Decision**: Use `pytest-mock` (`mocker` fixture) for all test mocking. Never import `MagicMock` or `AsyncMock` from `unittest.mock`.

**Reason**: The `mocker` fixture auto-cleans mocks after each test, eliminating forgotten `stop()` calls and unpatched mocks. `mocker.MagicMock()` / `mocker.AsyncMock()` are direct replacements. All 5 files that used `unittest.mock` have been converted.

---

## 2026-09-04: Deterministic dependency management with uv lock

**Decision**: Use `uv lock` + `uv sync` as the single source of truth for dependencies. Never run `uv pip install` inside Docker containers.

**Reason**: Running `uv pip install` or `uv sync` with a stale lock file inside the container caused packages to be stripped or installed into the wrong environment. The correct workflow is:

1. Edit `pyproject.toml` on the host
2. Run `uv lock` to regenerate `uv.lock`
3. Run `uv sync --extra dev` to apply to host `.venv`
4. Run `docker compose build api` to rebuild the container from the updated lock file

The Dockerfile installs into `/opt/venv` (via `UV_PROJECT_ENVIRONMENT`), which is separate from the host's `backend/.venv`. The `UV_NO_SYNC=1` env var prevents `uv run` from re-syncing at runtime.
