# Client Contract: Auth for Web SPA + Mobile

**Date**: 2026-09-14
**Feature**: 002-user-auth

One REST contract serves both clients. No SDK, no per-client auth dialect.

## Rules (both clients)

1. Send `Authorization: Bearer <access_token>` on every authenticated call.
2. Access token lives **in memory** (never `localStorage` on web; never plaintext prefs on mobile — Keychain / Keystore-backed storage for the refresh token).
3. On `401` from any call: single-flight `POST /api/v1/auth/refresh` with the stored refresh token → replace **both** tokens → retry the original request **once**.
4. If refresh itself returns `401`: drop tokens, route to login (web) / login screen (mobile). A `401` from refresh after an app update or device restore is normal — do not retry-loop.
5. Never send `TMDB_API_KEY` or `JWT_SECRET_KEY` from a client. Never log tokens.
6. Concurrent 401s MUST coalesce into one refresh call (single-flight); losers wait for the winner's tokens.

## Web SPA specifics

- Silent refresh on page load if a refresh token is retained (retention mechanism must avoid `localStorage`; implementation detail of the frontend slice).
- `<RequireAuth>` / `<RequireAdmin>` route guards; admin section calls `/admin/jobs` and is hidden for non-admin roles (defense in depth — API still enforces 403).

## Mobile specifics (future `client/`)

- Store refresh token in Keychain (iOS) / EncryptedSharedPreferences or Keystore (Android).
- "Log out" → `POST /auth/logout` + wipe storage. "Log out everywhere" → `POST /auth/logout-all` + wipe storage.
- Queue + single-flight refresh to avoid token stampedes on flaky networks.
