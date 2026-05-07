---
name: blueprint-consumer-ops
description: Operate generated-consumer repositories initialized from stackit-platform-blueprint. Use for contract preflight, profile-aware runbooks, module lifecycle, runtime identity reconciliation, app onboarding, upgrade/resync bridge, validation matrix, release-readiness checks, and troubleshooting artifact capture with deterministic make-target flows.
---

# Blueprint Consumer Operations

## When to Use
Use this skill when working in a **generated-consumer** repo and the user asks for blueprint operations outside upgrade execution, such as:
- contract/run preflight and readiness checks
- profile-aware day-2 operations (`local` or `stackit-*`)
- optional-module lifecycle changes
- infra/apps deploy/smoke/status and release-readiness flows
- runtime identity reconciliation (ESO + Argo repo access + Keycloak/module coverage)
- adding new apps to app catalog + runtime GitOps scaffold
- upgrade/resync planning and execution with manual-action handling
- feature-flag validation matrix runs
- docs/quality/contract validation
- troubleshooting artifact collection and diagnostics

## Governance Context

`AGENTS.md` is the canonical policy source for behavioral and code changes triggered during consumer operations. Sections that apply:

- `§ Blueprint Contract Precedence` — `blueprint/contract.yaml` is the executable contract; blueprint-managed surfaces must not be overridden outside canonical flows.
- `§ Mandatory Workflow` — any non-trivial behavioral or code change discovered during operations MUST follow the SDD lifecycle before implementation.
- `§ Minimum Validation Bundles by Change Type` — the bundle matching the change type must pass before declaring the operation complete.
- `§ Definition of Done (DoD)` — operations that result in code or config changes are not done until tests, docs, and contracts are synchronized.

> If `AGENTS.md` changes any of the above sections, update this block to reflect the affected sections.

> Quality-hooks usage policy (per-slice vs pre-PR gate, keep-going env, force-full): see AGENTS.md § Quality Hooks — Inner-Loop and Pre-PR Usage.

## Guardrails
1. Treat `blueprint/contract.yaml` as the execution contract.
2. Keep ownership boundaries strict:
   - blueprint-managed files: update only through canonical blueprint flows
   - consumer-owned platform files: preserve customizations
3. Prefer make targets over ad-hoc scripts.
4. Do not commit/push unless the user explicitly requests it.
5. For drift-sensitive flows, report exact commands and artifacts.
6. Keep operations deterministic: no directory scanning/discovery scripts in consumer overrides.
7. In generated-consumer mode, fail fast when contract placeholders are still active (for example `apps-ci-bootstrap-consumer` and optional `infra-post-deploy-consumer`).
8. For non-trivial behavioral/code changes, follow SDD lifecycle in consumer `AGENTS.md`:
   `Discover -> High-Level Architecture -> Specify -> Plan -> Implement -> Verify -> Document -> Operate`.
9. During `Discover`, `High-Level Architecture`, `Specify`, and `Plan`, do not resolve missing requirements with assumptions.
10. Keep `SPEC_READY=false` until all required inputs are explicit; if unresolved, mark `BLOCKED_MISSING_INPUTS`.
11. Require applicable `SDD-C-###` control IDs in `spec.md` for each non-trivial work item.

## Operating Modes

### 1) Repo-Mode + Contract Preflight
Goal: verify the repository is safe to operate before any deploy/change flow.
```bash
make blueprint-bootstrap
make infra-validate
make blueprint-check-placeholders
```
If key targets are missing, stop and recommend source upgrade/resync first.

### 2) Profile-Aware Runbooks
Goal: run deterministic chains matching selected execution profile.

Local baseline:
```bash
make blueprint-bootstrap
make infra-bootstrap
make infra-validate
make infra-smoke
make infra-status-json
```

STACKIT baseline:
```bash
make infra-stackit-bootstrap-preflight
make infra-stackit-foundation-preflight
make infra-stackit-runtime-prerequisites
make infra-stackit-runtime-deploy
make infra-status-json
```

### 3) Module Lifecycle Assistant
Goal: safely enable/disable optional modules and reconcile generated surfaces.
```bash
make infra-destroy-disabled-modules
make blueprint-render-makefile
make blueprint-bootstrap
make infra-bootstrap
make infra-validate
```
Always report which module flags were changed and what scaffold/targets were materialized.

### 4) Runtime Identity Assistant
Goal: reconcile runtime identity contracts after infra/app changes.
```bash
make auth-reconcile-runtime-identity
make infra-status-json
```
Include explicit summary of ESO source->target, Argo repo credentials contract, and Keycloak/module reconciliation outcomes.

### 5) App Onboarding Generator Mode
Goal: add a new app using app catalog + runtime GitOps contract paths.

Preconditions:
- `APP_RUNTIME_GITOPS_ENABLED=true` (default)
- `APP_CATALOG_SCAFFOLD_ENABLED=true` when catalog contract is required

Bootstrap onboarding surfaces:
```bash
APP_CATALOG_SCAFFOLD_ENABLED=true APP_RUNTIME_GITOPS_ENABLED=true make blueprint-bootstrap
APP_CATALOG_SCAFFOLD_ENABLED=true APP_RUNTIME_GITOPS_ENABLED=true make apps-bootstrap
APP_CATALOG_SCAFFOLD_ENABLED=true APP_RUNTIME_GITOPS_ENABLED=true make infra-bootstrap
```
Required consumer-owned implementation:
- replace `apps-ci-bootstrap-consumer` placeholder in `make/platform.mk` with deterministic dependency/bootstrap commands.

Then keep these synchronized:
- `apps/catalog/manifest.yaml` (`deliveryTopology`, `runtimeDeliveryContract`)
- `apps/catalog/versions.lock`
- `infra/gitops/platform/base/apps/*` + `kustomization.yaml`
- app test lanes/targets in `make/platform.mk` and `scripts/bin/platform/**`

Validate:
```bash
APP_CATALOG_SCAFFOLD_ENABLED=true APP_RUNTIME_GITOPS_ENABLED=true make apps-smoke
APP_CATALOG_SCAFFOLD_ENABLED=true APP_RUNTIME_GITOPS_ENABLED=true make infra-validate
APP_CATALOG_SCAFFOLD_ENABLED=true APP_RUNTIME_GITOPS_ENABLED=true make infra-smoke
make quality-hooks-run
```

### 6) Consumer CI Bootstrap Contract Checker
Goal: ensure consumer CI dependency hook is implemented and deterministic.
- Confirm `apps-ci-bootstrap-consumer` is no longer placeholder in `make/platform.mk`.
- Run:
```bash
make apps-ci-bootstrap
make test-unit-all
make test-integration-all
make test-contracts-all
```
- If placeholder is active in generated-consumer mode, stop with remediation.

### 7) Upgrade/Resync Bridge
Goal: upgrade safely while preserving consumer-owned customizations.

This mode is an orchestration bridge. Use the companion `blueprint-consumer-upgrade` skill for the actual
upgrade execution workflow (`preflight` / `plan` / `apply` / `validate`).

Prepare and hand off:
```bash
make blueprint-resync-consumer-seeds
BLUEPRINT_RESYNC_APPLY_SAFE=true make blueprint-resync-consumer-seeds
```
Then run the upgrade via `blueprint-consumer-upgrade` skill.

Post-upgrade checks (still in this skill):
```bash
make blueprint-upgrade-consumer-validate
make auth-reconcile-runtime-identity
make apps-smoke
make infra-status-json
```
Treat non-empty `required_manual_actions` as blocking until reconciled.

### 8) Validation Matrix Mode
Goal: run key feature-flag combinations with one consolidated outcome report.
Minimum matrix:
- `OBSERVABILITY_ENABLED=false`
- `OBSERVABILITY_ENABLED=true`
For each row run:
```bash
make infra-validate
make apps-smoke
make infra-smoke
```
Report pass/fail by row and failed artifact paths.

### 9) Release-Readiness Mode
Goal: verify the repo is ready for promotion/release workflows.
```bash
make quality-hooks-run
make infra-audit-version
make apps-audit-versions
make infra-status-json
```
Summarize dependency drift/audit outcomes and workload health.

### 10) Troubleshooting Artifact Pack
Goal: collect deterministic diagnostics for rapid incident analysis.
```bash
make infra-context
make infra-status
make infra-status-json
make infra-help-reference
```
Include artifact references when present:
- `artifacts/infra/infra_status_snapshot.json`
- `artifacts/infra/smoke_result.json`
- `artifacts/infra/smoke_diagnostics.json`
- `artifacts/infra/workload_health.json`
- `artifacts/blueprint/upgrade_preflight.json`
- `artifacts/blueprint/upgrade_plan.json`
- `artifacts/blueprint/upgrade_apply.json`
- `artifacts/blueprint/upgrade_validate.json`

### 11) Blueprint Defect Escalation
Goal: turn confirmed blueprint defects into actionable upstream issues.

Escalate to blueprint repo only when all are true:
- issue reproduces with canonical blueprint targets (not only custom consumer scripts)
- behavior conflicts with blueprint contract/docs or breaks expected lifecycle guarantees
- evidence is captured with deterministic command output and artifact references

Issue creation rules:
- search existing open blueprint bug issues first using repro keywords (target, module, error signature) and only create a new issue when no matching active issue exists
- use blueprint bug template (`.github/ISSUE_TEMPLATE/bug_report.yml`)
- apply labels:
  - `bug`
  - one `area/*` label (for example `area/upgrade`, `area/contracts`, `area/docs`, `area/ci`, `area/runtime-identity`)
  - one priority label (`P0`, `P1`, or `P2`)
  - profile context label when available (`profile/local` or `profile/stackit`)

Required issue contents:
- blueprint tag/commit and consumer profile/feature flags
- exact reproducible command sequence
- expected vs actual behavior
- artifact paths used as evidence (`artifacts/infra/*`, `artifacts/blueprint/*`)
- minimal reproduction scope
- workaround currently applied in consumer repo (if any), described generically and without secrets
- suggested fix direction (if known), described generically and without secrets

Sensitive-data guardrails:
- never include tokens, passwords, client secrets, private keys, kubeconfigs, or internal hostnames
- redact secret material from logs before posting
- if a secret appeared in terminal output, sanitize the transcript before issue submission

## Day-2 App/Infra Workflow
Use this default chain for normal operations after preflight:
```bash
make infra-provision-deploy
make apps-smoke
make auth-reconcile-runtime-identity
make infra-status-json
```

## Required Report Format
Return:
1. Active profile/flags used.
2. Operating mode selected and why.
3. Commands executed.
4. Artifacts inspected (`artifacts/infra/*.json`, `artifacts/blueprint/*.json`).
5. Findings and blocking items.
6. Minimal safe next step.
7. For app onboarding: exact paths added/updated for catalog, GitOps manifests, and test lanes.
8. If escalated upstream: issue URL, labels applied, and sanitized workaround/suggested-fix summary.

## References
- Operational checklist: `references/consumer_ops_checklist.md`
