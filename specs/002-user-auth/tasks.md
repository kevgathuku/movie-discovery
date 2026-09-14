# Tasks: User Auth

**Input**: Design documents from `/specs/002-user-auth/`

**Prerequisites**: plan.md, spec.md, data-model.md, contracts/auth.md, contracts/admin-jobs.md, contracts/client-auth.md, research.md, quickstart.md

**Tests**: Included — success criteria SC-002/SC-003/SC-004 require automated proof (rotation/reuse, isolation, gate matrix), and Constitution XV requires service/repo/API coverage. `pytest-mock` (`mocker`) only; never `unittest.mock`.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Dependencies, configuration surface, decision record

- [X] T001 Add `pyjwt>=2.13`, `pwdlib[argon2]`, `slowapi` to `backend/pyproject.toml`, run `uv lock` + `uv sync --extra dev` on host, rebuild with `docker compose build api` (per `docs/decisions.md` uv-lock workflow; never `uv pip install` in containers)
- [X] T002 [P] Extend `backend/app/config.py` Settings with `JWT_SECRET_KEY` (required, no default — fail fast), `JWT_ALGORITHM="HS256"`, `ACCESS_TOKEN_EXPIRE_MINUTES=15`, `REFRESH_TOKEN_EXPIRE_DAYS=30`, `CORS_ORIGINS` (comma-separated, default empty)
- [X] T003 [P] Record reversal of 001 single-user/no-auth assumption + `pyjwt`/`pwdlib`/`slowapi` selections in `docs/decisions.md`, and file to MemPalace (`wing: movie_discovery, room: general`) per `AGENTS.md`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Auth primitives, user/session persistence, admin gate, schema migration — MUST complete before ANY user story

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Add `UserAlreadyExistsError`, `InvalidCredentialsError`, `TokenRevokedError`, `NotAuthorizedError` to `backend/app/exceptions.py`
- [X] T005 [P] Create `backend/app/security/passwords.py` — `pwdlib` wrapper (`hash_password`, `verify_password`, Argon2id recommended defaults)
- [X] T006 [P] Create `backend/app/security/tokens.py` — `pyjwt` wrapper (`mint_access_token`, `decode_access_token` with pinned `algorithms=["HS256"]`, opaque `new_refresh_token` via `secrets`, `sha256_hash` for storage)
- [X] T007 [P] Create `backend/app/models/user.py` — `User` + `UserRole` (`user`/`admin`) per `data-model.md`
- [X] T008 [P] Create `backend/app/models/refresh_token.py` — `RefreshToken` (`jti`, `family_id`, `token_hash`, `expires_at`, `revoked_at`) per `data-model.md`
- [X] T009 [P] Create `backend/app/repositories/user_repo.py` — `get_by_email` (normalized), `get_by_id`, `create`
- [X] T010 [P] Create `backend/app/repositories/refresh_token_repo.py` — `store_hash`, `get_by_hash`, `revoke_jti`, `revoke_family`, `revoke_all_for_user`, `purge_expired`
- [X] T011 [P] Add `get_current_user` (Bearer decode → load user → `is_active` check) and `require_admin` (403 unless `role == admin`) to `backend/app/dependencies.py`
- [X] T012 Create Alembic revision A — `users` + `refresh_tokens` tables, `watchlists.owner_id` NULLABLE FK → `users.id` ON DELETE CASCADE (no backfill yet)
- [X] T013 [P] Create `backend/app/seed_admin.py` CLI — reads `ADMIN_EMAIL`/`ADMIN_PASSWORD` from env, creates first `role=admin` user, refuses if an admin exists (unless `--force`), never logs the password
- [X] T014 Create Alembic revision B (depends on T012 + seeded admin via T013 at deploy time) — backfill `watchlists.owner_id` to first admin, then `SET NOT NULL` + `ix_watchlists_owner_id` index; assert row count preserved (SC-006)

**Checkpoint**: Foundation ready — `users`/`refresh_tokens` tables, hashing/JWT helpers, `get_current_user`/`require_admin`, owner column with backfill path; user story implementation can now begin

---

## Phase 3: User Story 1 — Register and log in (Priority: P1) 🎯 MVP

**Goal**: Email+password registration and login issuing access + refresh tokens; `GET /me`

**Independent Test**: Register via `POST /api/v1/auth/register` → 201 with no password material; login → 200 token pair; `GET /api/v1/auth/me` with access token → 200; wrong password → 401 generic; duplicate email → 409; bad input → 422

### Tests for User Story 1

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T015 [P] [US1] Unit tests for `AuthService` register/authenticate/mint in `backend/tests/unit/test_auth_service.py` (mocked repos via `mocker`, real `security/` helpers)
- [X] T016 [P] [US1] Unit tests for password/JWT helpers in `backend/tests/unit/test_security.py` (hash/verify, mint/decode, expiry, wrong-algorithm rejection)
- [X] T017 [P] [US1] Integration tests for register/login/me in `backend/tests/integration/api/test_auth.py` (201/200/401-generic/409/422 matrix per quickstart §2)

### Implementation for User Story 1

- [X] T018 [P] [US1] Create auth Pydantic schemas in `backend/app/schemas/auth.py` (`UserRegisterRequest`, `UserLoginRequest`, `TokenPairResponse`, `UserResponse`)
- [X] T019 [US1] Implement `register`/`authenticate`/`mint_pair` in `backend/app/services/auth_service.py` (domain exceptions only, never `HTTPException`; email normalize; generic credential failure)
- [X] T020 [US1] Create `backend/app/api/auth.py` with `POST /register`, `POST /login`, `GET /me` + `slowapi` limits, and wire router + new exception handlers (`UserAlreadyExistsError`→409, `InvalidCredentialsError`→401) in `backend/app/main.py`

**Checkpoint**: US1 fully functional and independently testable — full auth MVP (register/login/me) without sessions management

---

## Phase 4: User Story 2 — Stay logged in and log out (Priority: P1)

**Goal**: Single-use refresh rotation with reuse detection, logout, logout-everywhere

**Independent Test**: `POST /auth/refresh` with R1 → new pair (R2), R1 reuse → 401 + family revoked (R2 also 401); logout revokes session; logout-all revokes all sessions (quickstart §3)

> **NOTE: Same files as US1 (`auth_service.py`, `api/auth.py`) — implement sequentially after US1, not in parallel**

### Tests for User Story 2

- [X] T021 [P] [US2] Token security tests (rotation, reuse-revokes-family, logout, logout-all, expiry) in `backend/tests/unit/test_token_security.py`
- [X] T022 [P] [US2] Integration tests for refresh/logout/logout-all flow in `backend/tests/integration/api/test_auth_refresh.py`

### Implementation for User Story 2

- [X] T023 [US2] Add `rotate_refresh` (single-use + `family_id` reuse detection → revoke family), `logout`, `logout_all` to `backend/app/services/auth_service.py`, extending `backend/app/schemas/auth.py` (`RefreshRequest`)
- [X] T024 [US2] Add `POST /refresh`, `POST /logout`, `POST /logout-all` with `slowapi` limits to `backend/app/api/auth.py` (reuse event logged as security warning with `user_id`, never the token)

**Checkpoint**: US1 + US2 deliver the complete backend auth slice — independently valuable to any client (web, mobile, CLI)

---

## Phase 5: User Story 3 — My watchlists are mine (Priority: P2)

**Goal**: All watchlists owned by exactly one user; cross-user access returns 404

**Independent Test**: User A creates watchlist W; user B lists (empty) and gets 404 on W; anonymous gets 401 on all watchlist endpoints (quickstart §4)

### Tests for User Story 3

- [X] T025 [P] [US3] Cross-user isolation integration tests in `backend/tests/integration/api/test_watchlist_isolation.py` (create-as-A/read-as-B→404, list scoping, entry-level scoping, anonymous→401)

### Implementation for User Story 3

- [X] T026 [US3] Scope every `WatchlistService` method by `owner_id` in `backend/app/services/watchlist_service.py` (constructor takes `owner_id`; all queries filter `(id, owner_id)`)
- [X] T027 [US3] Gate `backend/app/api/watchlist.py` with `Depends(get_current_user)` and pass `current_user.id` as `owner_id` into the service

**Checkpoint**: US3 working — per-user data isolation proven; can run in parallel with US2/US4 (different files) once US1 is done

---

## Phase 6: User Story 4 — Admin views job status (Priority: P2)

**Goal**: Hidden admin-only job history; public stub removed

**Independent Test**: Admin `GET /admin/jobs` → 200 paginated; missing id → 404; user → 403; anonymous → 401; `/api/v1/jobs/*` → 404; `/openapi.json` contains no `/admin` paths (quickstart §5)

### Tests for User Story 4

- [X] T028 [P] [US4] Admin gate matrix tests in `backend/tests/integration/api/test_admin_jobs.py` (401/403/200/404 + OpenAPI-hidden assertion + public-stub-gone assertion)

### Implementation for User Story 4

- [X] T029 [US4] Create `backend/app/api/admin_jobs.py` — `APIRouter(prefix="/admin/jobs", dependencies=[Depends(require_admin)], include_in_schema=False)` with `GET /` (status/job_type filters, pagination, newest first) and `GET /{job_id}`, reusing `JobRepository` + `JobResponse`
- [X] T030 [US4] Edit `backend/app/main.py` — mount `admin_jobs` router, add `JobNotFoundError`→404 handler, remove `jobs_router` import/mount; delete `backend/app/api/jobs.py`

**Checkpoint**: US4 working — original motivation delivered; parallel-safe with US2/US3 (different files) once US1 is done

---

## Phase 7: User Story 5 — Web SPA login session (Priority: P3)

**Goal**: React login persistence via silent refresh; admin-gated jobs UI

**Independent Test**: Log in via SPA → reload → still logged in; expired access transparently refreshed; admin sees jobs panel; non-admin blocked by route guard (spec US5 scenarios)

### Implementation for User Story 5

- [X] T031 [US5] Tighten CORS in `backend/app/main.py` — `allow_origins` from `CORS_ORIGINS` env (no more `["*"]`); keep `allow_credentials=True`
- [X] T032 [P] [US5] Create `frontend/src/services/api.ts` — fetch wrapper attaching Bearer, single-flight refresh + one retry per `contracts/client-auth.md` (tokens in memory only, never `localStorage`)
- [X] T033 [P] [US5] Create `frontend/src/context/AuthContext.jsx` + `frontend/src/components/RequireAuth.jsx` / `RequireAdmin.jsx` route guards (`.jsx` to match existing `main.jsx` skeleton)
- [X] T034 [P] [US5] Create `frontend/src/pages/Login.jsx` (register + login forms with loading/error states)
- [X] T035 [US5] Create `frontend/src/pages/AdminJobs.jsx` (calls `/admin/jobs`, loading/error/empty states; depends on T032)
- [X] T036 [P] [US5] Frontend auth flow tests in `frontend/tests/` (login persistence, 401→refresh→retry, admin guard)

**Checkpoint**: All user stories independently functional — web SPA consumes the same Bearer contract mobile will use

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Hardening, docs, full validation

- [X] T037 [P] Call `purge_expired()` on refresh-token writes (or document scheduled purge) in `backend/app/repositories/refresh_token_repo.py` usage sites — `# ponytail: in-process slowapi limiter; move to Redis when >1 API replica` comment at limiter setup in `backend/app/api/auth.py`
- [X] T038 [P] Document `/auth/*` + `/admin/jobs` in `specs/001-movie-explorer/contracts/api.md` (or superseding note pointing at `specs/002-user-auth/contracts/`)
- [X] T039 [P] Document `JWT_SECRET_KEY`, `CORS_ORIGINS`, `ADMIN_EMAIL`/`ADMIN_PASSWORD`, and `python -m app.seed_admin` bootstrap in `README.md`
- [ ] T040 Run `quickstart.md` validation scenarios end-to-end (all 6 sections)
- [ ] T041 Final gate: `uv run ruff check app/ tests/` zero errors + `uv run pytest` all green, per `AGENTS.md` checklist

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies — start immediately
- **Phase 2 (Foundational)**: Depends on Phase 1 — BLOCKS all user stories (migration rev A/B + seed CLI order matters at deploy: migrate A → seed admin → migrate B)
- **Phase 3–7 (User Stories)**: All depend on Phase 2 completion
  - US1 (Register/login) is the MVP backend slice
  - US2 (Refresh/logout) extends US1's files — sequential after US1, not parallel
  - US3 (Ownership) and US4 (Admin jobs) need only Foundational + US1 (a user to test with) — parallel-safe with US2 (different files)
  - US5 (SPA) needs US1–US4 APIs; CORS edit (T031) must land before browser testing
- **Phase 8 (Polish)**: Depends on all desired stories being complete

### User Story Dependencies

- **US1 (P1)**: After Foundational — no story dependencies
- **US2 (P1)**: After US1 (same files `auth_service.py`, `api/auth.py`)
- **US3 (P2)**: After US1 (needs authenticated users); parallel with US2/US4
- **US4 (P2)**: After US1 (needs admin user); parallel with US2/US3
- **US5 (P3)**: After US1–US4 APIs

### Within Each User Story

- Tests MUST be written and FAIL before implementation
- Schemas/models before services; services before routers
- `main.py` wiring edited once per story that adds a router (T020 auth, T030 admin, T031 CORS) — sequential, small appends

### Parallel Opportunities

- Phase 1: T002, T003 in parallel (different files)
- Phase 2: T004–T011, T013 all in parallel (different files); T012 then T014 sequential (migration order)
- After Foundational: US2, US3, US4 in parallel by file area (auth vs watchlist vs admin) once US1 lands
- US1 tests T015, T016, T017 in parallel; US2 tests T021, T022 in parallel
- US5 frontend T032, T033, T034, T036 in parallel (different files); T035 after T032

---

## Parallel Example: Post-US1 stories (three developers)

```bash
# Developer A (auth sessions, backend/app/services/auth_service.py + api/auth.py):
Task: "T023 Add rotate/logout/logout-all to auth_service.py"
Task: "T024 Add refresh/logout routes to api/auth.py"
# Developer B (ownership, backend/app/services/watchlist_service.py + api/watchlist.py):
Task: "T026 Scope WatchlistService by owner_id"
Task: "T027 Gate api/watchlist.py with get_current_user"
# Developer C (admin, backend/app/api/admin_jobs.py + main.py):
Task: "T029 Create api/admin_jobs.py"
Task: "T030 Wire admin router + delete jobs stub in main.py"
```

---

## Implementation Strategy

### MVP First (US1 + US2 backend auth slice)

1. Complete Phase 1: Setup (deps, config, decision record)
2. Complete Phase 2: Foundational — migrate A → seed admin → migrate B
3. Complete US1: Register/login/me → **STOP and VALIDATE** (quickstart §2)
4. Complete US2: Refresh/logout → **STOP and VALIDATE** (quickstart §3)
5. Deploy/demo: any HTTP client can now authenticate

### Incremental Delivery

1. Setup + Foundational → migration chain proven, admin seeded
2. US1 → Test → Demo (register/login MVP)
3. US2 → Test → Demo (sessions — backend auth complete)
4. US3 → Test → Demo (per-user watchlists; needs data-migration care on existing DBs)
5. US4 → Test → Demo (admin jobs; original motivation)
6. US5 → Test → Demo (SPA; same contract mobile will reuse)
7. Polish → release (CORS already in US5; docs, purge, full gate)

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Deploy-time migration order is load-bearing: rev A (nullable column) → run `seed_admin` → rev B (backfill + NOT NULL)
- `main.py` is touched by T020, T030, T031 — keep each edit a small append; do not parallelize those three
- Commit after each task or logical group; `uv lock` after any `pyproject.toml` change
