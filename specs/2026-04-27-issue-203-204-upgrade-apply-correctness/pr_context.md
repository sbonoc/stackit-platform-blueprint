# PR Context

## Summary
- Work item: 2026-04-27-issue-203-204-upgrade-apply-correctness
- Objective: Fix two correctness bugs in the upgrade apply stage — (1) #203: prune guard only covered `base/apps/`; consumer-renamed manifests in overlay trees (e.g. `environments/local/`) were silently deleted; fixed by `_is_kustomization_referenced` as a third prune guard layer. (2) #204: `git merge-file` can produce byte-identical duplicate Terraform blocks without conflict markers, yielding syntactically invalid `.tf` files; fixed by `_tf_deduplicate_blocks` post-merge scan.
- Scope boundaries: `scripts/lib/blueprint/upgrade_consumer.py`, `scripts/lib/blueprint/schemas/upgrade_apply.schema.json`, test file, schema, and blueprint/consumer documentation only — no infra, no app delivery, no contract.yaml changes.

## Requirement Coverage
- Requirement IDs covered: REQ-001, REQ-002, REQ-003, REQ-004, REQ-005, REQ-006, NFR-SEC-001, NFR-OBS-001, NFR-REL-001, NFR-OPS-001
- Acceptance criteria covered: AC-001 ✓ AC-002 ✓ AC-003 ✓ AC-004 ✓ AC-005 ✓ AC-006 ✓ (all verified by automated tests — see traceability.md for full test-to-AC mapping)
- Contract surfaces changed: `scripts/lib/blueprint/schemas/upgrade_apply.schema.json` — `merged-deduped` added to `result` enum; `tf_dedup_count` and `consumer_kustomization_ref_count` added as required `summary` fields; optional `deduplication_log` array added.

## Key Reviewer Files
- Primary files to review first:
  - `scripts/lib/blueprint/upgrade_consumer.py` — three-layer prune guard stack (`_is_kustomization_referenced` function at ~L231, `_classify_entries` wiring after `_is_consumer_owned_workload`) and Terraform block dedup (`_tf_deduplicate_blocks`, apply loop wiring after `_three_way_merge` for `.tf` paths); main implementation surface for both bugs
  - `scripts/lib/blueprint/schemas/upgrade_apply.schema.json` — schema change that downstream consumers of the apply artifact JSON must be aware of: new enum value and two new required summary counters
  - `tests/blueprint/test_upgrade_consumer.py` — 10 new tests in two new classes (`KustomizationRefPruneGuardTests`, `TerraformBlockDeduplicationTests`); red→green TDD evidence and positive/negative path coverage for all ACs
- High-risk files:
  - `scripts/lib/blueprint/upgrade_consumer.py` — `_classify_entries` branching change is the highest-risk surface: incorrect guard ordering or a logic error here silently deletes consumer-owned files with no immediate failure signal

## Validation Evidence
- Required commands executed: 8 commands — all PASS except one pre-existing failure unrelated to this change (details below)
  - `pytest tests/blueprint/test_upgrade_consumer.py` — PASSED — 83/83 (10 new tests green)
  - `make quality-hardening-review` — PASSED
  - `make quality-sdd-check` — PASSED
  - `make quality-hooks-fast` — PASSED
  - `make infra-validate` — PASSED
  - `make docs-build` — PASSED
  - `make docs-smoke` — PASSED
  - `make quality-docs-check-changed` — PASSED — blueprint template and platform seed mirrors in sync
  - `make blueprint-template-smoke` — PRE-EXISTING FAILURE — `declare -A` bash incompatibility in `prune_codex_skills.sh`; reproduced identically on `main`; unrelated to this change
- Result summary: All quality gates green; 83/83 tests pass; docs build and smoke pass; one pre-existing `blueprint-template-smoke` failure reproduced on `main` and confirmed unrelated

## Risk and Rollback
- Main risks: kustomization.yaml parse errors (guard defaults to unprotected) and Terraform regex edge cases (conflict fallback prevents corrupted output — see details below)
  - `_is_kustomization_referenced` on a malformed `kustomization.yaml` returns `False` (file unprotected). Mitigated by NFR-REL-001: explicit `try/except` + `warning:` to stderr so operators can diagnose.
  - `_TF_BLOCK_RE` regex misses a valid block header edge case. Mitigated by conflict-artifact fallback: on any non-identical duplicate the scanner emits a conflict artifact rather than writing corrupted content to disk.
  - `merged-deduped` is a new `result` enum value; downstream consumers of the apply artifact JSON must handle it. Mitigated by schema update and contract test.
- Rollback strategy: Revert the PR merge commit on `main` (`git revert <merge-sha>`) and push. The prune guard change only activates when `BLUEPRINT_UPGRADE_ALLOW_DELETE=true`; consumers not setting that flag are unaffected. If a consumer already ran the upgrade and a file was incorrectly deleted by a pre-fix blueprint version, restore from git history: `git checkout HEAD~1 -- <path/to/deleted-file>` in the consumer repo, then re-run `make blueprint-upgrade-consumer`. No database or data migration required.

## Deferred Proposals
- none
