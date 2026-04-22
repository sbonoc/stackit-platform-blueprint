# Traceability Matrix

## Requirement-to-Delivery Mapping

| Requirement ID | Control IDs | Design Element | Implementation Path(s) | Test Evidence | Documentation Evidence | Operational Evidence |
|---|---|---|---|---|---|---|
| FR-001 | SDD-C-005, SDD-C-007 | `external-secrets` destination in all AppProject overlays | `infra/gitops/argocd/overlays/*/appproject.yaml` (×4), `scripts/templates/infra/bootstrap/.../appproject.yaml` | `AppProjectNamespacePolicyTests` | ADR | ArgoCD sync result |
| FR-002 | SDD-C-005, SDD-C-012 | Guard test class `AppProjectNamespacePolicyTests` | `tests/infra/test_tooling_contracts.py` | guard fails before fix, passes after | — | `make infra-contract-test-fast` |
| FR-003 | SDD-C-005, SDD-C-012 | Guard covers all five AppProject files | `tests/infra/test_tooling_contracts.py` | `AppProjectNamespacePolicyTests` | — | `make infra-contract-test-fast` |
| NFR-SEC-001 | SDD-C-009 | no new resource kinds in whitelist | `infra/gitops/argocd/overlays/*/appproject.yaml` | test suite clean | — | — |
| NFR-OPS-001 | SDD-C-012 | assertFalse message names file and namespace | `tests/infra/test_tooling_contracts.py` | guard failure message | — | `make infra-contract-test-fast` |
| AC-001 | SDD-C-012 | five AppProject files contain external-secrets destination | five AppProject YAML files | guard test | — | — |
| AC-002 | SDD-C-012 | infra-contract-test-fast passes | test suite | 94 passed, 2 subtests passed | — | `make infra-contract-test-fast` |
| AC-003 | SDD-C-012 | guard fails when external-secrets removed | `tests/infra/test_tooling_contracts.py` | guard pre-fix failure confirmed | — | — |
| AC-004 | SDD-C-012 | infra-validate passes | `scripts/bin/infra/validate.sh` | `make infra-validate` | — | `make infra-validate` |
| AC-005 | SDD-C-007 | AppProject namespace policy resolved | five AppProject YAML files | guard green | ADR | ArgoCD sync |
| AC-006 | SDD-C-007 | platform-local-core health resolves | five AppProject YAML files | — | — | ArgoCD health check |

## Graph Linkage
- Graph file: `graph.json`
- Every `FR-###`, `NFR-*-###`, and `AC-###` listed in this file MUST have a corresponding node in `graph.json`.
- Node IDs referenced:
  - FR-001, FR-002, FR-003
  - NFR-SEC-001, NFR-OPS-001
  - AC-001, AC-002, AC-003, AC-004, AC-005, AC-006

## Validation Summary
- Required bundles executed: all green
- Result summary:
  - `python3 -m pytest tests/infra/test_tooling_contracts.py::AppProjectNamespacePolicyTests -v` → 1 passed (guard red before fix, green after)
  - `make infra-contract-test-fast` → 94 passed, 2 subtests passed
  - `make infra-validate` → contract validation passed
  - `make quality-hooks-fast` → pass
  - `make quality-hardening-review` → pass
- Documentation validation:
  - `make quality-hooks-fast` → pass
  - `make infra-validate` → pass

## Evidence Manifest
- Manifest file: `evidence_manifest.json`
- Context export: `context_pack.md`
- PR context export: `pr_context.md`
- Hardening review export: `hardening_review.md`

## Open Risks and Follow-Ups
- Follow-up 1: optional-module ExternalSecrets (postgres-runtime-credentials, etc.) deployed unconditionally from platform base may still show NotReady when the module is not seeded, keeping platform-local-core Health: Degraded. Tracked in issue #137.
