# PR Context

## Summary
- Work item: issue #277 — ArgoCD health=N/A fix (override ignoreResourceUpdates.all + chart bump to 9.5.13)
- Objective: ArgoCD health status correctly reflects actual pod readiness for all local-lane managed resources; blueprint tracks ArgoCD v3.4.1 (chart 9.5.13).
- Scope boundaries: local-lane Helm values override and version pin only; cloud-lane ArgoCD topology and application-layer code are out of scope.

## Requirement Coverage
- Requirement IDs covered: FR-001, FR-002, FR-003, NFR-OBS-001, NFR-REL-001, NFR-OPS-001
- Acceptance criteria covered: AC-001, AC-002, AC-003, AC-004 (automated); AC-005 (manual — requires live cluster)
- Contract surfaces changed: `infra/local/helm/core/argocd.values.yaml` gains `configs.cm` block; `scripts/lib/infra/versions.sh` and `versions.baseline.sh` pin `ARGOCD_CHART_VERSION=9.5.13`.

## Key Reviewer Files
- Primary files to review first:
  - `infra/local/helm/core/argocd.values.yaml` — the fix (empty-string override)
  - `scripts/templates/infra/bootstrap/infra/local/helm/core/argocd.values.yaml` — bootstrap template carries the same fix
  - `tests/infra/test_argocd_values_health_fix.py` — 4 regression tests covering AC-001/002/003
- High-risk files: `scripts/lib/infra/versions.sh`, `scripts/lib/infra/versions.baseline.sh` — chart version bump; no CRD or API breaking changes in 9.4.16→9.5.13.

## Validation Evidence
- Required commands executed: `uv run python3 -m pytest tests/infra/test_argocd_values_health_fix.py -v`, `make infra-contract-test-fast`, `make test-unit-all`, `make infra-validate`, `make infra-audit-version`, `make docs-build`, `make docs-smoke`, `make quality-hardening-review`
- Result summary: 4/4 regression tests PASS; 68 contract tests PASS; 1009 unit tests PASS; infra-validate PASS; infra-audit-version PASS (reports `ARGOCD_CHART_VERSION=9.5.13`); docs-build PASS; docs-smoke PASS; quality-hardening-review PASS.
- Artifact references: `specs/2026-05-14-issue-277-argocd-health-na/evidence_manifest.json`

## Risk and Rollback
- Main risks: Setting `ignoreResourceUpdates.all: ""` restores status-event processing for all resource types, which can slightly increase ArgoCD reconciliation CPU on large clusters. Not a concern for local Docker Desktop development. No risk of data loss or state migration.
- Rollback strategy: Remove the `configs.cm` block from `argocd.values.yaml` (and bootstrap template), revert `ARGOCD_CHART_VERSION` to `9.4.16` in both `versions.sh` and `versions.baseline.sh`, run `make infra-deploy`. No state migration required.

## Deferred Proposals
- none
