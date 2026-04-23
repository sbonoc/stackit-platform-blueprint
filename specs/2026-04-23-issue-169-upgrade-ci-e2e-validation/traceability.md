# Traceability Matrix

## Requirement-to-Delivery Mapping

| Requirement ID | Control IDs | Design Element | Implementation Path(s) | Test Evidence | Documentation Evidence | Operational Evidence |
|---|---|---|---|---|---|---|
| FR-001 | SDD-C-005 | ci_upgrade_validate.sh invokes pytest with --junitxml | `scripts/bin/blueprint/ci_upgrade_validate.sh` | `test_quality_ci_upgrade_validate_target_and_script_exist` (AC-001 assertion) | script body in `ci_upgrade_validate.sh` | n/a |
| FR-002 | SDD-C-005 | quality-ci-upgrade-validate make target invokes ci_upgrade_validate.sh | `make/blueprint.generated.mk`, `scripts/templates/blueprint/bootstrap/make/blueprint.generated.mk.tmpl` | `test_quality_ci_upgrade_validate_target_and_script_exist` (AC-002 assertion) | make target doc comment | n/a |
| FR-003 | SDD-C-005 | render_ci_workflow.py renders upgrade-e2e-validation job on push events | `scripts/lib/quality/render_ci_workflow.py`, `.github/workflows/ci.yml` | `make quality-ci-check-sync` (AC-003, AC-004 assertion) | CI workflow file | CI job visible in GitHub Actions UI |
| FR-004 | SDD-C-005 | quality-ci-sync/check-sync validate complete CI workflow | `scripts/lib/quality/render_ci_workflow.py` via `make quality-ci-check-sync` | `make quality-ci-check-sync` pass | n/a | n/a |
| NFR-SEC-001 | SDD-C-009 | No external network calls; local subprocess only | `scripts/bin/blueprint/ci_upgrade_validate.sh` | `shellcheck --severity=error` pass; structural test | n/a | n/a |
| NFR-OBS-001 | SDD-C-010 | CI job uploads JUnit XML artifact | `.github/workflows/ci.yml` — `upload-artifact` step | `make quality-ci-check-sync` pass | artifact name `upgrade-validate-junit` in CI workflow | JUnit XML visible in Actions UI |
| NFR-REL-001 | SDD-C-012 | set -euo pipefail propagates pytest failures | `scripts/bin/blueprint/ci_upgrade_validate.sh` | `test_quality_ci_upgrade_validate_target_and_script_exist` (`set -euo pipefail` assertion) | n/a | n/a |
| NFR-OPS-001 | SDD-C-012 | make quality-ci-upgrade-validate runnable locally | `make/blueprint.generated.mk` target definition | `make quality-ci-upgrade-validate` local run | make target doc comment | n/a |
| AC-001 | SDD-C-012 | ci_upgrade_validate.sh exists, executable, contains set -euo pipefail | `scripts/bin/blueprint/ci_upgrade_validate.sh` | `test_quality_ci_upgrade_validate_target_and_script_exist` | n/a | n/a |
| AC-002 | SDD-C-012 | quality-ci-upgrade-validate target in both mk files | `make/blueprint.generated.mk`, `scripts/templates/blueprint/bootstrap/make/blueprint.generated.mk.tmpl` | `test_quality_ci_upgrade_validate_target_and_script_exist` | n/a | n/a |
| AC-003 | SDD-C-012 | upgrade-e2e-validation job with push-only condition | `.github/workflows/ci.yml` | `make quality-ci-check-sync` | CI workflow file | n/a |
| AC-004 | SDD-C-012 | upgrade-e2e-validation job uploads JUnit XML | `.github/workflows/ci.yml` | `make quality-ci-check-sync` | CI workflow file | n/a |
| AC-005 | SDD-C-012 | shellcheck passes on ci_upgrade_validate.sh | `scripts/bin/blueprint/ci_upgrade_validate.sh` | `shellcheck --severity=error scripts/bin/blueprint/ci_upgrade_validate.sh` | n/a | n/a |
| AC-006 | SDD-C-012 | Structural test asserts AC-001 and AC-002 | `tests/blueprint/contract_refactor_scripts_cases.py` | pytest pass | n/a | n/a |

## Graph Linkage
- Graph file: `graph.json`
- Every `FR-###`, `NFR-*-###`, and `AC-###` listed in this file MUST have a corresponding node in `graph.json`.
- Node IDs referenced:
  - FR-001
  - FR-002
  - FR-003
  - FR-004
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

## Validation Summary
- Required bundles executed: `make quality-hooks-fast`, `shellcheck --severity=error scripts/bin/blueprint/ci_upgrade_validate.sh`, `python3 -m pytest tests/blueprint/contract_refactor_scripts_cases.py -k ci_upgrade_validate -v`, `make quality-ci-check-sync`
- Result summary: all gates green; structural test passes; shellcheck clean; CI sync check passes
- Documentation validation:
  - `make docs-build`
  - `make docs-smoke`

## Evidence Manifest
- Manifest file: `evidence_manifest.json`
- Context export: `context_pack.md`
- PR context export: `pr_context.md`
- Hardening review export: `hardening_review.md`

## Open Risks and Follow-Ups
- None.
