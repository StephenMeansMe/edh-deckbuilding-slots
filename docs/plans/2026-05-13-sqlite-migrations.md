# Design: SQLite Schema Migration Pattern

Phase 4.1 hardens `SqliteRepository`'s migration path so existing databases
survive deckslots upgrades. This note documents the pattern future contributors
follow when introducing a schema change (US-022 / #88).

## Pattern

`storage.py` exposes:

- `_MIGRATIONS: list[tuple[int, Callable[[sqlite3.Connection], None]]]` — ordered
  list of `(target_version, upgrade_fn)` pairs. Index 0 is the v0 → v1 upgrade,
  index 1 is v1 → v2, and so on.
- `CURRENT_SCHEMA_VERSION` — derived from `_MIGRATIONS[-1][0]`; it is the latest
  version the app understands.
- `_migrate(conn)` — applies any upgrade whose `target_version > stored_version`
  in order. Each upgrade runs inside its own transaction (commit on success,
  rollback on exception). On a DB whose stored version exceeds
  `CURRENT_SCHEMA_VERSION`, `_migrate` raises `RuntimeError`.

## Adding a v3 migration

```python
# 1. Add the v3 schema script (idempotent DDL).
_SCHEMA_V3 = """
ALTER TABLE decks ADD COLUMN archived INTEGER NOT NULL DEFAULT 0;
"""

# 2. Add the upgrade function.
def _upgrade_to_v3(conn: sqlite3.Connection) -> None:
    conn.executescript(_SCHEMA_V3)

# 3. Append to the migrations list.
_MIGRATIONS.append((3, _upgrade_to_v3))
```

`CURRENT_SCHEMA_VERSION` updates automatically.

## Constraints

- **Idempotency is not required** — `_migrate` only runs each upgrade once
  (`stored_version < target_version`).
- **Backward-incompatible changes are not allowed** without bumping the major
  version of deckslots itself. The current pattern handles additive changes
  (new tables, new nullable / defaulted columns); destructive changes
  (dropping columns, narrowing types) need a release-notes deprecation step.
- **Transaction boundary**: each upgrade runs in a single transaction. If it
  needs to operate on rows that were inserted by a previous upgrade in the
  same `_migrate` call, that data is already committed before the next
  upgrade starts.

## Tests

`tests/test_storage_repository.py::TestSqliteSchemaMigration` covers:

- fresh DB → `schema_version` rows match `CURRENT_SCHEMA_VERSION`
- reopen → no new rows are inserted
- DB stamped at v1 only → reopening applies v1 → current
- DB stamped at `CURRENT_SCHEMA_VERSION + 10` → `RuntimeError`

When you add a v3 migration, add a corresponding test that stamps the DB at
v2 and verifies the v2 → v3 upgrade is applied on the next open.
