# Tasks

## Gate Checks (Required Before Implementation)
- [ ] G-001 Confirm `SPEC_READY=true` in `spec.md`
- [ ] G-002 Confirm open questions and unresolved alternatives are `0`
- [ ] G-003 Confirm required sign-offs are approved
- [ ] G-004 Confirm `Applicable Guardrail Controls` section includes `SDD-C-###` IDs
- [ ] G-005 Confirm `Implementation Stack Profile` section is fully populated

## Implementation

### Slice 1 — Red phase (failing tests first)
- [ ] T-001 Write `tests/blueprint/test_workaround_manifest_check.py`:
      - Case (a): subprocess exit 0 for a temp-dir manifest with all files present
      - Case (b): subprocess exit 1 + stderr output for a temp-dir manifest with a missing `action_path` file
      - Case (c): live-manifest assertion — all v1.10.0 entries resolve to existing files on disk
      Run `pytest tests/blueprint/test_workaround_manifest_check.py` — confirm (a)+(b) fail (checker not yet created); (c) passes trivially or is deferred.

### Slice 1 — Green phase (implementation)
- [ ] T-002 Write `scripts/bin/quality/check_workaround_manifest.py`:
      - Resolve SKILL_ROOT and MANIFEST_PATH from REPO_ROOT
      - Read manifest via `yaml.safe_load`
      - Iterate all versions → workarounds → `action_path`; resolve each as `SKILL_ROOT / action_path`
      - Collect missing files; exit 0 (all present) or exit 1 + stderr per violation
- [ ] T-003 Add `quality-workaround-manifest-check` to `.PHONY` list in `make/blueprint.generated.mk` and add recipe: `@uv run python3 scripts/bin/quality/check_workaround_manifest.py`
- [ ] T-004 Add mirror target to `scripts/templates/blueprint/bootstrap/make/blueprint.generated.mk.tmpl`
- [ ] T-005 Add unconditional `run_check "quality-workaround-manifest-check" -- make -C "$ROOT_DIR" quality-workaround-manifest-check` to `scripts/bin/quality/hooks_fast.sh` after the `quality-sdd-check-all` block
- [ ] T-006 Run `pytest tests/blueprint/test_workaround_manifest_check.py` — all three cases PASS
- [ ] T-007 Run `make quality-workaround-manifest-check` — exits 0
- [ ] T-008 Run `make quality-hooks-fast` — `quality-workaround-manifest-check  PASS` in summary

## Test Automation
- [ ] T-101 `tests/blueprint/test_workaround_manifest_check.py` written (T-001) and passing (T-006)
- [ ] T-102 N/A — no API contract or Pact test
- [ ] T-103 N/A — no filter or payload-transform logic
- [ ] T-104 N/A — no reproducible pre-PR smoke/curl finding; missing-action-path test (T-001 case b) is the regression test
- [ ] T-105 N/A — no boundary/integration tests beyond the live-manifest pytest assertion (T-001 case c)

## Accessibility Testing (Normative — mark N/A with rationale for non-UI specs)
- [ ] T-A01 NFR-A11Y-001 declared in spec.md as "N/A — no UI or frontend changes"
- [ ] T-A02 N/A — no UI changes
- [ ] T-A03 N/A — no UI changes
- [ ] T-A04 N/A — no UI changes
- [ ] T-A05 N/A — no UI changes

## Validation and Release Readiness
- [ ] T-201 Run `make quality-hooks-fast` and `make infra-validate`; capture pass/fail
- [ ] T-202 Attach evidence to traceability document
- [ ] T-203 Confirm no stale TODOs/dead code/drift
- [ ] T-204 Run documentation validation (`make docs-build` and `make docs-smoke`)
- [ ] T-205 Run hardening review validation bundle (`make quality-hardening-review`)

## Publish
- [ ] P-001 Update `hardening_review.md` with repository-wide findings fixed and proposals-only section
- [ ] P-002 Update `pr_context.md` with requirement/contract coverage, key reviewer files, validation evidence, and rollback notes
- [ ] P-003 Ensure PR description follows repository template headings and references `pr_context.md`

## App Onboarding Minimum Targets (Normative)
- [ ] A-001 `apps-bootstrap` and `apps-smoke` — N/A; tooling-only change, no app delivery workflow impact
- [ ] A-002 Backend app lanes (`backend-test-unit`, `backend-test-integration`, `backend-test-contracts`, `backend-test-e2e`) — N/A; tooling-only change
- [ ] A-003 Frontend app lanes (`touchpoints-test-unit`, `touchpoints-test-integration`, `touchpoints-test-contracts`, `touchpoints-test-e2e`) — N/A; tooling-only change
- [ ] A-004 Aggregate gates (`test-unit-all`, `test-integration-all`, `test-contracts-all`, `test-e2e-all-local`) — N/A; tooling-only change
- [ ] A-005 Port-forward operational wrappers (`infra-port-forward-start`, `infra-port-forward-stop`, `infra-port-forward-cleanup`) — N/A; tooling-only change
