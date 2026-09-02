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

## 2026-09-02: Remove User Story 6 (Delete Movie) from scope

**Decision**: Remove the ability to delete movies from the local database. Movies persist once imported.

**Reason**: Simplifies the data model and avoids cascade-delete complexity. In a single-user app with a small local database, storage is not a concern. Removing this feature reduces scope and eliminates potential data loss risks.
