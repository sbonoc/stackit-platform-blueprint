# Work Item Context Pack

## Context Snapshot
- Work item: 2026-05-27-issue-171-managed-cache
- Track: blueprint
- SPEC_READY: false (Q-1 open — STACKIT Redis TF resource names unverified; implementation gate closed)
- ADR path: docs/blueprint/architecture/decisions/ADR-issue-171-managed-cache.md
- ADR status: proposed

## Problem Being Solved
No blueprint module exists for managed Redis/cache. Consumer use cases (session store, rate-limiting, idempotency cache, Postal email backing store) currently require bespoke per-consumer Redis wiring with no shared secret contract, no ESO integration, and no consistent env-var naming. This work item adds a first-class `managed-cache` optional module that provisions STACKIT Managed Redis on the STACKIT lane and a bitnami/redis instance on the local lane, exposing a stable shell and ESO credential contract (`MANAGED_CACHE_HOST`, `MANAGED_CACHE_PORT`, `MANAGED_CACHE_PASSWORD`, `MANAGED_CACHE_URI`) to consumer workloads. This is also the prerequisite for the `platform-email` module (issue #172).

## Affected Files (Key — at design time; implementation will create these)
- New: `infra/cloud/stackit/terraform/modules/managed-cache/main.tf` (+ variables.tf, outputs.tf, versions.tf)
- New: `infra/local/helm/managed-cache/values.yaml`
- New: `scripts/lib/infra/managed_cache.sh`
- New: `scripts/bin/infra/managed_cache_{plan,apply,smoke,destroy}.sh`
- New: `blueprint/modules/managed-cache/module.contract.yaml`
- New: `tests/infra/modules/managed-cache/test_managed_cache_module.py`
- New: `docs/platform/modules/managed-cache/README.md`
- New: `scripts/templates/infra/bootstrap/infra/local/helm/managed-cache/values.yaml`
- Modified: `blueprint/contract.yaml` — `optional_modules` entry
- Modified: `infra/cloud/stackit/terraform/foundation/variables.tf` — `managed_cache_enabled`
- Modified: `infra/cloud/stackit/terraform/foundation/outputs.tf` — `managed_cache_*` outputs
- Modified: `infra/cloud/stackit/terraform/foundation/main.tf` — module call
- Modified: `make/blueprint.generated.mk` + template — four new targets
- Modified: `scripts/bin/infra/bootstrap.sh` — `ensure_infra_template_file` call

## Open Questions
- Q-1 (blocking Slice 3): Verify exact STACKIT Terraform resource name for Redis. Agent recommendation: `stackit_redis_instance` + `stackit_redis_credential` with attrs `host`, `port`, `password`, `uri`. Must be confirmed via `terraform providers schema -json` (provider version `= 0.88.0`) before writing Slice 3 TF code.

## Guardrail Controls
- Applicable control IDs: SDD-C-002, SDD-C-003, SDD-C-004, SDD-C-005, SDD-C-006, SDD-C-007, SDD-C-008, SDD-C-009, SDD-C-010, SDD-C-011, SDD-C-012, SDD-C-013, SDD-C-014, SDD-C-015, SDD-C-016, SDD-C-017, SDD-C-019, SDD-C-020, SDD-C-021

## Required Commands
- `make quality-sdd-check`
- `make quality-sdd-check-all`
- `make quality-hooks-run`
- `make quality-hardening-review`
- `make infra-validate`
- `make docs-build`
- `make docs-smoke`
- `make spec-pr-context`

## Artifact Index
- `architecture.md`
- `spec.md`
- `plan.md`
- `tasks.md`
- `traceability.md`
- `graph.json`
- `evidence_manifest.json`
- `pr_context.md`
- `hardening_review.md`
