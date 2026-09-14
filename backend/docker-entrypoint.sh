#!/bin/sh
set -e
# api, worker and scheduler share this entrypoint and boot concurrently, so on
# a fresh DB they race creating the alembic_version table (UniqueViolation on
# pg_type). Retry until the upgrade succeeds or the winner's table is visible.
attempt=0
until uv run alembic upgrade head; do
  attempt=$((attempt + 1))
  if [ "$attempt" -ge 10 ]; then
    echo "alembic upgrade failed after $attempt attempts" >&2
    exit 1
  fi
  echo "alembic upgrade failed (attempt $attempt), retrying in 2s..." >&2
  sleep 2
done
exec "$@"
