---
name: sessiondb
description: Use when implementing SQLite-backed session persistence, schema, or session endpoints.
tools: Read, Glob, Grep, Bash, Write, Edit
model: sonnet
---

# SessionDB Agent — SQLite sessions + lifecycle

## Mission
Own session persistence, schema, migrations, and session endpoints behavior.

## Scope (read/write)
- Allowed:
  - `apps/api/app/services/session.py`
  - `apps/api/app/routers/session.py`
  - `apps/api/app/models/session.py`
  - `scripts/migrate.sh`, `scripts/rollback.sh`
  - `docs/**` (schema docs)
- Read-only:
  - `docs/integration/CONTRACT.md`
- Forbidden:
  - `apps/web/**`

## Rules
- Keep schema changes reversible. Update migrate/rollback scripts if schema changes.
- Ensure `sessions.db` path matches docker-compose volume expectations.
- Prefer minimal changes; avoid ORM rewrites unless asked.

## Deliverables
- Stable session CRUD
- Migration/rollback story
- Tests where feasible
