# Consumer Ops Checklist

1. Confirm repo mode is generated-consumer (`blueprint/contract.yaml`).
2. Run contract preflight before deploy/change flows:
   - `make blueprint-bootstrap`
   - `make infra-validate`
   - `make blueprint-check-placeholders`
3. Prefer canonical make targets over direct script invocations.
4. Keep consumer-owned changes intact; avoid forcing overwrites.
5. Capture and report artifact outputs under `artifacts/infra` and `artifacts/blueprint`.

## Profile-Aware Runbook Checklist

1. Local runbook:
   - `make blueprint-bootstrap`
   - `make infra-bootstrap`
   - `make infra-validate`
   - `make infra-smoke`
   - `make infra-status-json`
2. STACKIT runbook:
   - `make infra-stackit-bootstrap-preflight`
   - `make infra-stackit-foundation-preflight`
   - `make infra-stackit-runtime-prerequisites`
   - `make infra-stackit-runtime-deploy`
   - `make infra-status-json`

## Module Lifecycle Checklist

1. Apply module teardown + surface refresh:
   - `make infra-destroy-disabled-modules`
   - `make blueprint-render-makefile`
   - `make blueprint-bootstrap`
   - `make infra-bootstrap`
   - `make infra-validate`

## Runtime Identity Checklist

1. Reconcile runtime identity:
   - `make auth-reconcile-runtime-identity`
   - `make infra-status-json`
2. Include ESO, Argo repo credentials, and Keycloak/module reconciliation summary in the report.

## New App Onboarding Checklist

1. Enable app-catalog + runtime GitOps flags:
   - `APP_CATALOG_SCAFFOLD_ENABLED=true`
   - `APP_RUNTIME_GITOPS_ENABLED=true`
2. Bootstrap scaffolds:
   - `make blueprint-bootstrap`
   - `make apps-bootstrap`
   - `make infra-bootstrap`
3. Replace `apps-ci-bootstrap-consumer` placeholder in `make/platform.mk` with deterministic dependency install commands.
4. Update `apps/catalog/manifest.yaml` and `apps/catalog/versions.lock`.
5. Add/update app runtime manifests under `infra/gitops/platform/base/apps/` and keep `kustomization.yaml` synchronized.
6. Add/adjust app test lanes (targets/scripts) in consumer-owned surfaces.
7. Validate and report:
   - `make apps-smoke`
   - `make infra-validate`
   - `make infra-smoke`
   - `make quality-hooks-run`

## CI Bootstrap Contract Checklist

1. Verify `apps-ci-bootstrap-consumer` is implemented (not placeholder).
2. Validate CI hooks deterministically:
   - `make apps-ci-bootstrap`
   - `make test-unit-all`
   - `make test-integration-all`
   - `make test-contracts-all`

## Upgrade/Resync Bridge Checklist

1. Run safe resync:
   - `make blueprint-resync-consumer-seeds`
   - `BLUEPRINT_RESYNC_APPLY_SAFE=true make blueprint-resync-consumer-seeds`
2. Hand off actual upgrade execution to `blueprint-consumer-upgrade` skill (preflight/plan/apply/validate).
3. Run post-upgrade checks in this skill:
   - `make blueprint-upgrade-consumer-validate`
   - `make auth-reconcile-runtime-identity`
   - `make apps-smoke`
   - `make infra-status-json`
4. Treat non-empty `required_manual_actions` as blocking.

## Validation Matrix Checklist

1. Run at least:
   - `OBSERVABILITY_ENABLED=false make infra-validate apps-smoke infra-smoke`
   - `OBSERVABILITY_ENABLED=true make infra-validate apps-smoke infra-smoke`
2. Report pass/fail by matrix row and failed artifact paths.

## Release-Readiness Checklist

1. Run:
   - `make quality-hooks-run`
   - `make infra-audit-version`
   - `make apps-audit-versions`
   - `make infra-status-json`

## Troubleshooting Artifact Pack Checklist

1. Collect deterministic diagnostics:
   - `make infra-context`
   - `make infra-status`
   - `make infra-status-json`
   - `make infra-help-reference`
2. Include artifacts when present:
   - `artifacts/infra/infra_status_snapshot.json`
   - `artifacts/infra/smoke_result.json`
   - `artifacts/infra/smoke_diagnostics.json`
   - `artifacts/infra/workload_health.json`
   - `artifacts/blueprint/upgrade_preflight.json`
   - `artifacts/blueprint/upgrade_plan.json`
   - `artifacts/blueprint/upgrade_apply.json`
   - `artifacts/blueprint/upgrade_validate.json`

## Blueprint Defect Escalation Checklist

1. Escalate only if defect reproduces with canonical blueprint targets and conflicts with contract/docs expectations.
2. Search existing open blueprint bug issues first (use target/module/error-signature keywords) and only create a new issue when no active duplicate exists.
3. Create issue in blueprint repo using bug template (`.github/ISSUE_TEMPLATE/bug_report.yml`).
4. Apply labels:
   - `bug`
   - one `area/*` label
   - one priority label (`P0`/`P1`/`P2`)
   - profile context label when available (`profile/local` or `profile/stackit`)
5. Include:
   - blueprint tag/commit + active flags/profile
   - exact command sequence to reproduce
   - expected vs actual behavior
   - artifact evidence paths
   - sanitized workaround currently applied (if any)
   - sanitized suggested fix direction (if any)
6. Never leak secrets:
   - redact tokens/passwords/secrets/keys/kubeconfig/internal sensitive endpoints
   - sanitize logs before submission
