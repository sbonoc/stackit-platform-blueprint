# ADR: Restore FR-009 source_only Phase 1 + Phase 2 Filter in Stage 3 Contract Resolver

- **Status:** approved
- **ADR technical decision sign-off:** approved
- **Date:** 2026-04-27
- **Issues:** #216
- **Work item:** `specs/2026-04-27-issue-216-upgrade-source-only-filter/`

## Context

The v1.8.0 refactor of `resolve_contract_upgrade.py` simplified Stage 3 by starting with `resolved = source.copy()` and then overriding only `required_files` (FR-006) and `source_artifact_prune_globs_on_init` (FR-007). All other fields, including `spec.repository.ownership_path_classes.source_only`, are taken wholesale from the source contract.

The v1.7.0 resolver had a `_filter_source_only` function implementing FR-009:
- **Phase 1**: drop source `source_only` entries whose paths exist in the consumer repo (prevents `infra-validate` from flagging consumer-owned files as "must be absent")
- **Phase 2**: carry forward consumer-added `source_only` entries (paths in the consumer's contract not in the source's) whose files exist on disk (preserves consumer extensions such as per-ADR enumeration workarounds)

Without this filter, after a v1.8.0 upgrade the consumer's `source_only` becomes the upstream 9-entry list: `tests/blueprint`, `tests/docs`, `specs`, `CLAUDE.md`, `docs/src`, `docs/sidebars.js`, `docs/pnpm-lock.yaml`, `docs/package.json`, `blueprint/modules`. For any consumer that has `specs/`, `CLAUDE.md`, or other commonly-populated paths, the next `make infra-validate` fails with `file must be absent for current repo_mode: <path>` for each conflicting entry.

The dhe-marketplace consumer discovered this during their v1.7.0 → v1.8.0 upgrade and has a manual post-edit workaround in place.

## Decision

Restore `_filter_source_only` semantics inside `resolve_contract_conflict`:

1. Add `_filter_source_only(source_list, consumer_list, repo_root)` → `(merged_list, dropped, kept_consumer)`:
   - Phase 1: for each entry in `source_list`, drop it if `(repo_root / entry).exists()` (the path exists in the consumer).
   - Phase 2: for each entry in `consumer_list` not in `source_list`, carry it forward if `(repo_root / entry).exists()`.
   - Return merged list (filtered source + carried-forward consumer entries), dropped list, and kept-consumer list.

2. Wire the filter into `resolve_contract_conflict` after FR-007, writing the filtered list to `resolved["spec"]["repository"]["ownership_path_classes"]["source_only"]`.

3. Extend `ContractResolveResult` with `dropped_source_only` and `kept_consumer_source_only` for transparency.

4. Extend `contract_resolve_decisions.json` and pipeline stdout logging with the drop/keep counts (mirrors the existing pattern for `required_files` and `prune_globs`).

## Consequences

- Consumers upgrading to v1.8.1+ will have their `source_only` field correctly filtered — no `infra-validate` false positives for consumer-owned paths.
- Consumer-added `source_only` entries (e.g., per-ADR enumeration workarounds for issue #214) are preserved through the upgrade.
- No-conflict consumers (no on-disk path conflicts, no consumer additions) produce an identical result to the current behavior for their entries.
- Phase 1 silently drops a source `source_only` entry if the consumer has a file at that path. This is intentional and matches v1.7.0 semantics. The decision log records all drops.

## Alternatives Considered

**Manual post-edit**: consumers post-edit `blueprint/contract.yaml` after Stage 3 to remove conflicting entries and re-add consumer additions. This is the current workaround — it was rejected as the permanent solution because it imposes ongoing manual maintenance after every upgrade.

## Diagrams

No diagram required — single function addition within an existing script; no new component boundaries.
