# Tasks

## Gate Checks (Required Before Implementation)
- [x] G-001 Confirm `SPEC_READY=true` in `spec.md`
- [x] G-002 Confirm open questions and unresolved alternatives are `0`
- [x] G-003 Confirm required sign-offs are approved (sbonoc, 2026-04-23)
- [x] G-004 Confirm `Applicable Guardrail Controls` section includes `SDD-C-###` IDs
- [x] G-005 Confirm `Implementation Stack Profile` section is fully populated

## Slice 1 — Annotation module

- [ ] T-101 Create `tests/blueprint/fixtures/semantic_annotator/function_added_baseline.sh` (script without `foo`)
- [ ] T-102 Create `tests/blueprint/fixtures/semantic_annotator/function_added_source.sh` (same script + `function foo() { echo done; }`)
- [ ] T-103 Create `tests/blueprint/fixtures/semantic_annotator/function_removed_baseline.sh` (script with `bar()`)
- [ ] T-104 Create `tests/blueprint/fixtures/semantic_annotator/function_removed_source.sh` (same script with `bar()` removed)
- [ ] T-105 Create `tests/blueprint/fixtures/semantic_annotator/variable_changed_baseline.sh` (`FOO_VERSION=1.0`)
- [ ] T-106 Create `tests/blueprint/fixtures/semantic_annotator/variable_changed_source.sh` (`FOO_VERSION=2.0`)
- [ ] T-107 Create `tests/blueprint/fixtures/semantic_annotator/source_directive_baseline.sh` (no source directive)
- [ ] T-108 Create `tests/blueprint/fixtures/semantic_annotator/source_directive_source.sh` (adds `source ./helpers.sh`)
- [ ] T-109 Create `tests/blueprint/fixtures/semantic_annotator/no_match_baseline.sh` and `no_match_source.sh` (large structural diff, no pattern match)
- [ ] T-110 Create `scripts/lib/blueprint/upgrade_semantic_annotator.py`:
  - `SemanticAnnotation(kind, description, verification_hints)` frozen dataclass with `.as_dict()`
  - `annotate(baseline_content, source_content) -> SemanticAnnotation`
  - `_detect_function_added`, `_detect_function_removed`, `_detect_variable_changed`, `_detect_source_directive_added` helpers
  - Structural-change fallback; additive-file empty-baseline short-circuit
- [ ] T-111 Create `tests/blueprint/test_upgrade_semantic_annotator.py` with all eight test cases
- [ ] T-112 Verify `pytest tests/blueprint/test_upgrade_semantic_annotator.py` passes (all green, positive-path fixtures for each `kind`)

## Slice 2 — UpgradeEntry / ApplyResult extension

- [ ] T-201 Add `semantic: SemanticAnnotation | None = None` field to `UpgradeEntry` dataclass in `upgrade_consumer.py`
- [ ] T-202 Update `UpgradeEntry.as_dict()` to serialise `semantic` as nested dict (or `null`)
- [ ] T-203 Update 3-way merge creation site (~line 640): call `annotate(baseline_content, source_content)` with per-entry try/except; log warning on exception fallback
- [ ] T-204 Update additive file creation site (~line 606): call `annotate("", source_content)` with per-entry try/except
- [ ] T-205 Emit annotation coverage log line after all entries are built: `merge-required=N, auto=M, fallback=P`
- [ ] T-206 Add `semantic: SemanticAnnotation | None = None` field to `ApplyResult` dataclass
- [ ] T-207 Update `ApplyResult.as_dict()` to serialise `semantic`
- [ ] T-208 Pass `semantic=entry.semantic` when constructing `ApplyResult` at both merge-required apply sites (merged + conflict paths)
- [ ] T-209 Update `upgrade_summary.md` renderer to render `semantic.description` and `semantic.verification_hints` for each merge-required entry
- [ ] T-210 Add consumer test cases for both creation sites and all rendering assertions in `tests/blueprint/test_upgrade_consumer.py`
- [ ] T-211 Verify `pytest tests/blueprint/test_upgrade_consumer.py` passes (all green, including new cases)

## Slice 3 — JSON schema updates

- [ ] T-301 Add optional `semantic` property to entry items in `upgrade_plan.schema.json` (kind enum, description, verification_hints — not in required)
- [ ] T-302 Add optional `semantic` property to result items in `upgrade_apply.schema.json` (same structure)
- [ ] T-303 Verify all existing schema-validated tests still pass
- [ ] T-304 Verify upgraded fixture plan/apply JSON validates against updated schemas

## Slice 4 — Docs update

- [ ] T-401 Update `docs/blueprint/` upgrade reference docs: document `semantic` annotation field, closed-set `kind` enum, verification hint format, structural-change fallback behaviour
- [ ] T-402 Run `make docs-build` and confirm no errors
- [ ] T-403 Run `make docs-smoke` and confirm no errors

## Validation and Release Readiness

- [ ] T-501 Run `make quality-sdd-check` — confirm clean
- [ ] T-502 Run `make quality-hooks-run` — confirm clean
- [ ] T-503 Run `make infra-validate` — confirm clean
- [ ] T-504 Run full test suite: `pytest tests/blueprint/test_upgrade_semantic_annotator.py tests/blueprint/test_upgrade_consumer.py`
- [ ] T-505 Attach pytest output as validation evidence in `traceability.md`
- [ ] T-506 Confirm no stale TODOs or dead code in touched scope
- [ ] T-507 Run `make quality-hardening-review`

## Publish

- [x] P-001 Fill `hardening_review.md` with repository-wide findings fixed, observability changes, proposals-only section
- [x] P-002 Fill `pr_context.md` with: FR-001–FR-007 and AC-001–AC-007 coverage mapping, key reviewer files (`upgrade_semantic_annotator.py`, `upgrade_consumer.py` diff, schema files, test files), pytest validation evidence, rollback notes
- [x] P-003 Ensure PR description follows repository template and references `pr_context.md`

## App Onboarding Minimum Targets (Normative)
- [x] A-001 `apps-bootstrap` and `apps-smoke` are implemented and verified for the affected app scope (no-impact: pre-existing targets unaffected)
- [x] A-002 Backend app lanes (`backend-test-unit`, `backend-test-integration`, `backend-test-contracts`, `backend-test-e2e`) are available (no-impact: pre-existing targets unaffected)
- [x] A-003 Frontend app lanes (`touchpoints-test-unit`, `touchpoints-test-integration`, `touchpoints-test-contracts`, `touchpoints-test-e2e`) are available (no-impact: pre-existing targets unaffected)
- [x] A-004 Aggregate gates (`test-unit-all`, `test-integration-all`, `test-contracts-all`, `test-e2e-all-local`) are available (no-impact: pre-existing targets unaffected)
- [x] A-005 Port-forward operational wrappers (`infra-port-forward-start`, `infra-port-forward-stop`, `infra-port-forward-cleanup`) are available (no-impact: pre-existing targets unaffected)
