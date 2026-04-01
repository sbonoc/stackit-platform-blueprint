# Zero-Downtime Evolution Contract

This optional contract defines safe expand/migrate/contract rollout behavior for schema, API, and event evolution.

## Enablement
- Contract toggle: `ZERO_DOWNTIME_EVOLUTION_ENABLED`
- Default: `false`
- When disabled: no additional policy checks are enforced.

For existing generated repositories:
1. Upgrade blueprint-managed files.
2. Enable the toggle.
3. Run `make infra-validate` before rollout.

## Lifecycle
Canonical phases:
1. `expand`: add backward-compatible capabilities only.
2. `migrate`: move traffic/data to the new shape.
3. `contract`: remove legacy paths only after overlap windows.

### Non-negotiable baseline
- Destructive changes belong only to `contract`.
- Keep at least one stable release window before destructive removal.
- Maintain rollback checkpoints for every migration step.

## Database Policy
- Expand first (new nullable columns, additive indexes/tables).
- Avoid destructive DDL during mixed-version deployment windows.
- Require explicit contract-phase markers for drop operations.

Recommended marker for destructive SQL:
```sql
-- ZERO_DOWNTIME_CONTRACT_PHASE=contract
ALTER TABLE orders DROP COLUMN legacy_state;
```

## API Policy
- Additive API changes are the default.
- Breaking removals require an explicit deprecation window (`>=2` releases).
- Mixed-version clients must continue working during rollout windows.

## Event Policy
- Keep producer/consumer overlap windows (`>=2` releases).
- Breaking event payload changes require dual-read logic.
- Never mutate existing event version semantics in place.

## Mixed-Version Deployment Guidance
1. Deploy expand-safe schema/API/event changes.
2. Deploy producers that can emit both old/new versions when needed.
3. Deploy consumers that can read both versions.
4. Wait for overlap window and validate metrics/logs.
5. Execute contract cleanup only after window completion.

## Optional Quality Checks
When `ZERO_DOWNTIME_EVOLUTION_ENABLED=true`, validation checks can flag unsafe patterns where feasible:
- `DROP COLUMN` without explicit contract-phase marker.
- `DROP TABLE` without explicit contract-phase marker.
- Event version overwrite patterns without introducing a new event version.

These checks are guardrails, not substitutes for release engineering review.
