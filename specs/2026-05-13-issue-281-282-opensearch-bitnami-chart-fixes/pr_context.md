# PR Context

## Summary
- Work item: 2026-05-13-issue-281-282-opensearch-bitnami-chart-fixes
- Objective: Add `global.security.allowInsecureImages: true` and `sysctlImage.enabled: false` to the local OpenSearch Helm values seed file and consumer template; add TDD assertions for both keys to prevent regression
- Scope boundaries: Local lane Helm values YAML files and seed file; test module assertions; README documentation; no app delivery scope, no STACKIT lane changes, no HTTP routes, no filter/transform logic

## Requirement Coverage
- Requirement IDs covered: FR-001, FR-002, FR-003, FR-004, FR-005; NFR-SEC-001, NFR-OBS-001, NFR-REL-001, NFR-OPS-001, NFR-A11Y-001
- Acceptance criteria covered: AC-001 (template key present), AC-002 (seed file key present), AC-003 (test assertion allowInsecureImages), AC-004 (artifact mirrors template — satisfied via pass-through rendering), AC-005 (test assertion sysctlImage), AC-006 (test fails before fix), AC-007 (47/47 green after fix), AC-008 (template/seed are source of truth)
- Contract surfaces changed: none — Helm values keys are opaque to the platform contract layer; no new env-var outputs; smoke target assertions unchanged

## Key Reviewer Files
- Primary files to review first:
  - `scripts/templates/infra/bootstrap/infra/local/helm/opensearch/values.yaml` — consumer template with both new keys
  - `infra/local/helm/opensearch/values.yaml` — seed file with both new keys
  - `tests/infra/modules/opensearch/test_opensearch_module.py` — two new test methods (`test_opensearch_seed_values_allow_insecure_images`, `test_opensearch_seed_values_sysctl_image_disabled`)
- High-risk files: none — changes are purely additive YAML key additions and test assertions; no control-flow changes

## Validation Evidence
- Required commands executed: `make quality-hooks-fast` (QUALITY_HOOKS_KEEP_GOING=true), `make infra-validate`, `make docs-build`, `make docs-smoke`, `make quality-hardening-review`, `uv run python3 -m pytest tests/infra/modules/opensearch/test_opensearch_module.py -v`
- Result summary: quality-hooks-fast 9/9 PASS (shellcheck, root-dir-prelude, infra-shell-source-graph, sdd-check-all, spec-pr-ready, ci-check-sync, docs-check-changed, infra-validate, infra-contract-test-fast); pytest 47/47 GREEN; docs-build/smoke PASS; quality-hardening-review PASS
- Artifact references: `specs/2026-05-13-issue-281-282-opensearch-bitnami-chart-fixes/evidence_manifest.json`; `docs/blueprint/architecture/decisions/ADR-issue-281-282-opensearch-bitnami-chart-fixes.md`

## Risk and Rollback
- Main risks: `sysctlImage.enabled: false` disables the sysctl init container — safe for local dev because Docker Desktop pre-sets `vm.max_map_count`; consumers running on bare-metal or non-Docker-Desktop hosts with custom kernel settings must handle `vm.max_map_count` externally (documented in the README compatibility note)
- Rollback strategy: remove `global.security.allowInsecureImages: true` and `sysctlImage.enabled: false` from both values files; revert README additions; revert test methods; YAML-only change with no state side-effects

## Deferred Proposals
- Long-term Bitnami chart 2.x upgrade (not implemented): chart 2.x targets OpenSearch 3.x and is incompatible with the 2.17/2.19 image line; migration requires validating OpenSearch 3.x compatibility with STACKIT managed service plans and consumer applications — Parked — trigger: on-scope: infra — AGENTS.backlog.md entry added
