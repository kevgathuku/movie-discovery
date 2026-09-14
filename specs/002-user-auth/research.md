# Research: User Auth

**Feature**: `002-user-auth` | **Date**: 2026-09-14

All technical-context unknowns resolved. No NEEDS CLARIFICATION remains; open product questions (social login, watchlist backfill target, cookie vs header refresh) were decided with documented defaults in `spec.md` Assumptions.

## R1. Password hashing library

- **Decision**: `pwdlib` with the `argon2` extra (`pwdlib[argon2]`), Argon2id at `PasswordHash.recommended()` defaults, wrapped in `backend/app/security/passwords.py`.
- **Rationale**: The project's Python floor is 3.14. `passlib` is unmaintained and broken from Python 3.13 onward; its own ecosystem points at `pwdlib` as the successor. `pwdlib` is the library the official FastAPI security docs recommend, supports Argon2 (PHC winner, memory-hard — best against GPU cracking) and bcrypt, and was last released Aug 2026 (v0.3.1, actively maintained). A thin wrapper keeps the algorithm replaceable per Constitution Principle IV.
- **Alternatives considered**: `passlib` (rejected — unmaintained, breaks on 3.13+); raw `bcrypt` package directly (rejected — no algorithm agility, 72-byte truncation footgun without the sha256 pre-hash variant); `argon2-cffi` directly (viable fallback, but `pwdlib` gives the same primitive with a simpler verify/hash API and Django/Flask hash compatibility for future imports).

## R2. JWT library

- **Decision**: `PyJWT>=2.13` (require ≥2.13; latest verified 2.13.0, May 2026, zero known vulns), HS256, wrapped in `backend/app/security/tokens.py`. Decode MUST always pass `algorithms=["HS256"]` explicitly.
- **Rationale**: `python-jose` — the library older FastAPI tutorials used — has a trail of unpatched security issues through 2026 (open algorithm-confusion, `crit`-header, and JWE padding-oracle reports; irregular maintenance). PyJWT is actively maintained (health score 93/100, 160 maintainers), and versions ≥2.12 fix the `crit`-header validation gap (CVE-2026-32597). HS256 with a 256-bit random server secret is the simplest correct choice for single-issuer first-party tokens; no key rotation infrastructure needed at this scale.
- **Alternatives considered**: `python-jose` (rejected — maintenance/security posture); `authlib` (rejected — 4 critical CVEs in 2026, heavier than needed); third-party wrapper `fastapi-jwt-authlib` (rejected — single-maintainer, couples token handling to a framework-specific API; Principle XVII simplicity); asymmetric RS256 (rejected — only needed when multiple independent verifiers exist; YAGNI).

## R3. Session model: why short access + rotating opaque refresh

- **Decision**: Stateless JWT access token (15 min, claims: `sub=user_id`, `role`, `type=access`, `jti`, `exp`/`iat`) + opaque random refresh token (30 day, `secrets.token_urlsafe(48)`, SHA-256 hash stored server-side in `refresh_tokens`). Rotation on every use; reuse of a spent token revokes the whole chain (family id tracked per chain).
- **Rationale**: Access tokens stay stateless so every API request costs one indexed `users` PK lookup and no session store (Principle XXV). Refresh tokens are opaque + hashed-at-rest so a DB read doesn't yield usable sessions if leaked, unlike storing JWT refresh tokens verbatim. Single-use rotation bounds the window of a stolen refresh token to one use, and reuse detection converts silent theft into a visible revoke-all event. This is the OWASP-aligned standard pattern and works identically for SPA and mobile (one `Authorization: Bearer` mechanism, no cookie/mobile split).
- **Alternatives considered**: Long-lived JWT only (rejected — cannot revoke without a denylist, which reintroduces server state while keeping JWT downsides); server sessions in Redis (rejected — splits web/mobile handling, adds a stateful dependency to every request); sliding rolling sessions (rejected — complicates mobile offline/race behavior for no security gain).

## R4. Token transport: header-only Bearer for both clients

- **Decision**: `Authorization: Bearer <access>` header for all authenticated calls; refresh token sent in the JSON body of `POST /auth/refresh`. No cookie variant in v1.
- **Rationale**: One contract for web and mobile (spec FR-006/FR-016). Cookies would require `allow_credentials` + exact-origin CORS + CSRF protection for web while being useless to mobile — two mechanisms for one job. Header-only keeps the backend uniform; web XSS exposure is mitigated by keeping the access token in memory with a 15-minute lifetime and silent refresh, and by never using `localStorage` (spec FR-015).
- **Alternatives considered**: httpOnly `Secure; SameSite=Lax` refresh cookie for web + body for mobile (rejected for v1 — dual code paths; can be added later without breaking the header contract since refresh-by-body remains).

## R5. Rate limiting for auth endpoints

- **Decision**: `slowapi` (in-process fixed-window limiter, no new infra) on `register` / `login` / `refresh` — e.g. 5/min/IP for login, 10/min/IP for register — returning 429. Document Redis-backed limiting as the upgrade path (`# ponytail: in-process limiter; move to Redis when >1 API replica`).
- **Rationale**: Login/refresh are the brute-force surface; generic error messages alone don't stop online guessing. `slowapi` is the standard FastAPI limiter, zero infrastructure, sufficient for a single-replica personal app. Redis already exists as the Celery broker, so the upgrade path is trivial when replicas arrive.
- **Alternatives considered**: No limiting (rejected — brute-forceable login); custom middleware (rejected — `slowapi` exists, Principle XVII); immediate Redis limiter (rejected — over-engineering for one replica).

## R6. CORS tightening

- **Decision**: Replace `allow_origins=["*"]` with env-driven `CORS_ORIGINS` (comma-separated list, empty default = same-origin only). Keep `allow_credentials=True` only meaningful with explicit origins (browsers reject `*` + credentials anyway).
- **Rationale**: Current wildcard config is incompatible with any credentialed web client and exposes the API to any origin. Mobile apps are unaffected by CORS (non-browser), so this change only constrains browsers — exactly the desired effect. Env-driven list keeps Docker/local/prod differences out of code (Principle XI).
- **Alternatives considered**: Keep `*` (rejected — insecure + breaks credentialed requests); hardcoded origin list (rejected — differs per environment).

## R7. Admin bootstrap without a user table chicken-and-egg

- **Decision**: `python -m app.seed_admin` CLI reading `ADMIN_EMAIL` / `ADMIN_PASSWORD` from env, creating the first `role=admin` user; migration backfills existing `watchlists.owner_id` to that admin. CLI refuses to run if an admin already exists (unless `--force`); password never logged.
- **Rationale**: No login exists yet to create the first admin through the API, and a permanent seed-in-code credential would be a secret-in-repo violation (Principle XI). A one-shot CLI keeps the secret in env, is auditable, and composes with Docker (`docker compose run api ...`) and CI.
- **Alternatives considered**: Auto-create default admin password on boot (rejected — predictable-secret risk); creating admin via public register + manual DB role flip (rejected — error-prone, leaves a window with no admin).

## R8. Email uniqueness and case handling

- **Decision**: `CITEXT` column for `users.email` if the `citext` extension is acceptable in migration, else `varchar` + functional unique index on `lower(email)`; application layer also normalizes (strip + lowercase) before lookup.
- **Rationale**: Prevents `Ana@x.com` vs `ana@x.com` duplicate accounts at the DB level (Principle IX — constraints over app checks) while keeping the app-level normalization as defense in depth.
- **Alternatives considered**: App-level check only (rejected — raceable); case-sensitive unique (rejected — user-confusing duplicates).
