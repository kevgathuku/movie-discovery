# API Contracts: Admin Jobs

**Date**: 2026-09-14
**Feature**: 002-user-auth

Base path `/admin` (no `/api/v1` prefix — deliberately separate namespace). **All endpoints require `admin` role** (`require_admin` dependency): anonymous → `401`, non-admin → `403`. **Hidden from OpenAPI** (`include_in_schema=False` on the router). Replaces the deleted public stub `GET /api/v1/jobs/{id}`.

---

## GET /admin/jobs (admin)

Paginated job history, newest first.

**Query parameters**:

| Parameter | Type | Default | Notes |
| ----------- | ------ | --------- | ------- |
| `status` | string | — | Filter: `queued`, `processing`, `completed`, `failed` |
| `job_type` | string | — | Filter, e.g. `sync_trending` |
| `page` | int | 1 | |
| `per_page` | int | 20 | Max 100 |

**Response 200**:

```json
{
  "jobs": [
    {
      "id": "Xb3nK9",
      "job_type": "sync_trending",
      "status": "completed",
      "progress": 100,
      "created_at": "2026-09-14T10:00:00Z",
      "started_at": "2026-09-14T10:00:01Z",
      "completed_at": "2026-09-14T10:02:30Z",
      "error_info": null
    }
  ],
  "total": 42,
  "page": 1,
  "per_page": 20
}
```

---

## GET /admin/jobs/{job_id} (admin)

**Response 200**: single job object (same shape as list items).

**Errors**: `404` job not found · `401`/`403` per above.
