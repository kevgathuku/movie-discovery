# API Contracts: Auth

**Date**: 2026-09-14
**Feature**: 002-user-auth

Base URL: `http://localhost:8000/api/v1`. Auth uses `Authorization: Bearer <access_token>` unless noted. Rate-limited: register/login/refresh (429 when exceeded).

---

## POST /api/v1/auth/register (public)

Create an account.

**Request**:

```json
{ "email": "ana@example.com", "password": "s3cure-pass" }
```

**Response 201**:

```json
{
  "id": 1,
  "email": "ana@example.com",
  "role": "user",
  "is_active": true,
  "created_at": "2026-09-14T10:00:00Z"
}
```

**Errors**: `409` email taken · `422` invalid email / password < 8 chars · `429` rate-limited

---

## POST /api/v1/auth/login (public)

**Request**:

```json
{ "email": "ana@example.com", "password": "s3cure-pass" }
```

**Response 200**:

```json
{
  "access_token": "<jwt, 15min>",
  "refresh_token": "<opaque, 30d>",
  "token_type": "bearer",
  "expires_in": 900
}
```

**Errors**: `401` invalid credentials (generic — same for unknown email or wrong password) · `429` rate-limited

---

## POST /api/v1/auth/refresh (public, refresh token in body)

Rotate a refresh token. Single use — the presented token is revoked and a new pair issued.

**Request**:

```json
{ "refresh_token": "<opaque>" }
```

**Response 200**: same shape as login.

**Errors**: `401` invalid / expired / revoked / reused token (reuse also revokes the whole family) · `429` rate-limited

---

## POST /api/v1/auth/logout (authenticated)

Revoke the presented session. Client sends the refresh token to kill:

**Request**:

```json
{ "refresh_token": "<opaque>" }
```

**Response 204**: No content. **Errors**: `401` unauthenticated.

---

## POST /api/v1/auth/logout-all (authenticated)

Revoke ALL sessions for the current user (lost-device case).

**Response 204**: No content. **Errors**: `401` unauthenticated.

---

## GET /api/v1/auth/me (authenticated)

**Response 200**:

```json
{
  "id": 1,
  "email": "ana@example.com",
  "role": "user",
  "is_active": true,
  "created_at": "2026-09-14T10:00:00Z"
}
```

**Errors**: `401` missing/invalid/expired token, or user deactivated.

---

## Access token (JWT, HS256) claims

```json
{
  "sub": "1",
  "role": "user",
  "type": "access",
  "jti": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "iat": 1726310400,
  "exp": 1726311300
}
```

Verification rules: signature with `JWT_SECRET_KEY`, `algorithms=["HS256"]` pinned, `exp` enforced, `type == "access"`, user exists and `is_active`.

## Error response shape

All errors: `{ "detail": "..." }`. New mappings:

| Domain Exception | HTTP |
| ----------------- | ------ |
| `UserAlreadyExistsError` | 409 |
| `InvalidCredentialsError` | 401 (generic message) |
| `TokenRevokedError` / expired / reused | 401 |
| `NotAuthorizedError` (non-admin on `/admin/*`) | 403 |
| `JobNotFoundError` | 404 (new handler; class already exists) |
