# Project Agents

## MemPalace (Project Memory)

**Always check MemPalace first** before searching the codebase or reading files. Use `mempalace_search` with the `movie_discovery` wing to find existing knowledge about architecture, decisions, patterns, and implementation details.

When you make a **major decision** (architecture, tooling, patterns, conventions), record it in both:
1. `docs/decisions.md` — the source of truth
2. MemPalace — via `mempalace_add_drawer` to `wing: movie_discovery, room: general`

This ensures future sessions can discover context quickly without re-reading every file.

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
