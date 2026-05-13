# PR Context

## Summary

Delivers source_exists inference for `blueprint-managed` catch-all conflicts (FR-001–FR-006): when `source_exists=True` and a conflict entry is classified `blueprint-managed`, `_recommended_action()` now returns `take_source` instead of `human_required`, enabling auto-resolution. Safe because PR #290 (issue #270) eliminated consumer-created files in blueprint-tracked directories, making the inference sound. Additionally resolves 29 pre-existing test failures discovered during implementation: (1) a YAML inline-comment parsing bug in `contract_schema.py` (`last_applied_version: ""  # comment` was parsed with the comment string, causing `_resolve_baseline_ref` to return `None` and all 20 `test_upgrade_consumer.py` tests to fail); (2) AC-004 misalignment in one test expecting old `returncode=1` / `status="failure"` behavior; (3) nine stale assertions across `tests/blueprint/` reflecting pipeline ADR changes, file moves, and API evolution. Closes the structural CI gap by adding a `blueprint-test-unit` make target wired into `test-unit-all` so all 953 blueprint tests now run on every PR.

## Requirement Coverage

| Requirement | Implementation | Test Evidence |
|---|---|---|
| FR-001: `blueprint-managed` + `source_exists=True` → `take_source` | `_recommended_action(ownership_class, source_exists)` in `upgrade_consumer.py` (line ~1714) | `test_triage_blueprint_managed_source_exists_true_yields_take_source` |
| FR-002: `blueprint-managed` + `source_exists=False` → `human_required` | same function; default `source_exists=False` preserves pre-existing behaviour | `test_triage_blueprint_managed_source_exists_false_yields_human_required` |
| FR-003: `source_exists` boolean field in every conflict entry | `_write_upgrade_triage()` in `upgrade_consumer.py` (line ~1778) | `test_triage_entry_includes_source_exists_field` |
| FR-004: `reason` field identifies inference basis for promoted entries | `_BLUEPRINT_MANAGED_INFERRED_REASON` constant set in `_write_upgrade_triage()` (line ~1753) | `test_triage_entry_includes_source_exists_field` (reason assertions) |
| FR-005: `upgrade_triage.schema.json` declares `source_exists` as optional boolean | `scripts/lib/blueprint/schemas/upgrade_triage.schema.json` (line ~57) | `tests/infra/test_conflict_triage_issue_265.py` (5 existing triage tests GREEN) |
| FR-006: all other ownership class mappings unchanged | `_RECOMMENDED_ACTION_MAP` in `upgrade_consumer.py` (line ~1697) — unchanged | `test_triage_blueprint_managed_source_exists_false_yields_human_required`; 953/953 full suite PASS |
| NFR-REL-001: no new regressions | all pre-existing callers use default `source_exists=False` | 953 passed, 0 failures after all fixes |
| NFR-REL-002: CI coverage for blueprint tooling | `blueprint-test-unit` target wired into `test-unit-all` → `quality-ci-fast` | `make blueprint-test-unit` 953/953 PASS |
| AC-004: exit 0 on conflicts | confirmed via `test_apply_conflict_creates_artifact_and_writes_conflicts_status` | `returncode=0`, `status="conflicts"` |

## Key Reviewer Files

- Primary files to review first:
  - `scripts/lib/blueprint/upgrade_consumer.py` — `_recommended_action()` and `_write_upgrade_triage()`: two-parameter inference logic and `source_exists` field emission (lines ~1708–1760)
  - `scripts/lib/blueprint/contract_schema.py` — `_strip_inline_comment()` (new) and `_parse_scalar()` (updated): YAML inline-comment fix; root cause of 20 pre-existing failures; escape-aware quote loop handles embedded `\"`
  - `scripts/lib/blueprint/schemas/upgrade_triage.schema.json` — optional `source_exists` boolean property added; schema version unchanged; backward-compatible with existing triage files
  - `tests/blueprint/test_upgrade_consumer.py` — `SourceExistsInferenceTests` (3 new tests for FR-001/FR-002/FR-003) + `test_apply_conflict_creates_artifact_and_writes_conflicts_status` (AC-004 alignment)
  - `scripts/templates/blueprint/bootstrap/make/blueprint.generated.mk.tmpl` + `make/blueprint.generated.mk` — `blueprint-test-unit` target definition and `test-unit-all: blueprint-test-unit` prerequisite wiring
  - `.pre-commit-config.yaml` + `scripts/templates/blueprint/bootstrap/.pre-commit-config.yaml` — `blueprint-test-unit` pre-push hook (both kept in sync; `infra-validate` drift check confirmed clean)

## Validation Evidence

```
uv run python3 -m pytest tests/blueprint/test_upgrade_consumer.py -k "source_exists" -v
  → 3 PASS (SourceExistsInferenceTests)

uv run python3 -m pytest tests/blueprint/ -q
  → 953 passed, 29 subtests passed in 132s  (0 failures)

uv run python3 -m pytest tests/infra/test_conflict_triage_issue_265.py -v
  → 5 PASS (TriageEmissionTests)

make blueprint-test-unit
  → 953 passed, 29 subtests passed in 130s  exit 0

make infra-validate
  → PASS (bootstrap template drift check clean after .pre-commit-config.yaml template sync)

make quality-hooks-fast
  → PASS

make quality-hardening-review
  → PASS

make docs-build && make docs-smoke
  → PASS
```

## Risk and Rollback

- Main risk: a consumer who creates a file under a `blueprint_managed_roots` path with the same relative path as a blueprint source file will have that file auto-overwritten on the next upgrade run. Governed by the existing `blueprint_managed_roots` exclusivity contract (PR #290 prerequisite). No new risk surface introduced.
- `contract_schema.py` change risk: `_strip_inline_comment()` is a pure function; only `_parse_scalar()` calls it; no other code path affected. The only field that previously carried an inline comment (`last_applied_version`) now parses correctly to `""` — all downstream callers that expected an empty string will behave as before.
- `blueprint-test-unit` CI addition risk: adds ~2 min to the `quality-ci-fast` lane. No behavioural change to any existing target; pure addition via Make prerequisite.
- Rollback strategy: revert `_recommended_action` to single-parameter form; revert `_write_upgrade_triage` to exclude `source_exists`; revert schema; revert `_strip_inline_comment`. Revert `blueprint-test-unit` prerequisite in template and generated makefile. Revert pre-push hook additions. No persisted state (triage JSON is regenerated each upgrade run).

## Deferred Proposals

- Proposal 1: Active cleanup of stale consumer-created files in `blueprint_managed_roots` paths that coincidentally match blueprint source paths — Parked — trigger: on-scope: blueprint — `blueprint_managed_roots` exclusivity contract governs this; no new risk introduced by the inference change.
- Proposal 2: Automate `test_pyramid_contract.json` path existence validation to prevent silent drift when files move — Parked — trigger: on-scope: quality — demonstrated by `tests/infra/` → `tests/blueprint/` moves causing 2 of the 9 pre-existing stale failures.
- Proposal 3: `quality-ci-upgrade-validate` runs only on push to main, not PRs — Parked — trigger: on-scope: blueprint — making it a non-blocking PR annotation or required status would close the gap.
