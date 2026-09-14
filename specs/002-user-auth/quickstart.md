# Quickstart: User Auth validation

**Feature**: `002-user-auth` | **Date**: 2026-09-14

Validates the feature end-to-end. See `contracts/auth.md`, `contracts/admin-jobs.md`, `contracts/client-auth.md`, and `data-model.md` for details.

## Prerequisites

- `docker compose up postgres redis` (or full stack); backend deps installed (`uv sync --extra dev`).
- Env: `JWT_SECRET_KEY` set to a random 256-bit value (e.g. `openssl rand -hex 32`), `CORS_ORIGINS=http://localhost:5173`, `ADMIN_EMAIL` / `ADMIN_PASSWORD` for seeding.
- API running: `uv run uvicorn app.main:app --port 8000` (from `backend/`).

## 1. Migrate + seed admin

```bash
uv run alembic upgrade head
python -m app.seed_admin   # reads ADMIN_EMAIL / ADMIN_PASSWORD; refuses if admin exists
```

Expected: `users` and `refresh_tokens` tables exist; `watchlists` has `owner_id NOT NULL`; row count of `watchlists` unchanged from before; one `role=admin` user exists.

## 2. Register → login → me (US1)

```bash
curl -s -X POST localhost:8000/api/v1/auth/register \
  -H 'Content-Type: application/json' \
  -d '{"email":"ana@example.com","password":"s3cure-pass"}'          # → 201, no password material
curl -s -X POST localhost:8000/api/v1/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"ana@example.com","password":"s3cure-pass"}'          # → 200 {access_token, refresh_token}
curl -s localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer <access>"                                 # → 200, role=user
curl -s -X POST localhost:8000/api/v1/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"ana@example.com","password":"wrong"}'                # → 401 generic message
```

## 3. Refresh rotation + reuse detection + logout (US2)

```bash
curl -s -X POST localhost:8000/api/v1/auth/refresh \
  -H 'Content-Type: application/json' \
  -d '{"refresh_token":"<R1>"}'                                       # → 200 new pair (R2)
curl -s -X POST localhost:8000/api/v1/auth/refresh \
  -H 'Content-Type: application/json' \
  -d '{"refresh_token":"<R1>"}'                                       # → 401 (R1 spent; family revoked)
curl -s -X POST localhost:8000/api/v1/auth/refresh \
  -H 'Content-Type: application/json' \
  -d '{"refresh_token":"<R2>"}'                                       # → 401 (chain revoked)
# login again → logout with the fresh refresh token → refresh → 401
```

## 4. Watchlist isolation (US3)

```bash
# as ana: create watchlist → 201, id W
# register+login as ben → GET /api/v1/watchlists → empty; GET /api/v1/watchlists/W → 404
# anonymous GET /api/v1/watchlists → 401
```

## 5. Admin jobs gate (US4)

```bash
# login as ADMIN_EMAIL → GET /admin/jobs → 200 paginated list
# GET /admin/jobs/<missing> → 404
# as ana (user): GET /admin/jobs → 403
# anonymous: GET /admin/jobs → 401
# GET /api/v1/jobs/anything → 404 (stub gone)
# GET /openapi.json | grep /admin → no matches (hidden docs)
```

## 6. Automated suite

```bash
uv run ruff check app/ tests/
uv run pytest
```

Expected: zero lint errors; all new tests pass (`test_auth_service`, `test_token_security`, `test_auth`, `test_watchlist_isolation`, `test_admin_jobs`); full pre-existing suite still green.
