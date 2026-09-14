# Implementation Plan: User Auth

**Branch**: `002-user-auth` | **Date**: 2026-09-14 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/002-user-auth/spec.md` (full user model + JWT auth for web SPA and mobile, admin-only job tracking; reverses 001 single-user/no-auth assumption)

## Summary

Introduce `User` accounts (email + password, `user`/`admin` roles) with JWT bearer auth — short-lived access tokens plus single-use rotating refresh tokens — as the single authentication mechanism for the React SPA and future mobile clients. Scope all watchlists to their owning user via a new `owner_id` FK (existing rows backfilled to a seeded admin). Replace the public `GET /api/v1/jobs/{id}` stub with hidden admin-only `GET /admin/jobs` endpoints gated by a `require_admin` dependency. New libraries: `pyjwt` (JWT) and `pwdlib[argon2]` (password hashing).

## Technical Context

**Language/Version**: Python 3.14 (backend `requires-python = ">=3.14"`)

**Primary Dependencies**: FastAPI ≥0.141, SQLAlchemy 2.0 asyncio + asyncpg, Pydantic v2 + pydantic-settings, Celery + Redis (unchanged); NEW: `pyjwt>=2.13` (JWT mint/verify), `pwdlib[argon2]` (password hashing). See research.md for selection rationale.

**Storage**: PostgreSQL (existing `moviediscovery` DB + `moviediscovery_test` for tests). New tables `users`, `refresh_tokens`; new `watchlists.owner_id` FK. Alembic migration required; no `create_all`.

**Testing**: pytest + pytest-asyncio (`asyncio_mode = "auto"`), pytest-mock (`mocker` fixture only — never `unittest.mock`), httpx TestClient/ASGI transport. New coverage: auth service unit tests, refresh rotation/reuse tests, watchlist isolation tests, admin gate tests (401/403/200 matrix).

**Target Platform**: Linux server (Docker Compose: api, worker, scheduler, postgres, redis, frontend); clients: React SPA (Vite) + future mobile app over the same REST contract.

**Project Type**: web-service (modular monolith) + web SPA frontend; mobile client contract defined but not implemented (`client/` empty).

**Performance Goals**: Login/register p95 < 500 ms (Argon2 verify dominates; acceptable); authenticated request overhead < 5 ms (one indexed `users` lookup per request); local search still < 1 s (unchanged).

**Constraints**: `JWT_SECRET_KEY` required at startup (fail fast, no default); access 15 min / refresh 30 day defaults via env; rate-limited auth endpoints; CORS `allow_origins` must switch from `["*"]` to env-driven list (breaking change for `allow_credentials` correctness); `TMDB_API_KEY` and `JWT_SECRET_KEY` never reach clients; Argon2id parameters at `pwdlib` recommended defaults.

**Scale/Scope**: Personal/small-group app; hundreds of users max. Single `users` table, no sharding, no federated login. Refresh-token table grows ~1 row per active session; purged by expiry cleanup.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Architectural Boundaries | ✅ PASS | New code follows API → Services → Repositories → DB. `AuthService` holds login/token logic; `auth.py` routes stay thin; no SQL in routes. |
| II. Thin API Layer | ✅ PASS | `auth.py` / `admin_jobs.py` handle HTTP + schema validation + status codes only; delegate to `AuthService` / `JobRepository`. |
| III. Business Logic in Services | ✅ PASS | Token mint/rotate/revoke, credential verification, reuse detection live in `AuthService`; services raise domain exceptions (`InvalidCredentialsError`, `TokenRevokedError`), never `HTTPException`. |
| IV. Replaceable External Integrations | ✅ PASS | No new external integration. Hashing/JWT libs wrapped in small internal helpers so algorithms can change without touching services. |
| V./VIII. Async Processing | ✅ PASS | Auth is synchronous request/response; no background work added. Job writes stay in Celery workers as today. |
| VI. Persistence Isolation | ✅ PASS | `UserRepository`, `RefreshTokenRepository`; watchlist scoping enforced in service via repository filters, not inline SQL in routes. |
| IX. Idempotency | ✅ PASS | Register guarded by unique email constraint (409 on race); refresh rotation is single-use by design with reuse detection. |
| XI. Configuration and Secrets | ✅ PASS | `JWT_SECRET_KEY`, expiries, `CORS_ORIGINS`, admin bootstrap creds via env; secrets never logged, never sent to clients. |
| XIII. Database Migrations | ✅ PASS | One Alembic revision for `users`, `refresh_tokens`, `watchlists.owner_id` + backfill; reviewable, reproducible. |
| XIV. API Contracts | ✅ PASS | New Pydantic schemas (`UserRegisterRequest`, `TokenPair`, `UserResponse`, `AdminJobListResponse`); DB models never exposed. |
| XV. Testability | ✅ PASS | `AuthService` testable without FastAPI; JWT/hash helpers injectable/mockable; no real TMDB involved. |
| XVI. Dependency Injection | ✅ PASS | `get_current_user`, `require_admin` via FastAPI DI; sessions/services injected. |
| XVII. Simplicity Over Abstraction | ✅ PASS | No generic auth framework, no session store, no OIDC provider; header-only Bearer for both clients; single `role` enum instead of a permissions system. |
| XVIII. Single Application Boundary | ✅ PASS | Auth lives in the monolith; no new service/process. |
| XIX. Observability | ✅ PASS | Structured logs with `request_id` + `user_id` (never tokens/passwords); reuse-detection revocations logged as security events. |
| XX. Error Handling | ✅ PASS | New domain exceptions mapped at API boundary (401 generic credentials, 409 exists, 403 forbidden, 404 job); no internal detail leakage. |
| XXIV. Security Baseline | ⚠️ ATTENTION | This feature *is* the security surface: bcrypt/argon2 hashes, SHA-256 refresh hashes, generic login errors, rate limits, secret startup check. Constitution says "auth deferred from MVP but architecture SHOULD allow it later" — this is that later; spec 001's single-user assumption is explicitly reversed and recorded in `docs/decisions.md`. |
| XXV. Performance | ✅ PASS | Per-request user lookup is one indexed PK fetch; no N+1; pagination on admin job list. |

**Gate Result**: PASS — one intentional, documented reversal (001 single-user/no-auth assumption → full user model), no unjustified violations.

## Project Structure

### Documentation (this feature)

```text
specs/[###-feature]/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
backend/
├── app/
│   ├── api/
│   │   ├── auth.py               # NEW: register/login/refresh/logout (public, rate-limited)
│   │   ├── admin_jobs.py         # NEW: GET /admin/jobs (require_admin, hidden docs)
│   │   ├── jobs.py               # DELETE: public stub removed
│   │   ├── movies.py             # unchanged (stays public)
│   │   ├── search.py             # unchanged (stays public)
│   │   └── watchlist.py          # EDIT: gate with get_current_user, scope by owner_id
│   ├── services/
│   │   ├── auth_service.py       # NEW: register/authenticate/mint/rotate/revoke
│   │   ├── user_service.py       # NEW (thin): profile lookup, admin role changes
│   │   └── watchlist_service.py  # EDIT: owner_id scoping on every method
│   ├── repositories/
│   │   ├── user_repo.py          # NEW
│   │   └── refresh_token_repo.py # NEW
│   ├── models/
│   │   ├── user.py               # NEW: User + UserRole
│   │   └── refresh_token.py      # NEW: RefreshToken
│   │   └── watchlist.py          # EDIT: owner_id FK
│   ├── schemas/
│   │   ├── auth.py               # NEW: register/login/refresh/token/user schemas
│   │   └── job.py                # REUSE: JobResponse for admin endpoints
│   ├── security/                 # NEW: password hashing + JWT helpers (lib wrappers)
│   │   ├── passwords.py          # pwdlib wrapper
│   │   └── tokens.py             # pyjwt mint/verify wrapper
│   ├── dependencies.py           # EDIT: get_current_user, require_admin
│   ├── exceptions.py             # EDIT: + UserAlreadyExistsError, InvalidCredentialsError,
│   │                             #   TokenRevokedError, NotAuthorizedError
│   ├── config.py                 # EDIT: + JWT_SECRET_KEY, expiries, CORS_ORIGINS
│   ├── seed_admin.py             # NEW: bootstrap first admin (CLI)
│   └── main.py                   # EDIT: mount auth + admin routers, drop jobs stub,
│                                 #   env-driven CORS, new exception handlers
├── alembic/versions/
│   └── xxxx_add_users_auth.py    # NEW migration
└── tests/
    ├── unit/test_auth_service.py # NEW
    ├── unit/test_token_security.py # NEW (rotation/reuse/revoke)
    └── integration/api/
        ├── test_auth.py          # NEW (register→login→refresh→logout)
        ├── test_watchlist_isolation.py # NEW (cross-user 404)
        └── test_admin_jobs.py    # NEW (401/403/200 matrix)

frontend/
├── src/
│   ├── services/api.ts           # NEW: fetch wrapper (Bearer + single-flight refresh)
│   ├── context/AuthContext.tsx   # NEW (or .jsx to match current skeleton)
│   ├── components/RequireAuth.tsx# NEW route guards (+ RequireAdmin)
│   └── pages/
│       ├── Login.tsx             # NEW
│       └── AdminJobs.tsx         # NEW (admin only)
└── tests/                        # NEW frontend tests for auth flow

client/                           # contract defined (contracts/client-auth.md); no code yet
```

**Structure Decision**: Web-application layout (existing `backend/` + `frontend/`). Auth code follows the existing layered architecture (API → Services → Repositories → DB) plus a small `security/` wrapper package so hashing/JWT libraries stay replaceable (Principle IV). Mobile is contract-only in this feature.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient] |
