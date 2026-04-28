# Traceability Matrix

## Requirement-to-Delivery Mapping

| Requirement ID | Control IDs | Design Element | Implementation Path(s) | Test Evidence | Documentation Evidence | Operational Evidence |
|---|---|---|---|---|---|---|
| FR-001 | SDD-C-005, SDD-C-008 | architecture.md § Bounded Contexts § Context A | `blueprint/contract.yaml` `consumer_seeded` list (adds `infra/gitops/platform/base/apps/kustomization.yaml`); `scripts/templates/consumer/init/infra/gitops/platform/base/apps/kustomization.yaml.tmpl` (new); `scripts/lib/blueprint/init_repo_contract.py:seed_consumer_owned_files` (existing loop reseeds the new path) | `tests/blueprint/test_init_repo_descriptor_kustomization_pairing.py::test_force_init_against_consumer_kustomization_passes_validate_app_descriptor` | `docs/blueprint/architecture/decisions/ADR-2026-04-28-issue-230-init-descriptor-kustomization-sync.md` § Decision; `docs/blueprint/upgrade/release_notes.md` v1.8.2 | `make blueprint-template-smoke` exits 0 against the v1.8.0-shaped fixture |
| FR-002 | SDD-C-005, SDD-C-008 | architecture.md § Problem Statement | `scripts/lib/blueprint/init_repo_contract.py:seed_consumer_owned_files` | `tests/blueprint/test_init_repo_descriptor_kustomization_pairing.py` (paired-state assertion) | ADR § Decision | `make blueprint-template-smoke` |
| FR-003 | SDD-C-006, SDD-C-012 | architecture.md § Bounded Contexts § Context D | `scripts/bin/blueprint/template_smoke.sh` and/or `tests/blueprint/fixtures/upgrade_matrix/` extension | smoke fixture exercising v1.8.0-state-shaped consumer kustomization | release notes v1.8.2 entry | `make blueprint-template-smoke` exits 0 |
| FR-004 | SDD-C-012, SDD-C-016 | architecture.md § Non-Functional § Monitoring | CI workflow `make quality-ci-generated-consumer-smoke` | CI run logs (recorded in `pr_context.md`) | release notes v1.8.2 entry | CI lane green |
| NFR-SEC-001 | SDD-C-009 | architecture.md § Non-Functional § Security | `blueprint/contract.yaml` `consumer_seeded` list update | `tests/blueprint/test_contract_init_force_paired_paths_complete.py` | ADR § Decision | `python3 scripts/bin/blueprint/validate_contract.py` exits 0 |
| NFR-OBS-001 | SDD-C-010 | architecture.md § Non-Functional § Observability | existing `apply_file_update`/`ChangeSummary` log lines in `init_repo_contract.py` | unit test inspects `ChangeSummary` log entries for both reseeded paths | release notes v1.8.2 entry | `BLUEPRINT_INIT_FORCE=true make blueprint-init-repo` console output |
| NFR-REL-001 | SDD-C-008 | plan.md § Change Strategy § Rollback | `seed_consumer_owned_files` idempotency invariant | unit test runs force-init twice and asserts no diff on second run | ADR § Decision | `make blueprint-template-smoke` |
| NFR-OPS-001 | SDD-C-016 | plan.md § Change Strategy § Backward compatibility | (no consumer-side action) | smoke fixture proves zero-touch upgrade | release notes v1.8.2 entry | consumer runs `make blueprint-upgrade-consumer && make blueprint-upgrade-consumer-postcheck` exits 0 |
| AC-001 | SDD-C-012 | architecture.md § Bounded Contexts § Context A & D | smoke fixture path | `make blueprint-template-smoke` against the v1.8.0-shaped fixture | release notes | smoke exit 0 |
| AC-002 | SDD-C-012 | architecture.md § Bounded Contexts § Context A | `seed_consumer_owned_files` | `tests/blueprint/test_init_repo_descriptor_kustomization_pairing.py` | ADR | unit test exit 0 |
| AC-003 | SDD-C-012, SDD-C-016 | plan.md § Validation Strategy | CI workflow `make quality-ci-generated-consumer-smoke` + `make blueprint-template-smoke` | CI run IDs (recorded in `pr_context.md`) | release notes v1.8.2 entry | CI lane green |
| AC-004 | SDD-C-005, SDD-C-009 | architecture.md § Non-Functional § Security | `tests/blueprint/test_contract_init_force_paired_paths_complete.py` | unit test exit 0 | ADR § Decision | contract validation exit 0 |

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

## Validation Summary
- Required bundles executed: `make quality-sdd-check` (intake; populated in `pr_context.md` after Step 1); `make infra-validate`, `make blueprint-template-smoke`, `make quality-ci-generated-consumer-smoke` (deferred to Implement / Verify).
- Result summary: pending Implement phase. Intake-only `make quality-sdd-check` result captured in `pr_context.md`.
- Documentation validation:
  - `make docs-build`
  - `make docs-smoke`

## Evidence Manifest
- Manifest file: `evidence_manifest.json`
- Context export: `context_pack.md`
- PR context export: `pr_context.md`
- Hardening review export: `hardening_review.md`

## Open Risks and Follow-Ups
- Follow-up 1: parked proposal `proposal(issue-217): extract _assert_descriptor_kustomization_agreement as shared module helper for future smoke scenario reuse` may be promoted if FR-003's smoke fixture extension introduces a second caller of the cross-check logic. Surface in the publish-phase Deferred Proposals if applicable.
