# Tasks

## Gate Checks (Required Before Implementation)
- [x] G-001 Confirm `SPEC_READY=true` in `spec.md`
- [x] G-002 Confirm open questions and unresolved alternatives are `0`
- [x] G-003 Confirm required sign-offs are approved
- [x] G-004 Confirm `Applicable Guardrail Controls` section includes `SDD-C-###` IDs
- [x] G-005 Confirm `Implementation Stack Profile` section is fully populated

## Slice-to-Task Mapping

| Slice | Owner | Depends on | Task IDs | Validation IDs |
|---|---|---|---|---|
| S1 Descriptor contract and seed surface | Software Engineer - contract/bootstrap | approved spec and ADR | T-001, T-002 | T-101, T-102, T-201 |
| S2 Descriptor schema, loader, and validation core | Software Engineer - validation/domain | S1 | T-003, T-004 | T-101, T-102, T-104, T-201, T-203 |
| S3 App catalog compatibility rendering and smoke | Software Engineer - app runtime/catalog | S2 | T-005, A-001 | T-105, T-204, T-205 |
| S4 Upgrade diagnostics and advisory artifact | Software Engineer - upgrade pipeline | S2 | T-006, T-007 | T-106, T-107, T-203, T-206 |
| S5 Deprecation tracking and bridge cleanup preparation | Software Engineer - governance/upgrade | S3, S4 | T-008, T-009 | T-108, T-208 |
| S6 Documentation, evidence, and publish preparation | Software Engineer - docs/release | S1, S2, S3, S4, S5 | T-010, T-011, P-001, P-002, P-003 | T-201 through T-210 |

## Implementation
- [x] T-001 Add `apps/descriptor.yaml` to `consumer_seeded` in `blueprint/contract.yaml` and bootstrap mirror.
- [x] T-002 Add `scripts/templates/consumer/init/apps/descriptor.yaml.tmpl` with baseline app/component records.
- [x] T-003 Implement descriptor schema, loader, explicit manifest refs, convention defaults, and safe path resolution.
- [x] T-004 Wire descriptor validation into app runtime GitOps contract validation.
- [x] T-005 Wire descriptor records into deprecated app catalog compatibility rendering and smoke assertions.
- [x] T-006 Emit descriptor ownership evidence in upgrade plan/postcheck diagnostics.
- [x] T-007 Generate `artifacts/blueprint/app_descriptor.suggested.yaml` for existing consumers without the descriptor.
- [x] T-008 Mark `_is_consumer_owned_workload()` as deprecated bridge behavior with two-minor-release removal tracking.
- [x] T-009 Mark `apps/catalog/manifest.yaml` as deprecated generated compatibility output with two-minor-release removal tracking.
- [x] T-010 Update blueprint docs (`docs/blueprint/architecture/execution_model.md` four-layer prune-guard description with `consumer-app-descriptor` ahead of bridge guards + suggested-artifact note; ADR Mermaid `flowchart TD` already in place).
- [x] T-011 Update consumer-facing docs (`docs/platform/consumer/app_onboarding.md` descriptor section + workflow rewrite, `quickstart.md` runtime gitops scaffold + image-binding update, `troubleshooting.md` descriptor validation errors + suggested-artifact migration workflow).

## Test Automation
- [x] T-101 Add unit tests for descriptor schema, app/component ID validation, explicit manifest path validation, and convention default resolution.
- [x] T-102 Add contract tests for `consumer_seeded` template parity and app runtime validation.
- [x] T-103 Confirm no filter/payload-transform route is touched; record not-applicable evidence in `pr_context.md`.
- [x] T-104 Translate deterministic descriptor validation findings into failing tests first, then make them green.
- [x] T-105 Add renderer tests proving deprecated `apps/catalog/manifest.yaml` compatibility output follows descriptor records.
- [x] T-106 Add upgrade plan/postcheck tests for `consumer-app-descriptor` ownership diagnostics.
- [x] T-107 Add suggested descriptor artifact tests for existing generated consumers without `apps/descriptor.yaml`.
- [x] T-108 Add deprecation tracking tests or docs checks for app catalog compatibility output and `_is_consumer_owned_workload()`.

## Validation and Release Readiness
- [x] T-201 Run `make quality-sdd-check`.
- [x] T-202 Run `make quality-hooks-run`.
- [x] T-203 Run `make infra-validate`.
- [x] T-204 Run `make apps-bootstrap`.
- [x] T-205 Run `make apps-smoke`.
- [x] T-206 Run `make blueprint-template-smoke` — pre-existing macOS bash `declare -A` failure in `prune_codex_skills.sh`; reproduces on `main`; unrelated to this change. Recorded in `pr_context.md`.
- [x] T-207 Attach evidence to traceability document.
- [x] T-208 Confirm no stale TODOs/dead code/drift.
- [x] T-209 Run documentation validation (`make docs-build` and `make docs-smoke`).
- [x] T-210 Run hardening review validation bundle (`make quality-hardening-review`).

## Publish
- [x] P-001 Update `hardening_review.md` with repository-wide findings fixed and proposals-only section
- [x] P-002 Update `pr_context.md` with requirement/contract coverage, key reviewer files, validation evidence, and rollback notes
- [x] P-003 Ensure PR description follows repository template headings and references `pr_context.md`

## App Onboarding Minimum Targets (Normative)
- [x] A-001 `apps-bootstrap` and `apps-smoke` are implemented and verified for the affected app scope
- [x] A-002 Backend app lanes (`backend-test-unit`, `backend-test-integration`, `backend-test-contracts`, `backend-test-e2e`) are available
- [x] A-003 Frontend app lanes (`touchpoints-test-unit`, `touchpoints-test-integration`, `touchpoints-test-contracts`, `touchpoints-test-e2e`) are available
- [x] A-004 Aggregate gates (`test-unit-all`, `test-integration-all`, `test-contracts-all`, `test-e2e-all-local`) are available
- [x] A-005 Port-forward operational wrappers (`infra-port-forward-start`, `infra-port-forward-stop`, `infra-port-forward-cleanup`) are available
