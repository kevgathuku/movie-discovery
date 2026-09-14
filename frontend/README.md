# Movie Explorer — Frontend

React + Vite single-page app. Talks to the FastAPI backend with the shared
Bearer-token contract (`Authorization: Bearer <access_token>`, silent refresh;
see `specs/002-user-auth/contracts/client-auth.md`).

## Requirements

- **Node 20+** (`node --version`). The Docker build uses `node:20-alpine`.
- **Backend running** at `http://localhost:8000`
  (`docker compose up -d` from the repo root, plus `TMDB_API_KEY` in `.env`).
- An **admin user** if you want to see the Admin jobs view:
  `ADMIN_EMAIL=… ADMIN_PASSWORD=… docker compose exec api uv run python -m app.seed_admin`

## Getting started

```bash
cd frontend
npm ci            # clean install from package-lock.json (never commit node_modules/)
npm run dev       # → http://localhost:5173, API proxied to :8000 (see vite.config.js)
```

Open the URL, register an account, log in. Admins additionally see an
**Admin jobs** button for background sync history.

### Environment

| Variable             | Default | Description                                  |
|----------------------|---------|----------------------------------------------|
| `VITE_API_BASE_URL`  | `""` (same origin, via dev proxy) | Backend base URL for production builds |

```bash
VITE_API_BASE_URL=https://api.example.com npm run build
```

### Scripts

| Command          | What it does                                  |
|------------------|-----------------------------------------------|
| `npm run dev`    | Dev server with HMR (`:5173`, proxies `/api` + `/admin` to `:8000`) |
| `npm test`       | Vitest suite (API client: refresh, retry, logout) |
| `npm run build`  | Production build into `dist/` (served by nginx in Docker) |
| `npm run preview`| Serve the production build locally            |

## Token storage

- Access token: **memory only** (never `localStorage`).
- Refresh token: **`sessionStorage`** — tab-scoped, cleared on close.
  Survives reloads via silent refresh; close the tab and you log in again.
  (A httpOnly-cookie variant is a documented future option — see `research.md` R4.)

## Troubleshooting

| Symptom | Cause / fix |
|---------|-------------|
| `React is not defined` | `vite.config.js` missing or React plugin not loaded — the plugin enables the automatic JSX runtime. Do not delete it. |
| API calls 404/CORS errors in dev | Backend not running, or wrong port — dev proxy targets `http://localhost:8000`. For a non-proxied setup, set `VITE_API_BASE_URL` and add your origin to backend `CORS_ORIGINS`. |
| 401 on every request after reload | Refresh token expired/revoked (or `sessionStorage` cleared) — log in again. |
| No Admin jobs button | Only `role=admin` users see it (route-guarded in UI, enforced 403 by API). Seed an admin (see Requirements). |
| `npm ci` fails | Rebuild the lockfile with `npm install` and commit the updated `package-lock.json`. |
