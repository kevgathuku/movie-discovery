# Implementation Plan: Movie Explorer

**Branch**: `001-movie-explorer` | **Date**: 2026-09-02 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/001-movie-explorer/spec.md`

## Summary

Movie Explorer is a full-stack web application for discovering, searching, importing, and tracking movies. Users browse trending movies from a local database (kept current by a background sync), search locally first with TMDB IMDB-ID import as a fallback, manage a personal watchlist, and view movie details. The backend is a Python/FastAPI modular monolith with Celery workers for async processing, PostgreSQL for persistence, and Redis as the Celery broker. The frontend is to be defined (leaning toward ReScript).

## Technical Context

**Language/Version**: Python 3.14

**Primary Dependencies**: FastAPI, Pydantic, SQLAlchemy, Alembic, httpx, Celery, Redis, sqids

**Storage**: PostgreSQL

**Testing**: pytest (with pytest-asyncio, pytest-celery, httpx TestClient)

**Target Platform**: Linux server (Docker), modern web browsers (desktop + tablet)

**Project Type**: web-service (modular monolith: API + Worker + Scheduler)

**Performance Goals**: Local search results within 1s; TMDB fallback import within 3s; 90% of search queries return results within 3s

**Constraints**: Single-user MVP; no auth; background sync keeps trending data ≤24h stale; TMDB API key must never reach frontend

**Scale/Scope**: Single-user local application; ~5 core entities; ~15 API endpoints

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Architectural Boundaries | ✅ PASS | API → Services → Repositories → Database; Services → TMDB Client → TMDB; API → Celery → Worker → Services |
| II. Thin API Layer | ✅ PASS | Routes handle HTTP only; delegate to services |
| III. Business Logic in Services | ✅ PASS | No HTTPException in services; domain exceptions used |
| IV. Replaceable External Integrations | ✅ PASS | TMDB isolated behind dedicated client (httpx) |
| V. Reliable Asynchronous Processing | ✅ PASS | Celery task queue for background work |
| VI. Persistence Isolation | ✅ PASS | SQLAlchemy queries in repositories only |
| VII. External API Isolation | ✅ PASS | Dedicated TMDB client handles auth, requests, parsing |
| VIII. Asynchronous Work | ✅ PASS | API enqueues Celery tasks; worker executes via services |
| IX. Idempotency | ✅ PASS | TMDB ID uniqueness constraint; idempotent imports |
| X. Reliable Background Jobs | ✅ PASS | Celery task states; retry on transient failures |
| XI. Configuration and Secrets | ✅ PASS | TMDB_API_KEY, DATABASE_URL, REDIS_URL via env vars |
| XII. Docker as Development Environment | ✅ PASS | docker compose up with frontend, api, worker, scheduler, postgres, redis |
| XIII. Database Migrations | ✅ PASS | Alembic migrations; no create_all |
| XIV. API Contracts | ✅ PASS | Pydantic schemas separate from SQLAlchemy models |
| XV. Testability | ✅ PASS | Services testable without FastAPI; TMDB mocked |
| XVI. Dependency Injection | ✅ PASS | FastAPI DI at boundary; services/repositories injected |
| XVII. Simplicity Over Abstraction | ✅ PASS | No generic repositories, no premature patterns |
| XVIII. Single Application Boundary | ✅ PASS | Modular monolith; shared codebase for API + Worker + Scheduler |
| XIX. Observability | ✅ PASS | Structured logs with request_id, job_id, tmdb_id |
| XX. Error Handling | ✅ PASS | Domain exceptions mapped to HTTP at API boundary |
| XXI. Data Ownership | ✅ PASS | PostgreSQL owns local data; TMDB ID vs internal ID distinguished |
| XXII. Incremental Development | ✅ PASS | Vertical slices per feature |
| XXIII. Feature Specs Define Boundaries | ✅ PASS | Spec identifies all layer responsibilities |
| XXIV. Security Baseline | ✅ PASS | Secrets server-side; input validation; parameterized queries |
| XXV. Performance Principles | ✅ PASS | Local reads preferred; background jobs for sync; pagination |

**Gate Result**: ALL PASS — no violations to justify.

## Project Structure

### Documentation (this feature)

```text
specs/001-movie-explorer/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   └── api.md
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

```text
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application factory
│   ├── config.py               # Settings via pydantic-settings
│   ├── dependencies.py         # FastAPI dependency injection
│   ├── models/                 # SQLAlchemy models
│   │   ├── __init__.py
│   │   ├── movie.py
│   │   ├── watchlist.py
│   │   └── job.py
│   ├── schemas/                # Pydantic request/response schemas
│   │   ├── __init__.py
│   │   ├── movie.py
│   │   ├── watchlist.py
│   │   └── job.py
│   ├── services/               # Business logic (no HTTP concepts)
│   │   ├── __init__.py
│   │   ├── movie_service.py
│   │   ├── search_service.py
│   │   ├── watchlist_service.py
│   │   ├── sync_service.py
│   │   └── import_service.py
│   ├── repositories/           # Database access layer
│   │   ├── __init__.py
│   │   ├── movie_repo.py
│   │   ├── watchlist_repo.py
│   │   └── job_repo.py
│   ├── clients/                # External API clients
│   │   ├── __init__.py
│   │   └── tmdb_client.py
│   ├── api/                    # FastAPI routes (thin)
│   │   ├── __init__.py
│   │   ├── movies.py
│   │   ├── search.py
│   │   ├── watchlist.py
│   │   └── jobs.py
│   ├── tasks/                  # Celery task definitions
│   │   ├── __init__.py
│   │   ├── sync_tasks.py
│   │   └── import_tasks.py
│   └── exceptions.py           # Domain exceptions
├── alembic/                    # Database migrations
│   ├── env.py
│   └── versions/
├── alembic.ini
├── tests/
│   ├── unit/
│   │   ├── services/
│   │   └── repositories/
│   ├── integration/
│   │   └── api/
│   └── contract/
│       └── clients/
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml
└── requirements.txt

frontend/
├── src/
│   ├── components/
│   ├── pages/
│   └── services/
├── tests/
├── Dockerfile
└── package.json
```

**Structure Decision**: Option 2 — Web application with `backend/` and `frontend/` directories. Backend follows the constitution's layered architecture (API → Services → Repositories → Database) with a separate `clients/` boundary for TMDB. Single codebase shared by API, Worker, and Scheduler processes via Celery.

## Complexity Tracking

No constitution violations. No complexity justifications required.
