# Implementation Plan

## Implementation Start Gate
- Implementation tasks MUST remain unchecked until `SPEC_READY=true`.
- If required inputs are missing, add `BLOCKED_MISSING_INPUTS` in `spec.md` and keep the gate closed.

## Constitution Gates (Pre-Implementation)
- Simplicity gate: Two targeted changes — one sed loop in bash, one stdlib parser helper in Python. No new abstraction layers.
- Anti-abstraction gate: Direct stdlib `re` parsing; no wrapper classes. No framework dependencies beyond what already exists.
- Integration-first testing gate: Unit tests validate the parser function and the dynamic derivation path before integration with full smoke scenarios.
- Positive-path filter/transform test gate: not applicable — no filter/payload-transform logic. AC-001 covers the positive-path assertion for `validate_app_runtime_conformance()` with consumer-named manifests.
- Finding-to-test translation gate: The CI failure described in the issue (hardcoded names cause `AssertionError` when manifests don't exist) is reproduced by the unit test in Slice 1 that verifies dynamic derivation; the fix turns it green.

## Delivery Slices

### Slice 1 — Tests first (red phase)
1. Add `tests/blueprint/test_template_smoke_assertions.py`:
   - `test_extract_kustomization_resources_parses_resources_section`: verifies `_extract_kustomization_resources` returns correct filenames.
   - `test_extract_kustomization_resources_empty_resources`: verifies empty resources list returns `[]`.
   - `test_extract_kustomization_resources_ignores_non_yaml_entries`: verifies non-.yaml entries are included (parser is not filtering by extension — that is the smoke assertion's responsibility).
2. Extend `tests/blueprint/test_quality_contracts.py`:
   - `test_no_hardcoded_app_manifest_names_in_bootstrap_infra_static_templates`: asserts none of the four seed names appear in the function body.
   These tests fail before the fix is applied.

### Slice 2 — Python fix (green phase for Python)
1. Add `_extract_kustomization_resources(text: str) -> list[str]` to `scripts/lib/blueprint/template_smoke_assertions.py`.
2. Replace the hardcoded `app_manifest_paths` list in `validate_app_runtime_conformance()` with dynamic derivation from the consumer repo's `infra/gitops/platform/base/apps/kustomization.yaml`.
3. Run `pytest tests/blueprint/test_template_smoke_assertions.py` → green.

### Slice 3 — Bash fix (green phase for bash)
1. Replace the four hardcoded `ensure_infra_template_file` calls in `bootstrap_infra_static_templates()` with a `sed`-based `while` loop reading the infra template kustomization.
2. Run `pytest tests/blueprint/test_quality_contracts.py::..::test_no_hardcoded_app_manifest_names_in_bootstrap_infra_static_templates` → green.

### Slice 4 — Validation and hardening
1. Run `make quality-hooks-fast` → green.
2. Run `make infra-validate` → green.
3. Run `make quality-hardening-review` and capture results in `hardening_review.md`.
4. Update `traceability.md` with validation evidence.

## Change Strategy
- Migration/rollout sequence: single PR; no staged rollout required.
- Backward compatibility policy: fully backward compatible. The template kustomization already lists the same filenames that were hardcoded; the dynamic approach produces identical behavior on unmodified consumer repos.
- Rollback plan: `git revert` the PR. No consumer-side action required.

## Validation Strategy (Shift-Left)
- Unit checks: `pytest tests/blueprint/test_template_smoke_assertions.py` and `pytest tests/blueprint/test_quality_contracts.py` (new tests).
- Contract checks: `make quality-hooks-fast`, `make infra-validate`.
- Integration checks: `make blueprint-template-smoke` (runs generated-consumer-smoke scenarios via the CI job).
- E2E checks: none required — the fix is internal tooling; no runtime behavior changes.

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
- Notes: No app delivery workflow, build, or deploy path is modified. These targets are listed for completeness per SDD-C-015; none are introduced or changed by this work item.

## Documentation Plan (Document Phase)
- Blueprint docs updates: none required — no user-facing behavior or contract changes.
- Consumer docs updates: none required — consumers benefit automatically.
- Mermaid diagrams updated: none required.
- Docs validation commands:
  - `make docs-build`
  - `make docs-smoke`

## Publish Preparation
- PR context file: `pr_context.md`
- Hardening review file: `hardening_review.md`
- Local smoke gate (HTTP route/filter changes): not applicable — no HTTP routes affected.
- Publish checklist:
  - include requirement/contract coverage
  - include key reviewer files
  - include validation evidence + rollback notes

## Operational Readiness
- Logging/metrics/traces: no new signals; existing FATAL/error log paths cover the missing template case.
- Alerts/ownership: no changes.
- Runbook updates: none required.

## Risks and Mitigations
- Risk 1: `sed` parser in bash may silently skip valid entries if the kustomization uses unusual YAML formatting → mitigation: template kustomization is blueprint-controlled and always uses minimal flat `resources:` list format; any deviation will cause `ensure_infra_template_file` to not be called (detectable by comparing kustomize build output vs. expected files).
- Risk 2: `_extract_kustomization_resources()` returns empty list if `kustomization.yaml` is missing or malformed → mitigation: `validate_app_runtime_conformance()` MUST raise `AssertionError` when the list is empty and `app_runtime_gitops_enabled=true` (NFR-OBS-001).
