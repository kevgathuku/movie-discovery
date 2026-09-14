# Data Model: User Auth

**Date**: 2026-09-14
**Feature**: 002-user-auth (extends `001-movie-explorer` data model)

## Entities

### User (NEW)

Account identity. Owns watchlists. Role gates admin access.

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| `id` | BigInteger | PK, auto-increment | Internal identity (matches Movie/Watchlist PK style) |
| `email` | CITEXT (or varchar + `lower()` unique index) | UNIQUE, NOT NULL | Normalized (strip + lowercase) before write/lookup |
| `password_hash` | String(255) | NOT NULL | Argon2id via pwdlib; never plaintext |
| `role` | Enum(`user`, `admin`) | NOT NULL, default `user` | `admin` unlocks `/admin/*` |
| `is_active` | Boolean | NOT NULL, default `true` | `false` rejects auth immediately (logout effect) |
| `created_at` | DateTime(tz) | NOT NULL, default `now()` | |
| `updated_at` | DateTime(tz) | NOT NULL, default `now()`, on update `now()` | |

**Indexes**:
- `uq_users_email` unique on `email` (functional `lower(email)` variant if not CITEXT)
- `ix_users_role` on `role` (admin lookups, partial where `role = 'admin'`)

**Validation rules** (FR-001):
- `email` must parse as an email address (Pydantic `EmailStr`)
- password minimum 8 characters (checked pre-hash; length cap 256 to bound Argon2 work)

### RefreshToken (NEW)

Server-side session record. One row per live session; enables rotation, logout, logout-everywhere.

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| `jti` | UUID | PK | Token family/chunk id; also the lookup key |
| `user_id` | BigInteger | FK → `users.id` ON DELETE CASCADE, NOT NULL | Owner |
| `family_id` | UUID | NOT NULL | Chain id shared across rotations; reuse detection revokes by family |
| `token_hash` | String(64) | UNIQUE, NOT NULL | SHA-256 hex of the opaque token; DB leak yields nothing usable |
| `expires_at` | DateTime(tz) | NOT NULL | 30 days default from issue |
| `revoked_at` | DateTime(tz) | nullable | Set on rotation (replaced), logout, reuse-triggered revocation |
| `created_at` | DateTime(tz) | NOT NULL, default `now()` | |

**Indexes**:
- `uq_refresh_tokens_token_hash` unique on `token_hash`
- `ix_refresh_tokens_user_id` on `user_id`
- `ix_refresh_tokens_family_id` on `family_id`
- Periodic cleanup: delete rows where `expires_at < now()` or (`revoked_at` older than 7 days) — maintenance query, not a cron dependency for correctness since expired tokens are rejected by check.

**State transitions**:
```
live → rotated (revoked_at set, replaced by new jti in same family)
live → revoked  (logout / logout-everywhere / reuse detection / user deactivated)
live → expired  (expires_at passes; rejected on use)
```

### Watchlist (EXTENDED)

| Change | DDL | Notes |
|--------|-----|-------|
| ADD `owner_id` | BigInteger, FK → `users.id` ON DELETE CASCADE | `NOT NULL` after backfill |
| ADD index | `ix_watchlists_owner_id` on `owner_id` | Every watchlist query filters by owner |

**Migration backfill**: `UPDATE watchlists SET owner_id = <seeded admin id> WHERE owner_id IS NULL` before applying `NOT NULL`. Row count before == row count after (SC-006).

**Enforcement rule** (FR-007): every watchlist/entry read or write filters by `(id, owner_id)`; a row owned by another user behaves as if it does not exist → 404 (no existence oracle).

### Job (ACCESS CHANGE ONLY)

No schema change. Read path moves from deleted public `GET /api/v1/jobs/{id}` to admin-gated `GET /admin/jobs[/{id}]`. `JobNotFoundError` → 404 handler added (exception class already exists).

## Relationships

```
User 1 ──── N Watchlist (owner_id, cascade delete)
User 1 ──── N RefreshToken (user_id, cascade delete)
Watchlist 1 ──── N WatchlistEntry (unchanged)
Movie 1 ──── N WatchlistEntry (unchanged)
```

Deleting a user deletes their watchlists (and transitively entries) and all their sessions. Movies are unaffected (shared catalog).

## Enums

```python
class UserRole(str, enum.Enum):
    user = "user"
    admin = "admin"
```

## Design Decisions

1. **BigInteger PK for User**: matches Movie/Watchlist style; sequential internal IDs never exposed as auth material (only `sub` claim inside signed JWT).
2. **Opaque refresh tokens, hashed at rest**: a DB dump must not yield usable sessions. JWTs are used only for short-lived access where revocation is handled by expiry + `is_active` check.
3. **`family_id` for reuse detection**: rotation links new token to the same family; presenting a superseded token proves theft (or a race) → revoke whole family, forcing re-login. Single-flight refresh on clients makes races rare and recoverable.
4. **`is_active` checked per request**: `get_current_user` loads the user by `sub` on every request (one indexed PK fetch), so deactivation takes effect within one access-token lifetime at most, and refresh is blocked immediately.
5. **`owner_id` NOT NULL (not nullable + app check)**: ownership is a data invariant, enforced by the schema (Principle IX), not by convention.
6. **No permissions table**: a two-value `role` enum covers user-vs-admin for this app's size (Principle XVII). A permission system is the documented upgrade path if admin needs granularity later.
