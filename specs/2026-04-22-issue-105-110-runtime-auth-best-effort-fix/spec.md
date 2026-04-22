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
- ADR path: docs/blueprint/architecture/decisions/ADR-20260422-issue-105-110-runtime-auth-best-effort-fix.md
- ADR status: approved

## Applicable Guardrail Controls (Normative)
- Applicable control IDs: SDD-C-001, SDD-C-002, SDD-C-005, SDD-C-012
- Control exception rationale: none

## Implementation Stack Profile (Normative)
- Backend stack profile: none
- Frontend stack profile: none
- Test automation profile: pytest unit tests in `tests/infra/test_tooling_contracts.py`; fast-lane via `make infra-contract-test-fast`
- Agent execution model: specialized-subagents-isolated-worktrees
- Managed service preference: stackit-managed-first
- Managed service exception rationale: none
- Runtime profile: local-first-docker-desktop-kubernetes
- Local Kubernetes context policy: docker-desktop-preferred
- Local provisioning stack: crossplane-plus-helm
- Runtime identity baseline: eso-plus-argocd-plus-keycloak
- Local-first exception rationale: none

## Objective
- Business outcome: `make infra-provision-deploy` no longer aborts due to recoverable ESO namespace timing issues when `RUNTIME_CREDENTIALS_REQUIRED=false`, and local operator `gho_` tokens no longer produce ambiguous `success-with-warnings` status when credentials are functionally valid.
- Success metric: both acceptance criteria pass in `make infra-contract-test-fast`; no regression in existing 97-test suite.

## Normative Requirements

### Functional Requirements (Normative)
- FR-001 MUST: `reconcile_eso_runtime_secrets.sh` MUST NOT exit non-zero under `set -e` when `kustomize apply infra/gitops/platform/base/security` fails and `RUNTIME_CREDENTIALS_REQUIRED=false`. The failure MUST be captured as a reconcile issue and the state file MUST always be written.
- FR-002 MUST: `reconcile_argocd_repo_credentials.sh` MUST accept `gho_` GitHub OAuth tokens without raising a reconcile issue; a PAT MUST remain the preferred credential, communicated via `log_info` only (not `record_reconcile_issue`).
- FR-003 MUST: When `RUNTIME_CREDENTIALS_REQUIRED=true` and `kustomize apply` fails, `reconcile_eso_runtime_secrets.sh` MUST still exit non-zero (the guard must not swallow required failures).

### Non-Functional Requirements (Normative)
- NFR-OPS-001 MUST: `reconcile_eso_runtime_secrets.sh` MUST always write its state file before exiting, including in failure paths.
- NFR-REL-001 MUST: The fix MUST not affect dry-run mode; `run_kustomize_apply` in dry-run mode returns 0 unconditionally and must remain so.

## Normative Option Decision
- Option A: Wrap `run_kustomize_apply` in `if !` guard; change `gho_` branch to `log_info`.
- Option B: Use `set +e`/`set -e` pair around `run_kustomize_apply`; keep `gho_` as hard-error.
- Selected option: OPTION_A
- Rationale: `if !` suspends `set -e` for exactly one command and requires no state cleanup after; `set +e`/`set -e` is broader and risks missing future failures in the same block. Accepting `gho_` eliminates the ambiguous success-with-warnings state without weakening auth validation (empty token is still rejected).

## Contract Changes (Normative)
- Config/Env contract: none (no new env knobs)
- API contract: none
- Event contract: none
- Make/CLI contract: none
- Docs contract: none

## Blueprint Upstream Defect Escalation (Normative)
- Upstream issue URL: none
- Temporary workaround path: none
- Replacement trigger: none
- Workaround review date: none

## Normative Acceptance Criteria
- AC-001 MUST: With `RUNTIME_CREDENTIALS_REQUIRED=false`, a kustomize apply failure in `reconcile_eso_runtime_secrets.sh` results in `status=warn-and-skip` in the state file (not a non-zero exit).
- AC-002 MUST: With `RUNTIME_CREDENTIALS_REQUIRED=true`, a kustomize apply failure results in `status=failed-required` and a non-zero exit.
- AC-003 MUST: `reconcile_argocd_repo_credentials.sh` with `ARGOCD_REPO_TOKEN=gho_<value>` does NOT add a reconcile issue; overall status MUST be `success` (absent other issues).
- AC-004 MUST: `reconcile_argocd_repo_credentials.sh` with `ARGOCD_REPO_TOKEN=gho_<value>` emits at least one `[INFO]`-level log noting PAT preference.
- AC-005 MUST: A structural contract test asserts that `run_kustomize_apply` in `reconcile_eso_runtime_secrets.sh` is preceded by `if !` so `set -e` cannot abort in best-effort mode.
- AC-006 MUST: A structural contract test asserts that `gho_` does NOT trigger `record_reconcile_issue` in `reconcile_argocd_repo_credentials.sh`.

## Informative Notes (Non-Normative)
- Context: Issue #105 was discovered during a fresh local cluster bootstrap where the `security`, `apps`, `data`, and `observability` namespaces are created by Crossplane but the ESO reconciliation races against their creation. Issue #110 was discovered because `gh auth token` returns `gho_` tokens that work for repo read but triggered a warning-only failure state.
- Tradeoffs: Accepting `gho_` tokens means ArgoCD can lose repo access when the OAuth token expires; this is acceptable for local operator flows where `ARGOCD_REPO_CREDENTIALS_REQUIRED=false` is the default.
- Clarifications: none

## Explicit Exclusions
- No changes to `reconcile_runtime_identity.sh` (the orchestrator) — the ESO plugin exit-code fix eliminates the `failed-plugin` propagation.
- No changes to namespace creation timing or retry logic.
