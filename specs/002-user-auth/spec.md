# Feature Specification: User Auth

**Feature Branch**: `002-user-auth`

**Created**: 2026-09-14

**Status**: Draft

**Input**: Approved planning output — full user model with JWT authentication serving web SPA (React) and future mobile clients, with role-based admin protection for job status tracking.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Register and log in (Priority: P1)

A new user creates an account with email + password from the web app, then logs in. The app receives a short-lived access token and a rotating refresh token. All subsequent API calls authenticate with the access token.

**Why this priority**: Nothing else works without identity — watchlist ownership, per-user data isolation, and admin gating all depend on authenticated users. This is the MVP slice.

**Independent Test**: Can be fully tested by registering via `POST /api/v1/auth/register`, logging in via `POST /api/v1/auth/login`, and calling an authenticated endpoint (e.g. list my watchlists) with the returned access token.

**Acceptance Scenarios**:

1. **Given** no account exists for `ana@example.com`, **When** she registers with a valid email and a password of 8+ characters, **Then** she receives 201, her password is stored only as a hash, and she can immediately log in.
2. **Given** an existing account, **When** she logs in with the correct password, **Then** she receives an access token (15 min) and a refresh token (30 day), and no password material is returned.
3. **Given** an existing account, **When** she logs in with the wrong password, **Then** she receives 401 with a generic "invalid credentials" message (no hint whether email or password was wrong).
4. **Given** she registers with an already-used email, **When** the request is processed, **Then** she receives 409.
5. **Given** she registers with an invalid email or short password, **When** the request is validated, **Then** she receives 422.

---

### User Story 2 - Stay logged in and log out on any device (Priority: P1)

A logged-in user keeps using the app across sessions without re-entering credentials: the client silently refreshes the access token. She can log out on one device, or log out everywhere ("log out all devices") after losing a phone.

**Why this priority**: Session continuity is core login UX on both web and mobile; revocation is the security counterpart. Ships with US1 as one vertical auth slice.

**Independent Test**: Can be fully tested by logging in, calling `POST /api/v1/auth/refresh` with the refresh token to get a new pair, confirming the old refresh token no longer works (rotation), calling `POST /api/v1/auth/logout`, and confirming the refresh token is rejected afterwards.

**Acceptance Scenarios**:

1. **Given** a valid refresh token, **When** the client calls refresh, **Then** it receives a new access + refresh pair and the old refresh token is invalidated (single use).
2. **Given** an already-rotated (reused) refresh token, **When** it is presented again, **Then** the server rejects it with 401 and revokes the whole token chain for that user (reuse detection).
3. **Given** a logged-in user, **When** she logs out, **Then** her refresh token is revoked and further refresh attempts return 401.
4. **Given** a user who lost a device, **When** she triggers "log out everywhere", **Then** all her refresh tokens are revoked and every device must log in again.

---

### User Story 3 - My watchlists are mine (Priority: P2)

A logged-in user creates watchlists, adds movies, and sees only her own data. Another user cannot see, modify, or delete her watchlists.

**Why this priority**: Converts today's global watchlists into per-user data — the main behavioral change of introducing users. Depends on US1/US2.

**Independent Test**: Can be fully tested by creating two users, having user A create a watchlist, and confirming user B's list is empty and user B gets 404/403 when accessing A's watchlist id.

**Acceptance Scenarios**:

1. **Given** user A is logged in, **When** she creates a watchlist, **Then** it is owned by A and appears in her list.
2. **Given** user A owns watchlist 7, **When** user B requests watchlist 7, **Then** B receives 404 (no existence leak across users).
3. **Given** the migration runs on an existing database, **When** it completes, **Then** all pre-existing watchlists are owned by the seeded admin user and no data is lost.
4. **Given** no access token is supplied, **When** any watchlist endpoint is called, **Then** it returns 401.

---

### User Story 4 - Admin views background job status (Priority: P2)

An admin user opens the admin job view and sees background sync job history (status, progress, errors). Regular users cannot access it, and it does not appear in the public API docs.

**Why this priority**: This is the original motivation (job tracking under an admin interface, not a public endpoint). Depends on US1 for the role mechanism.

**Independent Test**: Can be fully tested by logging in as admin and calling `GET /admin/jobs` + `GET /admin/jobs/{id}`, then repeating as a regular user (403) and anonymously (401).

**Acceptance Scenarios**:

1. **Given** an admin access token, **When** she calls `GET /admin/jobs`, **Then** she receives a paginated job list with status/progress/error info.
2. **Given** an admin access token, **When** she calls `GET /admin/jobs/{id}` for a missing id, **Then** she receives 404.
3. **Given** a non-admin access token, **When** she calls any `/admin/*` endpoint, **Then** she receives 403.
4. **Given** the public OpenAPI schema, **When** inspected, **Then** no `/admin/*` path is listed (hidden docs).
5. **Given** the old public stub, **When** the feature ships, **Then** `GET /api/v1/jobs/{id}` no longer exists.

---

### User Story 5 - Web SPA login session (Priority: P3)

A web user logs in once via the React app and stays logged in across page reloads; admin users see an admin section in the UI.

**Why this priority**: Frontend integration slice; backend already supports it via US1/US2. Lower priority because backend + API contract deliver value to mobile/CLI consumers first.

**Independent Test**: Can be fully tested by logging in through the React app, reloading the page, and confirming the session persists; logging in as admin shows the jobs panel.

**Acceptance Scenarios**:

1. **Given** a logged-in web session, **When** the page reloads, **Then** the user stays logged in (silent refresh, no credential prompt).
2. **Given** an expired access token during a web request, **When** the API wrapper retries after refresh, **Then** the request succeeds transparently.
3. **Given** an admin web session, **When** she navigates to the admin section, **Then** she sees job status history.
4. **Given** a non-admin web session, **When** she navigates to the admin route, **Then** the UI blocks it (route guard) even before the API's 403.

---

### Edge Cases

- What happens when the `Authorization` header is malformed (missing "Bearer" prefix)? → 401, no crash.
- How does the system handle an expired access token? → 401 with `WWW-Authenticate: Bearer`; client refreshes.
- What happens when two refresh requests race with the same token? → Exactly one succeeds; the loser gets 401 and (per reuse policy) the chain is revoked — client must re-login. Documented in client contract.
- How does login behave under brute force? → Auth endpoints are rate-limited; responses stay generic; timing differences minimized.
- What happens when `JWT_SECRET_KEY` is missing at startup? → App fails fast with a clear error, never boots with a default secret.
- What happens to anonymous access for movies/search/import? → Unchanged (still public) unless a later spec says otherwise; only watchlists + admin are gated.
- What happens when a user is deactivated (`is_active=false`)? → Existing access tokens rejected on next request (user loaded per request); refresh tokens revoked.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST allow registration with email + password (email unique, case-insensitive; password minimum 8 characters).
- **FR-002**: System MUST store passwords only as Argon2 (preferred) or bcrypt hashes — never plaintext, never reversible.
- **FR-003**: System MUST issue a short-lived JWT access token (15 min default) and a single-use rotating opaque refresh token (30 day default) on login.
- **FR-004**: System MUST rotate refresh tokens on every use; reuse of a spent token MUST revoke the token chain.
- **FR-005**: System MUST support logout (revoke one token) and logout-everywhere (revoke all user tokens).
- **FR-006**: System MUST authenticate API requests via `Authorization: Bearer <access_token>` (single mechanism for web SPA and mobile).
- **FR-007**: System MUST scope every watchlist to exactly one owning user; cross-user access MUST return 404.
- **FR-008**: System MUST support a `role` of `user` or `admin`; only `admin` may access `/admin/*`.
- **FR-009**: System MUST expose admin job tracking at `GET /admin/jobs` (paginated, filterable by status/type) and `GET /admin/jobs/{id}`, hidden from the public OpenAPI schema.
- **FR-010**: System MUST remove the public `GET /api/v1/jobs/{id}` stub when the admin endpoints ship.
- **FR-011**: System MUST seed or bootstrap exactly one initial admin user (CLI/env, documented; password never logged).
- **FR-012**: System MUST rate-limit auth endpoints (register/login/refresh).
- **FR-013**: System MUST return generic "invalid credentials" on login failure (no email-vs-password oracle).
- **FR-014**: System MUST fail startup fast when `JWT_SECRET_KEY` is unset.
- **FR-015**: Web client MUST persist sessions across reloads via silent refresh and MUST NOT store tokens in `localStorage`.
- **FR-016**: Mobile clients MUST use the same Bearer-token REST contract as web; tokens stored in Keychain (iOS) / Keystore-backed storage (Android).

### Key Entities

- **User**: Account identity — email (unique), password hash, role (`user`|`admin`), `is_active` flag, timestamps. Owns watchlists.
- **RefreshToken**: Server-side session record — `jti`, owning user, token hash (SHA-256 of opaque token), expiry, revocation timestamp. Enables rotation, logout, logout-everywhere.
- **Watchlist (extended)**: Gains `owner_id → users.id` (NOT NULL, cascade delete). Previously global; migration assigns existing rows to the seeded admin.
- **Job (access change only)**: No schema change; read access moves from (removed) public endpoint to admin-only endpoints.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A new user completes register → login → create watchlist in under 2 minutes via the API.
- **SC-002**: Refresh-token reuse is detected and the chain revoked (proven by automated test, 100% of runs).
- **SC-003**: Zero cross-user data leaks: automated tests prove user B cannot read/modify user A's watchlists.
- **SC-004**: Anonymous requests to `/admin/*` get 401, non-admin get 403, admin gets 200 — all covered by tests.
- **SC-005**: Login with wrong password takes effect within the rate limit and never reveals whether the email exists.
- **SC-006**: Existing watchlist rows survive migration with zero loss (row count before == row count after, all owned by seeded admin).

## Assumptions

- Email + password is the only login method in scope; social/OIDC login is explicitly out of scope (would replace this design with code+PKCE against a provider).
- Single shared Bearer-token contract serves both web and mobile; no server sessions, no per-client auth dialects.
- Token transport is header-only (`Authorization: Bearer`) for both clients — no httpOnly-cookie refresh variant in v1.
- Web session persistence uses in-memory access token + silent refresh; exact refresh-token storage on web (httpOnly cookie vs. memory) is an implementation detail as long as `localStorage` is avoided.
- Existing watchlists are transferred to the seeded admin on migration (not wiped).
- Movies, search, and import stay public; only watchlists and admin are gated.
- `TMDB_API_KEY` and `JWT_SECRET_KEY` never reach any client.
- Mobile app does not exist yet (`client/` is empty); this spec defines the contract it will implement.
