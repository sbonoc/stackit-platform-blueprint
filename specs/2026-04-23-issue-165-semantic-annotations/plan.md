# Implementation Plan

## Implementation Start Gate
- Implementation tasks MUST remain unchecked until `SPEC_READY=true`.
- If required inputs are missing, add `BLOCKED_MISSING_INPUTS` in `spec.md` and keep the gate closed.
- SPEC_READY: true — gate open.

## Constitution Gates (Pre-Implementation)
- Simplicity gate: New module is minimal — pure string diff + regex; no abstraction layers beyond what is needed for testability. `SemanticAnnotation` is a frozen dataclass with three fields.
- Anti-abstraction gate: No new classes or registries. `annotate()` is a single function. Detection patterns are simple conditionals, not a plugin registry.
- Integration-first testing gate: Test contract (AC-001 through AC-007) defined before implementation. Annotator tested in isolation; consumer integration tested against both creation sites.
- Positive-path filter/transform test gate: FR-003 requires detection of at least four change patterns. Each pattern MUST have a positive-path fixture producing a matching `kind` (not structural-change). Empty/fallback-only assertions MUST NOT satisfy coverage.
- Finding-to-test translation gate: Any reproducible failure found during development MUST be captured as a failing test first; fix turns it green in the same work item. No exceptions without documentation in `pr_context.md`.

## Delivery Slices

### Slice 1 — Annotation module (no upstream deps)
- **New file:** `scripts/lib/blueprint/upgrade_semantic_annotator.py`
- Implements:
  - `SemanticAnnotation(kind: str, description: str, verification_hints: tuple[str, ...])` frozen dataclass with `.as_dict()` method.
  - `annotate(baseline_content: str, source_content: str) -> SemanticAnnotation` — main entry point.
  - Detection helpers (each returns `SemanticAnnotation | None`):
    - `_detect_function_added(baseline, source)` — uses `^\s*(?:function\s+(\w+)|(\w+)\s*\(\s*\))` to find function definitions in source absent from baseline; returns first match.
    - `_detect_function_removed(baseline, source)` — inverse of above.
    - `_detect_variable_changed(baseline, source)` — uses `^\s*(\w+)=(.*)` to find assignments whose value differs between baseline and source; returns first match.
    - `_detect_source_directive_added(baseline, source)` — uses `^\s*(?:source|\.)\s+(.+)` to find directives in source absent from baseline; returns first match.
  - Detection order in `annotate()`: function-added → function-removed → variable-changed → source-directive-added → structural-change.
  - Structural-change fallback: `kind="structural-change"`, `description="Structural diff detected — pattern not matched by annotator"`, `verification_hints=("Manually review the diff between baseline ref and upgrade source; verify the merged result is complete and correct.",)`.
  - Special case: `baseline_content=""` (additive file path) → `description="Additive file — no baseline ancestor available for diff analysis"`.
- **Owner:** blueprint maintainer
- **Depends on:** nothing
- **Validation:** `pytest tests/blueprint/test_upgrade_semantic_annotator.py`

### Slice 2 — UpgradeEntry / ApplyResult extension (depends on Slice 1)
- **Modified file:** `scripts/lib/blueprint/upgrade_consumer.py`
- Changes:
  - Add `semantic: SemanticAnnotation | None = None` field to `UpgradeEntry` dataclass (after `baseline_content_available`).
  - Update `UpgradeEntry.as_dict()` to include `"semantic": self.semantic.as_dict() if self.semantic else None`.
  - At 3-way merge creation site (~line 640): call `annotate(baseline_content, source_content)` in a per-entry `try/except Exception`; on exception, use structural-change fallback and `log_warn`.
  - At additive file creation site (~line 606): call `annotate("", source_content)` — annotator returns structural-change by design; wrap in same try/except.
  - After both creation sites are updated, emit one log line per plan generation run: `f"semantic annotator: merge-required={total}, auto={auto_count}, fallback={fallback_count}"`.
  - Add `semantic: SemanticAnnotation | None = None` field to `ApplyResult` dataclass.
  - Update `ApplyResult.as_dict()` to include `"semantic": self.semantic.as_dict() if self.semantic else None`.
  - At both apply sites for merge-required entries (merged and conflict paths, ~lines 1352–1410): pass `semantic=entry.semantic` when constructing `ApplyResult`.
  - Update summary markdown renderer (~lines 1473–1557) to render for each merge-required entry: `semantic.description` on its own line, followed by a bulleted list of `semantic.verification_hints`.
- **Owner:** blueprint maintainer
- **Depends on:** Slice 1
- **Validation:** `pytest tests/blueprint/test_upgrade_consumer.py` (extended cases)

### Slice 3 — JSON schema updates (depends on Slice 2)
- **Modified file:** `scripts/lib/blueprint/schemas/upgrade_plan.schema.json`
  - Add optional `semantic` property to entry `items` object:
    ```json
    "semantic": {
      "type": ["object", "null"],
      "properties": {
        "kind": {"type": "string", "enum": ["function-added", "function-removed", "variable-changed", "source-directive-added", "structural-change"]},
        "description": {"type": "string"},
        "verification_hints": {"type": "array", "items": {"type": "string"}, "minItems": 1}
      },
      "required": ["kind", "description", "verification_hints"]
    }
    ```
- **Modified file:** `scripts/lib/blueprint/schemas/upgrade_apply.schema.json`
  - Add identical optional `semantic` property to result `items` object.
- **Owner:** blueprint maintainer
- **Depends on:** Slice 2
- **Validation:** existing schema-validated tests still pass; updated schema validates against new fixture plan/apply JSON.

### Slice 4 — Test coverage (depends on Slice 1, parallel with Slice 2)
- **New file:** `tests/blueprint/test_upgrade_semantic_annotator.py`
- **New fixtures:** `tests/blueprint/fixtures/semantic_annotator/`
  - `function_added_baseline.sh` — script without `foo`
  - `function_added_source.sh` — same script + `function foo() { echo done; }`
  - `function_removed_baseline.sh` — script with `bar()`
  - `function_removed_source.sh` — same script with `bar()` removed
  - `variable_changed_baseline.sh` — `FOO_VERSION=1.0`
  - `variable_changed_source.sh` — `FOO_VERSION=2.0`
  - `source_directive_baseline.sh` — no source directive
  - `source_directive_source.sh` — adds `source ./helpers.sh`
  - `no_match_baseline.sh` / `no_match_source.sh` — large structural change with no pattern match
- **New cases in:** `tests/blueprint/test_upgrade_consumer.py`
- **Owner:** blueprint maintainer
- **Depends on:** Slice 1 (annotator unit tests); Slice 2 (consumer integration tests)
- **Validation:** all new and existing tests pass green

## Test File Plan

### New: `tests/blueprint/test_upgrade_semantic_annotator.py`

| Test | AC / FR |
|------|---------|
| `test_function_added_detected` | AC-001 |
| `test_function_removed_detected` | FR-002, FR-003 |
| `test_variable_changed_detected` | AC-002 |
| `test_source_directive_added_detected` | FR-003 |
| `test_no_match_returns_structural_change` | AC-003 |
| `test_exception_returns_structural_change` | AC-004 |
| `test_additive_file_empty_baseline_structural_change` | FR-003 (additive path) |
| `test_verification_hints_non_empty` | FR-001 |

### Extended: `tests/blueprint/test_upgrade_consumer.py`

| Test | AC |
|------|----|
| `test_merge_required_3way_entry_has_semantic` | AC-005 |
| `test_merge_required_additive_entry_has_semantic` | AC-005 |
| `test_upgrade_plan_json_includes_semantic` | AC-005 |
| `test_upgrade_summary_renders_semantic_description` | AC-006 |
| `test_upgrade_summary_renders_verification_hints` | AC-006 |
| `test_apply_result_carries_semantic` | AC-007 |

### Fixtures: `tests/blueprint/fixtures/semantic_annotator/`
Shell script pairs covering each detection pattern plus no-match; see Slice 4 above.

## Change Strategy
- Migration/rollout sequence: Slice 1 → Slice 2 + Slice 4 (parallel) → Slice 3 → Slice 5 → Slice 6.
- Backward compatibility policy: `semantic` field is optional (not in `required`) in both JSON schemas. Existing consumers and tooling that ignore unknown fields are unaffected. No existing field values change.
- Rollback plan: Revert this work item entirely. No schema migration, no persistent state, no consumer repo impact.

## Validation Strategy (Shift-Left)

| Layer | Command | Scope |
|-------|---------|-------|
| Unit | `pytest tests/blueprint/test_upgrade_semantic_annotator.py` | Annotator module (Slice 1) |
| Unit/integration | `pytest tests/blueprint/test_upgrade_consumer.py` | Consumer integration (Slice 2+3) |
| Contract/governance | `make quality-sdd-check` | SDD artifact correctness |
| Contract/governance | `make infra-validate` | Full contract validation |
| Quality | `make quality-hooks-run` | Pre-commit hook suite |
| Docs | `make docs-build && make docs-smoke` | Docs correctness (Slice 5) |
| Hardening | `make quality-hardening-review` | Repository-wide hardening (Slice 6) |

No local smoke — no HTTP routes, no K8s, no filter/transform logic in the affected scope.

## App Onboarding Contract (Normative)
- Required minimum make targets:
  - `apps-bootstrap`
  - `apps-smoke`
  - `backend-test-unit`
  - `backend-test-integration`
  - `backend-test-contracts`
  - `backend-test-e2e`
  - `touchpoints-test-unit`
  - `touchpoints-test-integration`
  - `touchpoints-test-contracts`
  - `touchpoints-test-e2e`
  - `test-unit-all`
  - `test-integration-all`
  - `test-contracts-all`
  - `test-e2e-all-local`
  - `infra-port-forward-start`
  - `infra-port-forward-stop`
  - `infra-port-forward-cleanup`
- App onboarding impact: no-impact
- Notes: This work item is confined to blueprint upgrade plan generation tooling. No app delivery paths, no new Make targets, no consumer onboarding surface affected. All listed targets are pre-existing and unaffected.

## Documentation Plan (Document Phase)
- Blueprint docs updates: `docs/blueprint/` upgrade reference docs — document `semantic` annotation field, closed-set `kind` enum values, verification hint format, and structural-change fallback behaviour.
- Consumer docs updates: none (annotation is surfaced in existing artifacts without consumer action).
- Mermaid diagrams updated: ADR diagrams already created; docs page may add an example snippet.
- Docs validation commands:
  - `make docs-build`
  - `make docs-smoke`

## Publish Preparation
- PR context file: `pr_context.md`
- Hardening review file: `hardening_review.md`
- Local smoke gate: not applicable (no HTTP routes, no K8s, no filter/transform logic).
- Publish checklist:
  - include FR-001 through FR-007 and AC-001 through AC-007 coverage mapping
  - include key reviewer files: `upgrade_semantic_annotator.py`, `upgrade_consumer.py` (diff), both schema files, test files
  - include pytest output as validation evidence
  - include rollback notes

## Operational Readiness
- Logging/metrics/traces: One log line per plan run (annotation coverage counts); one warning per fallback exception. No new metrics.
- Alerts/ownership: No new alerting surface. Existing plan generation CI lanes unaffected.
- Runbook updates: Blueprint upgrade reference docs updated (Slice 5 — `semantic` annotation field documented).

## Risks and Mitigations
- Risk 1: Both `merge-required` creation sites must be updated independently; a missed site produces entries without `semantic` → mitigation: test cases explicitly exercise both creation paths (additive file path + 3-way merge path) and assert `semantic` is non-None in both.
- Risk 2: Additive file path passes `baseline_content=""` to annotator — function/variable patterns might match on source-only content, producing misleading annotations for large new files → mitigation: additive path explicitly produces structural-change (annotator short-circuits when baseline is empty) and documents this in the description.
- Risk 3: Schema change breaks existing schema-validated tests → mitigation: `semantic` is optional; no field is added to `required`; existing required fields are preserved; schema-validated tests continue to pass against unchanged required structure.
