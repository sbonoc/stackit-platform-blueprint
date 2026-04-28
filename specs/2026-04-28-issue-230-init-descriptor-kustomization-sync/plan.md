# Implementation Plan

## Implementation Start Gate
- Implementation tasks MUST remain unchecked until `SPEC_READY=true`.
- If required inputs are missing, add `BLOCKED_MISSING_INPUTS` in `spec.md` and keep the gate closed.
- This work item is currently `SPEC_READY=false` pending Product/Architecture/Security/Operations sign-off. Q-1 (option selection) was resolved on PR #231: **Option A** selected.

## Constitution Gates (Pre-Implementation)
- Simplicity gate:
  - Keep the fix scoped to the smallest surface that satisfies FR-001 — one new entry in `blueprint/contract.yaml` (`infra/gitops/platform/base/apps/kustomization.yaml` added to `consumer_seeded`), one new consumer-init template mirroring the bootstrap kustomization, and the existing `seed_consumer_owned_files` loop reseeding the new path automatically.
  - No speculative wrapper helpers, no new env vars, no new make targets.
- Anti-abstraction gate:
  - Reuse the existing `apply_file_update` / `render_template` primitives in `scripts/lib/blueprint/init_repo_contract.py`. Do NOT introduce a new "paired-seed" abstraction layer for the single descriptor↔kustomization pair.
  - Keep contract scope declarative in `blueprint/contract.yaml`; do not introduce a new YAML key unless `consumer_seeded` semantics genuinely cannot accommodate the kustomization path (decision deferred to implementation slice 1).
- Integration-first testing gate:
  - The reproducer fixture (consumer-shaped kustomization with non-demo apps) MUST exist as a `pytest` fixture before the fix is written (T-104, AC-002).
  - The smoke-level fixture extension (FR-003) MUST be in place before the implementation slice is signed off; smoke MUST fail in red, then pass in green.
- Positive-path filter/transform test gate:
  - Not directly applicable — no filter/payload-transform logic changes. Validator and smoke assertion already have positive-path coverage from PR #228.
- Finding-to-test translation gate:
  - The reproducer steps in issue #230 (run `blueprint-upgrade-consumer-postcheck` against a v1.8.0-state consumer; observe 4 `manifest filename not listed` errors) MUST be encoded as failing automated tests first (one unit-level, one smoke-level), and the fix MUST turn both green in the same work item.

## Delivery Slices
1. Slice 1 — **Reproducer red-state**: add unit test `tests/blueprint/test_init_repo_descriptor_kustomization_pairing.py::test_force_init_against_consumer_kustomization_passes_validate_app_descriptor` that builds a temp repo with the descriptor template + a non-demo kustomization (e.g. `marketplace-deployment.yaml`/`marketplace-service.yaml`), runs the init force-reseed, then asserts `validate_app_descriptor` returns `[]`. The test MUST FAIL before the fix is implemented (proves the reproducer is wired). Add a smoke-level fixture under `tests/blueprint/fixtures/upgrade_matrix/` (or extend `template_smoke.sh`) that exercises the same v1.8.0-shaped consumer kustomization scenario via `make blueprint-template-smoke`.
2. Slice 2 — **Apply Option A**: add `infra/gitops/platform/base/apps/kustomization.yaml` to the `consumer_seeded` list in `blueprint/contract.yaml` (or to a new `init_force_paired` list if implementation review prefers explicit semantics — implementation-time decision) and add a new consumer-init template at `scripts/templates/consumer/init/infra/gitops/platform/base/apps/kustomization.yaml.tmpl` that mirrors `scripts/templates/infra/bootstrap/infra/gitops/platform/base/apps/kustomization.yaml`. The existing `seed_consumer_owned_files` loop in `scripts/lib/blueprint/init_repo_contract.py` then naturally reseeds the kustomization on force, with no new helper layer. MUST turn the Slice 1 unit test green and MUST satisfy the smoke-level fixture.
3. Slice 3 — **Contract drift guard + docs**: add a unit test asserting the on-disk init scope listed in `blueprint/contract.yaml` covers every path the init force-reseed actually writes (AC-004). Update `docs/blueprint/upgrade/release_notes.md` (v1.8.2 entry — root cause, fix, no consumer action required). Promote ADR `Status: proposed` → `Status: approved` once Architecture sign-off lands.

## Change Strategy
- Migration/rollout sequence: blueprint patch release (v1.8.2 or v1.8.1.1) → consumer runs `make blueprint-upgrade-consumer && make blueprint-upgrade-consumer-postcheck` → smoke and postcheck pass → consumer drops the `continue-on-error: true` workaround from their CI workflow.
- Backward compatibility policy: the fix is fully backward-compatible — no consumer-side action required (NFR-OPS-001). The paired reseed only fires when `BLUEPRINT_INIT_FORCE=true` is explicitly set; consumer-edited descriptors and kustomizations are untouched on standard upgrades.
- Rollback plan: revert the work-item commits — the validator and smoke assertion remain in place and the failure mode reverts to the pre-fix `infra-validate` 4-error state, which is the documented v1.8.1 baseline.

## Validation Strategy (Shift-Left)
- Unit checks: `pytest tests/blueprint/test_init_repo_descriptor_kustomization_pairing.py` (AC-002), `pytest tests/blueprint/test_contract_init_force_paired_paths_complete.py` (AC-004).
- Contract checks: `python3 scripts/bin/blueprint/validate_contract.py --contract-path blueprint/contract.yaml` (zero errors); `make quality-sdd-check` (zero violations).
- Integration checks: `make blueprint-template-smoke` against the new v1.8.0-shaped fixture (FR-003) — exits 0.
- E2E checks: `make quality-ci-generated-consumer-smoke` — exits 0 in CI (AC-003 / FR-004). No browser-level e2e applicable.

## App Onboarding Contract (Normative)
- Required minimum make targets:
  - `apps-bootstrap`
  - `apps-smoke`
  - `backend-test-unit`
  - `backend-test-integration`
  - `backend-test-contracts`
  - `backend-test-e2e`
  - `touchpoints-test-unit`
  - `touchpoints-test-integration`
  - `touchpoints-test-contracts`
  - `touchpoints-test-e2e`
  - `test-unit-all`
  - `test-integration-all`
  - `test-contracts-all`
  - `test-e2e-all-local`
  - `infra-port-forward-start`
  - `infra-port-forward-stop`
  - `infra-port-forward-cleanup`
- App onboarding impact: no-impact — this work item changes blueprint init/template seeding only; no app-onboarding make-target surface change. (If Option B is selected, `docs/platform/consumer/app_onboarding.md` MUST be updated to reflect the empty-descriptor starting state, but the make-target contract above is unchanged.)
- Notes: Option B's documentation impact is informative, not a contract change to the onboarding make-target list.

## Documentation Plan (Document Phase)
- Blueprint docs updates: `docs/blueprint/upgrade/release_notes.md` (v1.8.2 entry that explicitly notes the expanded force-init blast radius); `docs/blueprint/architecture/decisions/ADR-2026-04-28-issue-230-init-descriptor-kustomization-sync.md` (proposed → approved).
- Consumer docs updates: none required (init behaviour change is a paired-reseed scope detail, not a consumer-facing contract).
- Mermaid diagrams updated: `docs/blueprint/architecture/decisions/ADR-2026-04-28-issue-230-init-descriptor-kustomization-sync.md` includes a `flowchart TD` of the init → bootstrap → validate sequence with both pre-fix (red edges) and post-fix (green edges) states.
- Docs validation commands:
  - `make docs-build`
  - `make docs-smoke`

## Publish Preparation
- PR context file:
  - `pr_context.md`
- Hardening review file:
  - `hardening_review.md`
- Local smoke gate (HTTP route/filter changes):
  - Not applicable — no HTTP route/filter/new-endpoint scope. The local smoke evidence captured in `pr_context.md` for this work item is the deterministic `make blueprint-template-smoke` and `make quality-ci-generated-consumer-smoke` results, since those are the canonical signals for this contract surface.
- Publish checklist:
  - include requirement/contract coverage
  - include key reviewer files
  - include validation evidence + rollback notes

## Operational Readiness
- Logging/metrics/traces: existing `log_info`/`log_metric` lines from `init_repo.py` cover the new reseed path under Option A; no new metric required.
- Alerts/ownership: blueprint maintainer; no runtime alerts (this is a tooling/contract fix, not a runtime behaviour change).
- Runbook updates: `docs/blueprint/upgrade/release_notes.md` v1.8.2 entry serves as the operator-facing runbook; if a consumer is still stuck after upgrading, the diagnostic is `cat apps/descriptor.yaml && cat infra/gitops/platform/base/apps/kustomization.yaml | grep -E '\.yaml$'` to confirm filename agreement.

## Risks and Mitigations
- Risk 1 — the paired-reseed could surprise a consumer who manually edited their kustomization.yaml in source control without also updating descriptor.yaml. Mitigation: force-init is opt-in (`BLUEPRINT_INIT_FORCE=true`) and already overwrites consumer-owned files; the paired reseed is consistent with the existing force-init blast radius. Release notes MUST call out the expanded force-init scope explicitly.
- Risk 2 — smoke fixture extension (FR-003) could become a maintenance burden if the v1.8.0-state-shaped consumer fixture drifts from real consumer state. Mitigation: keep the fixture minimal (one consumer app pair, e.g. `marketplace-deployment.yaml`/`marketplace-service.yaml`) and document its purpose inline as the canonical reproducer for issue #230.
