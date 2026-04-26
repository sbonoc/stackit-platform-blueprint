# Tasks

## Gate Checks (Required Before Implementation)
- [ ] G-001 Confirm `SPEC_READY=true` in `spec.md`
- [ ] G-002 Confirm open questions and unresolved alternatives are `0`
- [ ] G-003 Confirm required sign-offs are approved (Architecture, Security, Operations)
- [ ] G-004 Confirm `Applicable Guardrail Controls` section includes `SDD-C-###` IDs
- [ ] G-005 Confirm `Implementation Stack Profile` section is fully populated

## Slice 1 — `blueprint-template-smoke` and `infra-argocd-topology-validate` in VALIDATION_TARGETS
- [x] T-001 Add failing unit test `test_blueprint_template_smoke_in_validation_targets` in `tests/blueprint/test_upgrade_consumer.py`
- [x] T-002 Add failing unit test `test_infra_argocd_topology_validate_in_validation_targets` in `tests/blueprint/test_upgrade_consumer.py`
- [x] T-003 Add `"blueprint-template-smoke"` and `"infra-argocd-topology-validate"` to `VALIDATION_TARGETS` tuple in `scripts/lib/blueprint/upgrade_consumer_validate.py` — both tests turn green

## Slice 2 — `feature_gated` ownership class
- [x] T-004 Add failing unit test: `audit_source_tree_coverage(feature_gated={"apps/catalog"})` does not flag `apps/catalog/manifest.yaml` as uncovered
- [x] T-005 Add `feature_gated: list[str]` field to `RepositoryOwnershipPathClasses` in `scripts/lib/blueprint/contract_schema.py` (default empty list)
- [x] T-006 Add `feature_gated_paths` property to `RepositoryContract` in `contract_schema.py`
- [x] T-007 Parse `feature_gated` from YAML in the schema loader (parallel to `conditional_scaffold`)
- [x] T-008 Add `feature_gated` parameter (default `frozenset()`) to `audit_source_tree_coverage` in `scripts/lib/blueprint/upgrade_consumer.py`; include it in `all_coverage_roots`
- [x] T-009 Update the `audit_source_tree_coverage` call site in `upgrade_consumer.py` to pass `set(contract.repository.feature_gated_paths)`
- [x] T-010 Update `validate_plan_uncovered_source_files` error message to reference `feature_gated`

## Slice 3 — Contract validation for `feature_gated`
- [x] T-011 Add test: a contract dict with `feature_gated: [apps/catalog]` produces no validation errors in `validate_contract.py` ownership section
- [x] T-012 Read and validate `feature_gated` in `scripts/bin/blueprint/validate_contract.py` — no disk-presence check, no equality constraint against `optional_modules`

## Slice 4 — Populate YAML
- [ ] T-013 Add `feature_gated:` list under `ownership_path_classes` in `blueprint/contract.yaml` with `apps/catalog`, `apps/catalog/manifest.yaml`, `apps/catalog/versions.lock`
- [ ] T-014 Mirror identical addition to `scripts/templates/blueprint/bootstrap/blueprint/contract.yaml`
- [ ] T-015 Run `make infra-validate` — passes (AC-004)

## Slice 5 — Fix yaml.dump indentation in resolve_contract_upgrade.py
- [ ] T-018 Add failing unit test `test_resolve_contract_yaml_dump_uses_indented_style` in `tests/blueprint/test_upgrade_pipeline.py`: calls `resolve_contract_conflict` with a long `required_files` entry, asserts the written YAML has no indentless sequences, no wrapped scalars, and is parseable by `load_blueprint_contract`
- [ ] T-019 Add `_IndentedDumper` class and replace bare `yaml.dump(...)` with `yaml.dump(..., Dumper=_IndentedDumper, width=4096)` in `scripts/lib/blueprint/resolve_contract_upgrade.py` — test turns green; pre-existing tests remain green

## Slice 6 — Quality gates and evidence
- [ ] T-016 Run `make quality-hooks-fast` — passes
- [ ] T-017 Capture test output and attach to `traceability.md`

## Validation and Release Readiness
- [ ] T-201 Run required Make validation bundles (`make quality-hooks-fast`, `make infra-validate`)
- [ ] T-202 Attach evidence to traceability document
- [ ] T-203 Confirm no stale TODOs/dead code/drift
- [ ] T-204 Run documentation validation (`make docs-build` and `make docs-smoke`)
- [ ] T-205 Run hardening review validation bundle (`make quality-hardening-review`)

## Publish
- [ ] P-001 Update `hardening_review.md` with repository-wide findings fixed and proposals-only section
- [ ] P-002 Update `pr_context.md` with requirement/contract coverage, key reviewer files, validation evidence, and rollback notes
- [ ] P-003 Ensure PR description follows repository template headings and references `pr_context.md`

## App Onboarding Minimum Targets (Normative)
- App onboarding impact: no-impact — Python/YAML-only changes to upgrade pipeline tooling; no app onboarding surface modified.
- [x] A-001 `apps-bootstrap` and `apps-smoke` — not applicable (no-impact)
- [x] A-002 `backend-test-unit`, `backend-test-integration`, `backend-test-contracts`, `backend-test-e2e` — not applicable (no-impact)
- [x] A-003 `touchpoints-test-unit`, `touchpoints-test-integration`, `touchpoints-test-contracts`, `touchpoints-test-e2e` — not applicable (no-impact)
- [x] A-004 `test-unit-all`, `test-integration-all`, `test-contracts-all`, `test-e2e-all-local` — not applicable (no-impact)
- [x] A-005 `infra-port-forward-start`, `infra-port-forward-stop`, `infra-port-forward-cleanup` — not applicable (no-impact)
