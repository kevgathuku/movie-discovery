# Tasks: Movie Explorer

**Input**: Design documents from `/specs/001-movie-explorer/`

**Prerequisites**: plan.md, spec.md, data-model.md, contracts/api.md, research.md

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [x] T001 Create backend project structure per implementation plan (backend/app/, backend/tests/, backend/alembic/)
- [x] T002 Initialize Python project with pyproject.toml and dependencies (fastapi, pydantic, sqlalchemy, alembic, httpx, celery, redis, sqids, uvicorn)
- [x] T003 [P] Create backend/app/config.py with pydantic-settings Settings class (TMDB_API_KEY, DATABASE_URL, REDIS_URL from env vars)
- [x] T004 [P] Create backend/app/exceptions.py with domain exceptions (MovieNotFoundError, MovieAlreadyExistsError, WatchlistEntryNotFoundError, WatchlistDuplicateError, JobNotFoundError, ExternalAPIError)
- [x] T005 [P] Create docker-compose.yml with services: api, worker, scheduler, postgres, redis
- [x] T006 [P] Create backend/Dockerfile for API/worker/scheduler
- [x] T007 Create backend/alembic.ini and backend/alembic/env.py configured for async SQLAlchemy

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T008 [P] Create backend/app/models/__init__.py, backend/app/models/movie.py with Movie model (BigInteger PK, tmdb_id, imdb_id, title, release_date, synopsis, genres JSON, rating, poster_url, source enum, timestamps, indexes per data-model.md)
- [x] T009 [P] Create backend/app/models/watchlist.py with Watchlist model (BigInteger PK, name, created_at) and WatchlistEntry model (BigInteger PK, watchlist_id FK, movie_id FK ON DELETE CASCADE, status enum, added_at, watched_at, unique constraint on watchlist_id+movie_id)
- [x] T010 [P] Create backend/app/models/job.py with Job model (String(20) Sqids PK, job_type, status enum, progress, timestamps, error_info JSON, celery_task_id)
- [ ] T011 Generate initial Alembic migration for all four tables (alembic revision --autogenerate)
- [x] T012 [P] Create backend/app/clients/tmdb_client.py with TMDBClient class (httpx.AsyncClient, auth, search, movie details, find by IMDB ID, error handling, retry)
- [x] T013 Create backend/app/dependencies.py with FastAPI DI: get_db (async session yield), get_tmdb_client
- [x] T014 Create backend/app/main.py with create_app factory, lifespan (engine, http client), CORS, router mounting
- [x] T015 [P] Create backend/app/schemas/movie.py with Pydantic schemas (MovieListResponse, MovieDetailResponse, MovieImportRequest — NO source field per clarification)
- [x] T016 [P] Create backend/app/schemas/watchlist.py with Pydantic schemas (WatchlistResponse, WatchlistCreateRequest, WatchlistUpdateRequest, WatchlistEntryResponse, WatchlistEntryCreateRequest, WatchlistEntryUpdateRequest)
- [x] T017 [P] Create backend/app/schemas/job.py with Pydantic schemas (JobResponse)
- [x] T018 [P] Create backend/app/repositories/movie_repo.py with MovieRepository (get_by_id, get_by_tmdb_id, get_by_imdb_id, search by title, list with pagination, create, delete)
- [x] T019 [P] Create backend/app/repositories/watchlist_repo.py with WatchlistRepository (list, get_by_id, create, update_name, delete) and WatchlistEntryRepository (list with filters/sort, get_by_id, get_by_watchlist_and_movie, create, update_status, delete)
- [x] T020 [P] Create backend/app/repositories/job_repo.py with JobRepository (get_by_id, create, update_status, generate Sqids ID)
- [x] T020a Write pytest tests for models, schemas, and repositories (backend/tests/unit/test_models.py, backend/tests/unit/test_schemas.py, backend/tests/unit/test_repositories.py)

**Checkpoint**: Foundation ready — user story implementation can now begin

---

## Phase 3: User Story 1 — Discover Movies (Priority: P1) 🎯 MVP

**Goal**: Users see trending/popular movies on the home page from the local database

**Independent Test**: GET /api/v1/movies returns movies; background sync populates trending data

### Implementation

- [x] T021 [US1] Create backend/app/services/movie_service.py with list_movies(page, per_page) — queries local DB, returns paginated results
- [x] T022 [US1] Create backend/app/services/sync_service.py with sync_trending() — fetches popular movies from TMDB /movie/popular, upserts into local DB (idempotent per Principle IX), creates Job record
- [x] T023 [US1] Create backend/app/api/movies.py with GET /api/v1/movies route — delegates to MovieService, returns MovieListResponse
- [x] T024 [US1] Create backend/app/tasks/sync_tasks.py with sync_trending_movies Celery task — calls SyncService.sync_trending, updates Job lifecycle
- [x] T025 [US1] Configure Celery app in backend/app/tasks/__init__.py with Redis broker, beat schedule (every 6 hours), JSON serialization *(T024 depends on this — not parallel)*
- [x] T026 [US1] Create backend/app/schemas/__init__.py re-exporting all schemas
- [x] T027 [US1] Create backend/app/api/__init__.py registering movies router on /api/v1
- [x] T027a [US1] Write pytest tests for movie_service, sync_service, and API endpoints (backend/tests/unit/test_movie_service.py, backend/tests/integration/api/test_movies.py)

**Checkpoint**: Home page shows trending movies; background sync keeps data current

---

## Phase 4: User Story 2 — Search Movies (Priority: P2)

**Goal**: Users search local DB first; empty results trigger IMDB ID import fallback

**Independent Test**: GET /api/v1/search?q= returns local results; empty results include suggestion

### Implementation

- [ ] T028 [US2] Create backend/app/services/search_service.py with search_movies(query, page, per_page) — local DB title search, returns results with suggestion when empty
- [ ] T029 [US2] Create backend/app/api/search.py with GET /api/v1/search route — validates min 2 chars, delegates to SearchService, returns results or suggestion
- [ ] T029a [US2] Write pytest tests for search_service and API endpoint (backend/tests/unit/test_search_service.py, backend/tests/integration/api/test_search.py)

**Checkpoint**: Search returns local results; empty results prompt IMDB import

---

## Phase 5: User Story 3 — Import by IMDB ID (Priority: P3)

**Goal**: Users import a movie from TMDB by IMDB ID when local search finds nothing

**Independent Test**: POST /api/v1/movies/import with valid IMDB ID returns 201; duplicate returns 409; invalid returns 404

### Implementation

- [ ] T030 [US3] Create backend/app/services/import_service.py with import_movie_by_imdb(imdb_id) — calls TMDBClient.find_by_imdb_id, checks uniqueness (tmdb_id), creates Movie record, returns movie
- [ ] T031 [US3] Add POST /api/v1/movies/import route to backend/app/api/movies.py — validates IMDB ID format, delegates to ImportService, handles 409/404/502
- [ ] T031a [US3] Write pytest tests for import_service and API endpoint (backend/tests/unit/test_import_service.py, backend/tests/integration/api/test_import.py)

**Checkpoint**: IMDB ID import works; duplicate and error cases handled

---

## Phase 6: User Story 4 — Movie Details (Priority: P4)

**Goal**: Users view full metadata for any movie

**Independent Test**: GET /api/v1/movies/{id} returns full detail including synopsis, genres, rating

### Implementation

- [ ] T032 [US4] Add get_movie_detail(movie_id) to backend/app/services/movie_service.py — returns full movie metadata
- [ ] T033 [US4] Add GET /api/v1/movies/{movie_id} route to backend/app/api/movies.py — returns MovieDetailResponse, handles 404
- [ ] T033a [US4] Write pytest tests for movie detail endpoint (backend/tests/integration/api/test_movie_detail.py)

**Checkpoint**: Movie detail view shows all metadata

---

## Phase 7: User Story 5 — Watchlist Management (Priority: P5)

**Goal**: Users create multiple watchlists, add movies to specific watchlists, view lists, mark as watched, remove entries

**Independent Test**: CRUD on /api/v1/watchlists and /api/v1/watchlists/{id}/entries work; duplicate add returns 409; remove doesn't delete movie

### Implementation

- [ ] T034 [US5] Create backend/app/services/watchlist_service.py with create_watchlist(name), list_watchlists(), rename_watchlist(watchlist_id, name), delete_watchlist(watchlist_id), add_to_watchlist(watchlist_id, movie_id), list_watchlist_entries(watchlist_id, status, sort, order, page, per_page), mark_watched(entry_id), remove_from_watchlist(entry_id)
- [ ] T035 [US5] Create backend/app/api/watchlist.py with watchlists and watchlist entries routes — delegates to WatchlistService, handles 404/409
- [ ] T035a [US5] Write pytest tests for watchlist_service and API endpoints (backend/tests/unit/test_watchlist_service.py, backend/tests/integration/api/test_watchlist.py)

**Checkpoint**: Full watchlist CRUD works; idempotent add; remove doesn't delete movie

---

## Phase 8: User Story 6 — Remove Movie from Local Database (Priority: P6)

**Goal**: Users delete a movie's metadata; associated watchlist entries cascade-delete

**Independent Test**: DELETE /api/v1/movies/{id} returns 204; movie and watchlist entry removed

### Implementation

- [ ] T036 [US6] Add delete_movie(movie_id) to backend/app/services/movie_service.py — deletes movie (watchlist cascade via FK), handles not found
- [ ] T037 [US6] Add DELETE /api/v1/movies/{movie_id} route to backend/app/api/movies.py — returns 204, handles 404
- [ ] T037a [US6] Write pytest tests for movie deletion with cascade (backend/tests/integration/api/test_movie_delete.py)

**Checkpoint**: Movie deletion works with cascade

---

## Phase 9: User Story 7 — Job Status Tracking (Priority: P7)

**Goal**: Users check background job status (trending sync, import)

**Independent Test**: GET /api/v1/jobs/{job_id} returns current job state

### Implementation

- [ ] T038 [US7] Create backend/app/services/job_service.py with get_job(job_id) — returns job status, progress, timestamps
- [ ] T039 [US7] Create backend/app/api/jobs.py with GET /api/v1/jobs/{job_id} route — returns JobResponse, handles 404
- [ ] T039a [US7] Write pytest tests for job_service and API endpoint (backend/tests/unit/test_job_service.py, backend/tests/integration/api/test_jobs.py)

**Checkpoint**: Job status polling works

---

## Phase 10: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T040 Add structured logging with request_id, job_id, tmdb_id context (Principle XIX)
- [ ] T041 Add global exception handler in backend/app/main.py mapping domain exceptions to HTTP responses (Principle XX)
- [ ] T042 Create frontend/ project skeleton (package.json, Dockerfile, placeholder components)
- [ ] T043 Run quickstart.md validation scenarios end-to-end
- [ ] T044 Final review: verify all constitution principles are respected

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies — start immediately
- **Phase 2 (Foundational)**: Depends on Phase 1 — BLOCKS all user stories
- **Phase 3–9 (User Stories)**: All depend on Phase 2 completion
  - US1 (Discovery) is the MVP
  - US2 (Search) and US3 (Import) are tightly coupled — implement together
  - US4 (Details) can run in parallel with US2/US3
  - US5 (Watchlist) depends on US3 (needs imported movies to add)
  - US6 (Remove Movie) depends on US5 (needs watchlist entries to cascade)
  - US7 (Jobs) can run in parallel with any story after Phase 2
- **Phase 10 (Polish)**: Depends on all desired stories being complete

### User Story Dependencies

- **US1 (Discovery)**: No story dependencies — MVP entry point
- **US2 (Search)**: No story dependencies — independent
- **US3 (Import)**: No story dependencies — independent
- **US4 (Details)**: No story dependencies — independent
- **US5 (Watchlist)**: Requires US3 (needs import capability to add movies)
- **US6 (Remove Movie)**: Requires US5 (needs watchlist to test cascade)
- **US7 (Jobs)**: No story dependencies — independent

### Parallel Opportunities

- Phase 1: T003, T004, T005, T006 can all run in parallel
- Phase 2: T008, T009, T010 (models) in parallel; T015, T016, T017 (schemas) in parallel; T018, T019, T020 (repos) in parallel
- Phase 3: T021, T022 can run in parallel (different files)
- After Phase 2: US1, US2, US3, US4, US7 can all start in parallel
- After US3: US5 can start; after US5: US6 can start

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL)
3. Complete Phase 3: User Story 1 — Discovery
4. **STOP and VALIDATE**: Trending movies display on home page; background sync runs
5. Deploy/demo if ready

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. US1 (Discovery) → Test → Deploy/Demo (MVP!)
3. US2 + US3 (Search + Import) → Test → Deploy/Demo
4. US4 (Details) → Test → Deploy/Demo
5. US5 (Watchlist) → Test → Deploy/Demo
6. US6 (Remove Movie) → Test → Deploy/Demo
7. US7 (Jobs) → Test → Deploy/Demo
8. Polish → Final release

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
