# Specification

## Spec Readiness Gate (Blocking)
- SPEC_READY: true
- Open questions count: 0
- Unresolved alternatives count: 0
- Unresolved TODO markers count: 0
- Pending assumptions count: 0
- Open clarification markers count: 0
- Product sign-off: approved
- Architecture sign-off: approved
- Security sign-off: approved
- Operations sign-off: approved
- Missing input blocker token: none
- ADR path: docs/blueprint/architecture/decisions/ADR-20260423-issue-169-upgrade-ci-e2e-validation.md
- ADR status: approved

## Applicable Guardrail Controls (Normative)
- Applicable control IDs: SDD-C-005, SDD-C-006, SDD-C-009, SDD-C-010, SDD-C-012
- Control exception rationale: none

## Implementation Stack Profile (Normative)
- Backend stack profile: python_plus_fastapi_pydantic_v2
- Frontend stack profile: vue_router_pinia_onyx
- Test automation profile: pytest_vitest_playwright_pact
- Agent execution model: specialized-subagents-isolated-worktrees
- Managed service preference: stackit-managed-first
- Managed service exception rationale: none
- Runtime profile: local-first-docker-desktop-kubernetes
- Local Kubernetes context policy: docker-desktop-preferred
- Local provisioning stack: crossplane-plus-helm
- Runtime identity baseline: eso-plus-argocd-plus-keycloak
- Local-first exception rationale: none

## Objective
- Business outcome: The blueprint CI validates the full consumer upgrade flow on every push to the main branch, making upgrade regressions visible as a dedicated job with artifact upload before any release tag is published.
- Success metric: A new `upgrade-e2e-validation` job exists in `.github/workflows/ci.yml`, triggers on `push` events only, calls `make quality-ci-upgrade-validate`, and uploads a JUnit XML artifact; all existing CI jobs continue to pass.

## Normative Requirements

### Functional Requirements (Normative)
- FR-001 `scripts/bin/blueprint/ci_upgrade_validate.sh` MUST exist and invoke `python3 -m pytest tests/blueprint/test_upgrade_fixture_matrix.py` with `--junitxml` output to `$BLUEPRINT_CI_UPGRADE_ARTIFACTS_DIR/upgrade_validate_junit.xml`; it MUST exit non-zero if pytest exits non-zero.
- FR-002 A `quality-ci-upgrade-validate` make target MUST exist in both `scripts/templates/blueprint/bootstrap/make/blueprint.generated.mk.tmpl` and `make/blueprint.generated.mk` and MUST invoke `ci_upgrade_validate.sh`.
- FR-003 `scripts/lib/quality/render_ci_workflow.py` MUST render a new `upgrade-e2e-validation` GitHub Actions job that runs `make quality-ci-upgrade-validate` on `push` events only (job-level `if: github.event_name == 'push'`) and uploads `artifacts/blueprint/upgrade_validate/upgrade_validate_junit.xml` via `actions/upload-artifact@v4`.
- FR-004 `quality-ci-sync` and `quality-ci-check-sync` (which invoke `render_ci_workflow.py`) MUST produce and validate the complete CI workflow including the new job; the check target MUST fail when the rendered workflow drifts from the tracked file.

### Non-Functional Requirements (Normative)
- NFR-SEC-001 `ci_upgrade_validate.sh` MUST NOT make external network calls; all operations MUST be local filesystem and Python subprocess invocations only; the script MUST NOT introduce new environment variables beyond `BLUEPRINT_CI_UPGRADE_ARTIFACTS_DIR`.
- NFR-OBS-001 The `upgrade-e2e-validation` CI job MUST upload `upgrade_validate_junit.xml` so upgrade test results are visible in the GitHub Actions UI with individual test names and pass/fail status.
- NFR-REL-001 `ci_upgrade_validate.sh` MUST use `set -euo pipefail`; any pytest failure MUST propagate as a non-zero exit code from the script.
- NFR-OPS-001 `make quality-ci-upgrade-validate` MUST be runnable locally without additional setup beyond the normal development prerequisites (Python, pytest).

## Normative Option Decision
- Option A: `ci_upgrade_validate.sh` wraps `python3 -m pytest tests/blueprint/test_upgrade_fixture_matrix.py`; no new Python script or duplicate fixture setup logic.
- Option B: New Python driver script sets up temp repos independently and calls Python upgrade scripts directly, matching the style of `template_smoke.sh`.
- Selected option: Option A
- Rationale: Option A reuses the existing, validated `test_upgrade_fixture_matrix.py` without duplicating the ~80 lines of temp-repo fixture setup logic. The pytest runner handles temp directory lifecycle, fixture materialization, and assertion failures. Option B would reproduce code already maintained in the test module and introduce a second fixture-setup path to keep in sync. Option A is the minimal correct Phase 1 foundation: Phase 2 issues (#162, #163) will add new test modules to the same pytest invocation inside `ci_upgrade_validate.sh`.

## Contract Changes (Normative)
- Config/Env contract: New env var `BLUEPRINT_CI_UPGRADE_ARTIFACTS_DIR` (default: `$ROOT_DIR/artifacts/blueprint/upgrade_validate/`); consumed only by `ci_upgrade_validate.sh`; no consumer-facing contract change.
- API contract: none.
- Event contract: none.
- Make/CLI contract: New make target `quality-ci-upgrade-validate` added to `make/blueprint.generated.mk` and its template source; no existing targets changed.
- Docs contract: none.

## Blueprint Upstream Defect Escalation (Normative)
- Upstream issue URL: none
- Temporary workaround path: none
- Replacement trigger: none
- Workaround review date: none

## Normative Acceptance Criteria
- AC-001 `scripts/bin/blueprint/ci_upgrade_validate.sh` exists, is executable, and its body contains `set -euo pipefail`.
- AC-002 `quality-ci-upgrade-validate` target exists in `make/blueprint.generated.mk` and in `scripts/templates/blueprint/bootstrap/make/blueprint.generated.mk.tmpl`.
- AC-003 `.github/workflows/ci.yml` contains an `upgrade-e2e-validation` job with `if: github.event_name == 'push'` at the job level.
- AC-004 The `upgrade-e2e-validation` job uploads `artifacts/blueprint/upgrade_validate/upgrade_validate_junit.xml` via `actions/upload-artifact@v4`.
- AC-005 `shellcheck --severity=error scripts/bin/blueprint/ci_upgrade_validate.sh` passes.
- AC-006 A structural test in `tests/blueprint/contract_refactor_scripts_cases.py` asserts AC-001 and AC-002.

## Informative Notes (Non-Normative)
- Context: `test_upgrade_fixture_matrix.py` already runs as part of `infra-contract-test-fast` (invoked by `quality-hooks-fast` inside the `blueprint-quality` CI job). Issue #169 adds a dedicated upgrade-e2e-validation job so the upgrade validation is visible as a separate CI gate with artifact upload. The dedicated job runs on push-to-main only (not on PRs) to act as a pre-release gate. Phase 2 issues (#162, #163) will extend `ci_upgrade_validate.sh` with additional pytest modules.
- Tradeoffs: Running `test_upgrade_fixture_matrix.py` twice on main pushes (once in blueprint-quality, once in upgrade-e2e-validation) is an intentional trade-off for explicit visibility and artifact upload. The duplication is bounded and accepted.
- Clarifications: none.

## Explicit Exclusions
- Replacing the existing `infra-contract-test-fast` invocation of `test_upgrade_fixture_matrix.py` is out of scope; both continue to run.
- Adding Phase 2 correctness gate assertions (#162 bash-n validation, #163 clean-worktree smoke) to `ci_upgrade_validate.sh` is out of scope for this item.
- Implementing live-tag upgrade validation (using the actual previous release tag rather than the fixture snapshot) is out of scope; the fixture snapshot approach is the correct Phase 1 baseline.
