# Work Item Context Pack

## Context Snapshot
- Work item: 2026-04-26-issue-208-dynamic-workload-derivation
- Track: blueprint
- SPEC_READY: true
- ADR path: docs/blueprint/architecture/decisions/ADR-2026-04-26-issue-208-dynamic-workload-derivation.md
- ADR status: approved

## Problem Statement
`scripts/bin/infra/bootstrap.sh` · `bootstrap_infra_static_templates()` and `scripts/lib/blueprint/template_smoke_assertions.py` · `validate_app_runtime_conformance()` maintain hardcoded lists of app workload manifest filenames (`backend-api-deployment.yaml`, `backend-api-service.yaml`, `touchpoints-web-deployment.yaml`, `touchpoints-web-service.yaml`). When a consumer renames their workloads, only the template kustomization is updated; the hardcoded lists diverge silently, causing `generated-consumer-smoke` CI failures with no local pre-commit signal.

## Fix Summary
1. `bootstrap.sh`: replace 4 hardcoded `ensure_infra_template_file` calls with a `sed`-based `while` loop reading from `$(bootstrap_templates_root "infra")/infra/gitops/platform/base/apps/kustomization.yaml`.
2. `template_smoke_assertions.py`: add `_extract_kustomization_resources()` stdlib parser; replace hardcoded `app_manifest_paths` with dynamic derivation from consumer's `infra/gitops/platform/base/apps/kustomization.yaml`.

## Guardrail Controls
- Applicable control IDs: SDD-C-001, SDD-C-002, SDD-C-003, SDD-C-004, SDD-C-005, SDD-C-006, SDD-C-007, SDD-C-008, SDD-C-009, SDD-C-010, SDD-C-011, SDD-C-012, SDD-C-016, SDD-C-017, SDD-C-019, SDD-C-020, SDD-C-021, SDD-C-024
- Exceptions: SDD-C-013 (no managed services), SDD-C-014 (no runtime K8s paths), SDD-C-015 (no app onboarding impact), SDD-C-018 (blueprint-source fix), SDD-C-022 (no HTTP routes), SDD-C-023 (no filter/transform logic)

## Related Issues
- GitHub issue: https://github.com/sbonoc/stackit-platform-blueprint/issues/208
- Related: #206 (contract schema), #207 (prune exclusion)

## Key Files
- `scripts/bin/infra/bootstrap.sh` (Bash fix — `bootstrap_infra_static_templates`)
- `scripts/lib/blueprint/template_smoke_assertions.py` (Python fix — `validate_app_runtime_conformance`, new `_extract_kustomization_resources`)
- `scripts/templates/infra/bootstrap/infra/gitops/platform/base/apps/kustomization.yaml` (source of truth)
- `tests/blueprint/test_template_smoke_assertions.py` (new test file)
- `tests/blueprint/test_quality_contracts.py` (extended regression guard)

## Required Commands
- `make quality-sdd-check`
- `make quality-sdd-check-all`
- `make quality-hooks-fast`
- `make quality-hardening-review`
- `make infra-validate`
- `make docs-build`
- `make docs-smoke`
- `make spec-pr-context`

## Artifact Index
- `architecture.md`
- `spec.md`
- `plan.md`
- `tasks.md`
- `traceability.md`
- `graph.json`
- `evidence_manifest.json`
- `pr_context.md`
- `hardening_review.md`
