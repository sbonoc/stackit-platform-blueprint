# Traceability Matrix

## Requirement-to-Delivery Mapping

| Requirement ID | Control IDs | Design Element | Implementation Path(s) | Test Evidence | Documentation Evidence | Operational Evidence |
|---|---|---|---|---|---|---|
| FR-001 | SDD-C-005, SDD-C-015 | Descriptor ownership class | `blueprint/contract.yaml`; `scripts/templates/blueprint/bootstrap/blueprint/contract.yaml` | contract parity tests | generated contract metadata | `infra-validate` |
| FR-002 | SDD-C-005, SDD-C-015 | Consumer init seed | `scripts/templates/consumer/init/apps.yaml.tmpl` | init template tests | `docs/platform/consumer/quickstart.md` | `blueprint-init-repo` dry-run evidence |
| FR-003 | SDD-C-004, SDD-C-009 | Descriptor schema and path derivation | `scripts/lib/blueprint/*app_descriptor*.py`; schema file | descriptor unit tests | `docs/platform/consumer/app_onboarding.md` | validation stderr |
| FR-004 | SDD-C-009, SDD-C-010, SDD-C-012 | App runtime validation | `scripts/lib/blueprint/contract_validators/app_runtime_gitops.py` | validation tests | troubleshooting docs | `infra-validate` |
| FR-005 | SDD-C-007, SDD-C-015 | App catalog renderer input | `scripts/lib/platform/apps/catalog_scaffold_renderer.py`; `scripts/bin/platform/apps/bootstrap.sh` | renderer tests | quickstart docs | `apps-bootstrap`; `apps-smoke` |
| FR-006 | SDD-C-010, SDD-C-012 | Upgrade diagnostics | `scripts/lib/blueprint/upgrade_consumer.py`; postcheck/report modules | upgrade tests | execution model docs | upgrade plan/postcheck artifacts |
| FR-007 | SDD-C-007, SDD-C-012 | Bridge guard retirement | `scripts/lib/blueprint/upgrade_consumer.py` | prune guard regression tests | ADR | upgrade apply artifact |
| NFR-SEC-001 | SDD-C-009 | Safe YAML and path constraints | descriptor loader | malicious-name tests | app onboarding docs | validation failure artifact |
| NFR-OBS-001 | SDD-C-010 | Deterministic diagnostics | validators and upgrade reporters | stderr/artifact tests | troubleshooting docs | diagnostics output |
| NFR-REL-001 | SDD-C-012 | One-cycle fallback | validators and upgrade flow | absent-descriptor tests | quickstart upgrade notes | upgrade warning evidence |
| NFR-OPS-001 | SDD-C-010, SDD-C-011 | Runbook guidance | docs | docs validation | quickstart/app_onboarding/troubleshooting | operator runbook evidence |
| AC-001 | SDD-C-012 | Consumer-seeded descriptor | contract/template paths | contract parity tests | generated contract metadata | `infra-validate` |
| AC-002 | SDD-C-009 | Unsafe name rejection | descriptor loader | invalid-name unit test | troubleshooting docs | validation stderr |
| AC-003 | SDD-C-012 | Missing derived manifest rejection | app runtime validator | missing-manifest test | troubleshooting docs | validation stderr |
| AC-004 | SDD-C-012 | Kustomization drift rejection | app runtime validator | missing-resource test | troubleshooting docs | validation stderr |
| AC-005 | SDD-C-015 | Descriptor-driven catalog render | catalog renderer | renderer test | quickstart docs | `apps-bootstrap` evidence |
| AC-006 | SDD-C-010 | Descriptor ownership diagnostics | upgrade planner/postcheck | upgrade artifact tests | execution model docs | upgrade plan/postcheck JSON |
| AC-007 | SDD-C-012 | Baseline smoke preservation | template smoke and app smoke | smoke tests | app onboarding docs | `blueprint-template-smoke`; `apps-smoke` |

## Graph Linkage
- Graph file: `graph.json`
- Every `FR-###`, `NFR-*-###`, and `AC-###` listed in this file MUST have a corresponding node in `graph.json`.
- Node IDs referenced:
  - FR-001
  - FR-002
  - FR-003
  - FR-004
  - FR-005
  - FR-006
  - FR-007
  - NFR-SEC-001
  - NFR-OBS-001
  - NFR-REL-001
  - NFR-OPS-001
  - AC-001
  - AC-002
  - AC-003
  - AC-004
  - AC-005
  - AC-006
  - AC-007

## Validation Summary
- Required bundles executed: intake only; `make quality-sdd-check` pending for this draft.
- Result summary: implementation not started; readiness remains blocked on sign-offs.
- Documentation validation:
  - `make docs-build`
  - `make docs-smoke`

## Evidence Manifest
- Manifest file: `evidence_manifest.json`
- Context export: `context_pack.md`
- PR context export: `pr_context.md`
- Hardening review export: `hardening_review.md`

## Open Risks and Follow-Ups
- Follow-up 1: add custom manifest filename support after convention-based descriptor adoption is validated in real consumers.
