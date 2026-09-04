# Project Agents

## Architecture Decisions

All architectural decisions are recorded in `docs/decisions.md`. Consult it before making changes that affect test setup, dependency management, or mocking patterns.

## Test Commands

- **Lint**: `uv run ruff check app/ tests/`
- **Tests (host)**: `uv run pytest`
- **Tests (Docker)**: `docker compose exec api uv run pytest`

## Task Completion Checklist

After every code change, before considering the task done:

1. `uv run ruff check app/ tests/` — must pass with zero errors
2. `uv run pytest` — all tests must pass
