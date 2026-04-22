# Traceability Matrix

## Requirement-to-Delivery Mapping

| Requirement ID | Control IDs | Design Element | Implementation Path(s) | Test Evidence | Documentation Evidence | Operational Evidence |
|---|---|---|---|---|---|---|
| FR-001 | SDD-C-001, SDD-C-002 | best-effort kustomize apply guard | `scripts/bin/platform/auth/reconcile_eso_runtime_secrets.sh` | `RuntimeAuthBestEffortTests::test_eso_kustomize_apply_is_guarded` | `architecture.md` | state file always written |
| FR-002 | SDD-C-001, SDD-C-002 | gho_ token policy change | `scripts/bin/platform/auth/reconcile_argocd_repo_credentials.sh` | `RuntimeAuthBestEffortTests::test_argocd_repo_credentials_accepts_gho_token` | `architecture.md` | status=success for gho_ tokens |
| FR-003 | SDD-C-001, SDD-C-002 | guard preserves required-mode failure | `scripts/bin/platform/auth/reconcile_eso_runtime_secrets.sh` | `RuntimeAuthBestEffortTests::test_eso_kustomize_apply_is_guarded` | `architecture.md` | log_fatal path remains intact |
| NFR-OPS-001 | SDD-C-005 | state file always written | `scripts/bin/platform/auth/reconcile_eso_runtime_secrets.sh` | `RuntimeAuthBestEffortTests::test_eso_kustomize_apply_is_guarded` | `hardening_review.md` | state file written before exit |
| NFR-REL-001 | SDD-C-005 | dry-run mode unaffected | `scripts/bin/platform/auth/reconcile_eso_runtime_secrets.sh` | existing dry-run tests | `hardening_review.md` | dry-run returns 0 |
| AC-001 | SDD-C-012 | warn-and-skip on apply failure with required=false | `scripts/bin/platform/auth/reconcile_eso_runtime_secrets.sh` | `RuntimeAuthBestEffortTests::test_eso_kustomize_apply_is_guarded` | `traceability.md` | status=warn-and-skip |
| AC-002 | SDD-C-012 | failed-required on apply failure with required=true | `scripts/bin/platform/auth/reconcile_eso_runtime_secrets.sh` | `RuntimeAuthBestEffortTests::test_eso_kustomize_apply_is_guarded` | `traceability.md` | status=failed-required |
| AC-003 | SDD-C-012 | gho_ does not trigger reconcile issue | `scripts/bin/platform/auth/reconcile_argocd_repo_credentials.sh` | `RuntimeAuthBestEffortTests::test_argocd_repo_credentials_accepts_gho_token` | `traceability.md` | no issue recorded for gho_ |
| AC-004 | SDD-C-012 | gho_ emits INFO log | `scripts/bin/platform/auth/reconcile_argocd_repo_credentials.sh` | `RuntimeAuthBestEffortTests::test_argocd_repo_credentials_accepts_gho_token` | `traceability.md` | log_info call present |
| AC-005 | SDD-C-012 | structural test for if ! guard | `tests/infra/test_tooling_contracts.py` | `RuntimeAuthBestEffortTests::test_eso_kustomize_apply_is_guarded` | `traceability.md` | assertRegex passes |
| AC-006 | SDD-C-012 | structural test for no gho_ record_reconcile_issue | `tests/infra/test_tooling_contracts.py` | `RuntimeAuthBestEffortTests::test_argocd_repo_credentials_accepts_gho_token` | `traceability.md` | assertNotRegex passes |

## Graph Linkage
- Graph file: `graph.json`
- Every `FR-###`, `NFR-*-###`, and `AC-###` listed in this file MUST have a corresponding node in `graph.json`.
- Node IDs referenced:
  - FR-001, FR-002, FR-003
  - NFR-OPS-001, NFR-REL-001
  - AC-001, AC-002, AC-003, AC-004, AC-005, AC-006

## Validation Summary
- Required bundles executed: `make quality-hooks-fast`, `make quality-hardening-review`, `make infra-contract-test-fast`
- Result summary: all gates green; 99 contract tests passed (was 97, +2 new guard tests)
- Documentation validation:
  - `make docs-build`
  - `make docs-smoke`

## Evidence Manifest
- Manifest file: `evidence_manifest.json`
- Context export: `context_pack.md`
- PR context export: `pr_context.md`
- Hardening review export: `hardening_review.md`

## Open Risks and Follow-Ups
- Follow-up 1: Consider adding retry/wait logic to `run_kustomize_apply` for namespace creation timing (deferred; out of scope for this item).
