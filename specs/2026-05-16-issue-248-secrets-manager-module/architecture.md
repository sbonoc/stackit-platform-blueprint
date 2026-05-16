# Architecture

## Context
- Work item: 2026-05-16-issue-248-secrets-manager-module
- Owner: bonos
- Date: 2026-05-16

## Stack and Execution Model
- Backend stack profile: n/a — tooling/infrastructure-only change
- Frontend stack profile: n/a — tooling/infrastructure-only change
- Test automation profile: pytest
- Agent execution model: specialized-subagents-isolated-worktrees

## Problem Statement
- What needs to change and why: The `infra/cloud/stackit/terraform/modules/secrets-manager/` standalone Terraform module is a 7-line stub with no provider resources. The shell layer (`secrets_manager.sh`, `secrets_manager_apply.sh`, `secrets_manager_plan.sh`, `secrets_manager_smoke.sh`) is missing two contract outputs (`SECRETS_MANAGER_NAMESPACE`, `SECRETS_MANAGER_AUTH_METHOD_DETAILS`), the `reconcile_runtime_secret` call (password → K8s Secret), and smoke validation for the new keys. Blueprint consumers need a provisioned STACKIT Secrets Manager instance with ESO-compatible credentials delivered through the standard optional-module flow.
- Scope boundaries: Standalone Terraform module, shell lib helpers, apply/plan/smoke scripts, module contract, pytest test_contract.py. No changes to foundation Terraform, Make targets, execution driver routing, or local Helm lane.
- Out of scope: Foundation Terraform refactoring; consumer-side ESO SecretStore; local Helm chart; other stub modules (dns, public-endpoints, observability, workflows, identity-aware-proxy).

## Bounded Contexts and Responsibilities
- Terraform provisioning context: `infra/cloud/stackit/terraform/modules/secrets-manager/` — standalone module that can be applied independently to provision `stackit_secretsmanager_instance` + `stackit_secretsmanager_user`. Foundation layer retains its own inline resources (unchanged).
- Shell orchestration context: `scripts/lib/infra/secrets_manager.sh` + `scripts/bin/infra/secrets_manager_{apply,plan,smoke,destroy}.sh` — reads Terraform outputs via foundation contract helper, writes runtime state artifact, reconciles K8s Secret for the password.

## High-Level Component Design
- Domain layer: `blueprint/modules/secrets-manager/module.contract.yaml` — declares required inputs and produced outputs including the two new keys.
- Application layer: `scripts/lib/infra/secrets_manager.sh` — helper functions (`secrets_manager_namespace`, `secrets_manager_auth_method_details`, `secrets_manager_reconcile_runtime_secret`) consumed by apply/plan/smoke scripts.
- Infrastructure adapters: `infra/cloud/stackit/terraform/modules/secrets-manager/{main,variables,outputs}.tf` — standalone Terraform module; `scripts/bin/infra/secrets_manager_{apply,plan,smoke}.sh` — orchestration scripts.
- Presentation/API/workflow boundaries: `module_execution.sh` routing (unchanged): STACKIT lane → `foundation_contract` (plan/apply) or `foundation_reconcile_apply` (destroy); local lane → `noop`.

## Integration and Dependency Edges
- Upstream dependencies: STACKIT Terraform provider (`stackit_secretsmanager_instance`, `stackit_secretsmanager_user` resources); foundation contract helper (`stackit_foundation_output_value_or_default`); shared `reconcile_runtime_secret()` helper.
- Downstream dependencies: Blueprint consumers read `artifacts/infra/secrets_manager_runtime.env` for `namespace` and `auth_method_details`; ESO SecretStore uses `blueprint-secrets-manager-auth` K8s Secret for the password.
- Data/API/event contracts touched: `blueprint/modules/secrets-manager/module.contract.yaml` — additive change (two new outputs); `artifacts/infra/secrets_manager_runtime.env` — additive state keys.

## Non-Functional Architecture Notes
- Security: Password value flows exclusively via `secrets_manager_reconcile_runtime_secret()` → K8s Secret. State file, CI logs, and all non-sensitive artifacts MUST NOT contain the password. `auth_method_details` = username only (NFR-SEC-001).
- Observability: Runtime state artifact gains `namespace` and `auth_method_details`; smoke script validates `namespace` non-empty. All script output prefixed with `[secrets-manager]` (NFR-OBS-001).
- Reliability and rollback: `lifecycle { create_before_destroy = true }` on `stackit_secretsmanager_instance.this` minimises downtime on replacement (NFR-REL-001). Rollback: destroy via `foundation_reconcile_apply` driver, then re-provision.
- Monitoring/alerting: No runtime service monitoring changes. Smoke check via `make infra-provision MODULE=secrets-manager` serves as the operational health gate.

## Risks and Tradeoffs
- Risk 1: Foundation Terraform manages its own inline `stackit_secretsmanager_instance` — the standalone module introduces a second provisioning path. Mitigated by never calling the standalone module from the foundation; the two are independent.
- Tradeoff 1: Namespace = instance_name (derived, not a provider attribute) — this is correct per STACKIT SM URL structure but relies on an implicit naming convention. Documented in the ADR and spec as a resolved decision.
