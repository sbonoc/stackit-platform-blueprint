# Implementation Plan

## Implementation Start Gate
- Implementation tasks MUST remain unchecked until `SPEC_READY=true`.
- If required inputs are missing, add `BLOCKED_MISSING_INPUTS` in `spec.md` and keep the gate closed.

## Constitution Gates (Pre-Implementation)
- Simplicity gate: Tests assert against existing file contents and shell helper behaviour — no new wrappers or abstraction layers introduced. Follow the `test_contract.py` pattern established in observability and kms modules exactly.
- Anti-abstraction gate: Helper functions tested via subprocess with minimal env fixture; no intermediate mock layers. Module contract YAML is read with `yaml.safe_load` directly.
- Integration-first testing gate: Register `test_contract.py` in `test_pyramid_contract.json` before creating the file (pyramid gate must not block the commit). Write failing assertions first (red), then confirm they pass against existing code (green).
- Positive-path filter/transform test gate: N/A — no filter or payload-transform logic in this work item.
- Finding-to-test translation gate: All shell helper assertions MUST use the actual source file paths in the repo; `workflows_payload_json` field presence checks MUST read the actual function output, not just grep the source.

## Delivery Slices

### Slice 1 — Red: register test file and write failing assertions
1. Add `tests/infra/modules/workflows/test_contract.py` entry to `scripts/lib/quality/test_pyramid_contract.json` under the `unit` scope. Commit registration before creating the file so the pyramid gate sees the entry on first commit.
2. Write `tests/infra/modules/workflows/test_contract.py` with ≥ 15 failing assertions covering:
   - `workflows_plan.env` state file structure: `provision_driver=api_contract`, `payload_file`, `display_name` keys present
   - `workflows_instance.env` state file structure: `instance_id`, `instance_name`, `instance_fqdn`, `web_url`, `health_status` keys present
   - Security: `STACKIT_WORKFLOWS_DAGS_REPO_TOKEN` key absent from all `workflows_*.env` state files
   - `workflows_keycloak_reconcile.env` structure: `realm`, `client_id`, `redirect_uris` keys present
   - `workflows_dag_deploy.env` structure: `status=synced`, `dags_repo_url` keys present
   - `workflows_smoke.env` structure: `status=passed` key present
   - `workflows_init_env()` guard: function definition present in `workflows.sh`; `log_fatal` call present for non-STACKIT profile guard
   - `workflows_default_display_name()` length constraint: function returns ≤ 16 characters
   - `workflows_payload_json()` required fields: `displayName`, `version`, `dagsRepository`, `identityProvider`, `observabilityId` present in function body
   - `workflows_api_request()` env var defaults: `STACKIT_WORKFLOWS_API_BASE_URL` default set in `workflows_api.sh`
   - Module contract YAML inputs: all `required_env` keys present in `module.contract.yaml`
   - Module contract YAML outputs: `STACKIT_WORKFLOWS_INSTANCE_ID`, `STACKIT_WORKFLOWS_INSTANCE_FQDN`, `STACKIT_WORKFLOWS_WEB_URL`, `STACKIT_WORKFLOWS_HEALTH_STATUS` present in `outputs.produced`
   - ArgoCD ConfigMap existence: `infra/gitops/argocd/optional/dev/workflows.yaml` file exists and contains `kind: ConfigMap`
   - Make target registration: `infra-stackit-workflows-apply` present in `scripts/bin/blueprint/render_makefile.sh`
   - DAG parse smoke script: `apps/` directory guard present in `stackit_workflows_dag_parse_smoke.sh`
3. Run `uv run python3 -m pytest tests/infra/modules/workflows/test_contract.py` — expect failures where implementation details are checked (red).

### Slice 2 — Green: verify tests pass against existing implementation
1. Run `uv run python3 -m pytest tests/infra/modules/workflows/test_contract.py` — all assertions MUST pass against the already-implemented shell scripts and module.contract.yaml (green).
   - If any assertion fails due to a real gap in the existing implementation, fix the implementation gap (not the test) to turn it green.
2. Run `make test-unit-all` — all existing module tests must remain green.
3. Run `make quality-hooks-fast`.

### Slice 3 — Docs: write README
1. Write `docs/platform/modules/workflows/README.md` replacing the generated contract summary stub with full documentation covering:
   - Module purpose and managed Airflow overview
   - Provisioning lifecycle: plan → apply → dag-deploy → smoke → destroy with make target commands
   - Keycloak OIDC contract: required realm roles, redirect URI pattern, client type
   - DAG repository requirements: `.git` URL constraint, branch, auth credentials
   - API contract approach and why TF is not used (no `stackit_workflows_instance` provider resource as of v0.96.0)
   - State file outputs: all keys in `workflows_instance.env`, `workflows_keycloak_reconcile.env`, `workflows_dag_deploy.env`, `workflows_smoke.env`
   - Security note: `DAGS_REPO_TOKEN` and `OIDC_CLIENT_SECRET` are never written to state files
   - Troubleshooting: HTTP 409 idempotency, Keycloak redirect URI mismatch, DAG parse smoke violations
   - Consumer usage examples: enable flag, required env vars, make target invocation sequence

### Slice 4 — Docs validation + full gate run
1. Run `make infra-validate` — exit 0 (module contract + make target consistency).
2. Run `make docs-build && make docs-smoke` — exit 0.
3. Run `make quality-hooks-run` — all hooks green.
4. Run `make quality-hardening-review` — exit 0.
5. Run `make quality-spec-pr-ready` — exit 0.

## Change Strategy
- Migration/rollout sequence: Pyramid registration → failing tests → tests pass green against existing code → README update → full validation gates.
- Backward compatibility policy: All changes are additive. No existing shell scripts, API helpers, or module.contract.yaml are modified. Existing module tests remain green.
- Rollback plan: Delete `tests/infra/modules/workflows/test_contract.py`, remove the pyramid registration entry, revert README to generated stub. No runtime impact — no shell scripts are changed.

## Validation Strategy (Shift-Left)
- Unit checks: `uv run python3 -m pytest tests/infra/modules/workflows/test_contract.py` after each slice.
- Contract checks: `make infra-validate` (validates module.contract.yaml + make target consistency).
- Integration checks: `make quality-hooks-fast` and `make quality-hooks-run`.
- E2E checks: N/A — no HTTP route changes; no new shell scripts; state file contract covered at unit level.

## App Onboarding Contract (Normative)
- App onboarding impact: no-impact
- Notes: Tooling/infrastructure-only change. No consumer app delivery workflow is affected.
- Required minimum make targets (all N/A — tooling-only scope):
  - `apps-bootstrap` — N/A
  - `apps-smoke` — N/A
  - `backend-test-unit` — N/A
  - `backend-test-integration` — N/A
  - `backend-test-contracts` — N/A
  - `backend-test-e2e` — N/A
  - `touchpoints-test-unit` — N/A
  - `touchpoints-test-integration` — N/A
  - `touchpoints-test-contracts` — N/A
  - `touchpoints-test-e2e` — N/A
  - `test-unit-all` — N/A
  - `test-integration-all` — N/A
  - `test-contracts-all` — N/A
  - `test-e2e-all-local` — N/A
  - `infra-port-forward-start` — N/A
  - `infra-port-forward-stop` — N/A
  - `infra-port-forward-cleanup` — N/A

## Documentation Plan (Document Phase)
- Blueprint docs updates: none — no blueprint-track architecture changes.
- Consumer docs updates: `docs/platform/modules/workflows/README.md` — full provisioning lifecycle, Keycloak contract, DAG repository requirements, state file outputs, troubleshooting, consumer usage examples.
- Mermaid diagrams updated: architecture.md contains provisioning flowchart, destroy sequence, and reconcile flow; README may include a simplified provisioning flowchart.
- Docs validation commands:
  - `make docs-build`
  - `make docs-smoke`

## Publish Preparation
- PR context file: `pr_context.md`
- Hardening review file: `hardening_review.md`
- Local smoke gate (HTTP route/filter changes): N/A — no HTTP route changes in this work item.
- Publish checklist:
  - include requirement/contract coverage (FR-001–FR-014, AC-001–AC-010)
  - include key reviewer files (test_contract.py, test_pyramid_contract.json, README.md)
  - include validation evidence (test count, infra-validate pass, quality-hooks-run pass, docs-smoke pass)
  - include rollback notes

## Operational Readiness
- Logging/metrics/traces: `stackit_workflows_smoke.sh` validates `health_status=Active` and writes `workflows_smoke.env`. Full end-to-end DAG execution validation is operator responsibility via the Airflow UI.
- Alerts/ownership: No new K8s workloads in this work item. The workflows instance is API-provisioned; health monitoring is via the STACKIT console.
- Runbook updates: `docs/platform/modules/workflows/README.md` updated with troubleshooting section for HTTP 409, Keycloak redirect URI mismatch, and DAG parse smoke violations.

## Risks and Mitigations
- Risk 1 (Q-1 — deferred TF provider upgrade): No functional impact on this work item. Provider upgrade is cross-cutting scope; deferred to a separate work item. Documented in spec.md Q-1.
- Risk 2 (REST API `v1alpha` instability): Mitigated by explicit HTTP code validation in `workflows_api_request()` and deterministic `jq` field path assertions in `workflows_api_json_pick()`. A schema change fails fast with a clear error.
