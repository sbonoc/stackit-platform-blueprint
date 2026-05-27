# PR Context

## Summary
- Work item: issue-171-managed-cache
- Objective: Add a first-class `managed-cache` optional module that provisions STACKIT Managed Redis (STACKIT lane) and bitnami/redis (local lane), exposing a stable shell and ESO credential contract (`MANAGED_CACHE_HOST`, `MANAGED_CACHE_PORT`, `MANAGED_CACHE_PASSWORD`, `MANAGED_CACHE_URI`) to consumer workloads. Eliminates bespoke Redis wiring per consumer and unblocks the `platform-email` module (issue #172).
- Scope boundaries: New optional module only. No changes to existing modules or make targets. Module is disabled by default — existing consumers completely unaffected.

## Requirement Coverage
- Requirement IDs covered: FR-001 through FR-011, NFR-SEC-001, NFR-SEC-002, NFR-OPS-001, NFR-OPS-002, NFR-A11Y-001, AC-001 through AC-005
- Acceptance criteria covered: AC-001 (apply provisions Redis + writes state without password), AC-002 (URI scheme valid on both lanes), AC-003 (smoke passes on both lanes), AC-004 (existing consumers unaffected), AC-005 (≥ 10 pytest assertions pass)
- Contract surfaces changed: `blueprint/contract.yaml` (new `optional_modules` entry); new env vars `MANAGED_CACHE_ENABLED/*`; new make targets `infra-managed-cache-{plan,apply,smoke,destroy}`; new state file `managed_cache_runtime.env`.

## Key Reviewer Files
- Primary files to review first:
  - `blueprint/modules/managed-cache/module.contract.yaml` — contract definition
  - `scripts/lib/infra/managed_cache.sh` — shell credential contract (lane branching)
  - `scripts/bin/infra/managed_cache_apply.sh` — state file write (password exclusion)
  - `infra/cloud/stackit/terraform/modules/managed-cache/main.tf` — STACKIT Redis provisioning
  - `infra/cloud/stackit/terraform/foundation/main.tf` — module wiring
  - `tests/infra/modules/managed-cache/test_managed_cache_module.py` — ≥ 10 assertions
- High-risk files: `scripts/lib/infra/managed_cache.sh` (`is_stackit_profile` lane branching must not break local path); `infra/cloud/stackit/terraform/modules/managed-cache/main.tf` (TF resource name blocked on Q-1 resolution); `scripts/templates/blueprint/bootstrap/make/blueprint.generated.mk.tmpl` (additive change; must not clobber existing targets).

## Validation Evidence
- Required commands executed: pending implementation
- Result summary: pending implementation
- Artifact references: `traceability.md`, `hardening_review.md`

## Open Questions
- Q-1 resolved (2026-05-27): `stackit_redis_instance` + `stackit_redis_credential` confirmed from provider registry (`stackitcloud/stackit` v0.88.x). Credential attrs: `host`, `port`, `username`, `password` (sensitive), `uri`. ACL via `parameters.sgw_acl`. No open questions remain.

## Risk and Rollback
- Main risks: STACKIT Redis TF resource name is inferred (Q-1); if incorrect, `terraform apply` fails and must be corrected before any STACKIT lane apply. Local bitnami/redis is subject to the same deprecation risk as bitnami/postgresql (issue #324).
- Rollback strategy: `make infra-managed-cache-destroy` (STACKIT: destroys TF resources; local: `helm uninstall blueprint-managed-cache -n managed-cache`). No data migration required — consumer data loss on destroy is expected and documented in README.

## Deferred Proposals
- Proposal A (bitnami/redis local migration): Parked — trigger: on-scope: managed-cache local lane migration — follow issue #324 bitnami migration scope. No current consumer request.
- Proposal B (Redis Cluster/HA): Out of scope — requires separate capacity planning. Single-instance only.
- Proposal C (KMS envelope encryption): Parked — KMS module concern; same deferral as issue #312 Proposal C. Trigger: when KMS module is in scope.
