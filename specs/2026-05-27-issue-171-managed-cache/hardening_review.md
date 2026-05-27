# Hardening Review

## Repository-Wide Findings Fixed
- Finding: no repository-wide hardening regressions introduced. Confirmed at implementation time: `make quality-hooks-fast` passes 10/11 checks (quality-spec-pr-ready resolves when publish tasks are marked [x]); `python3 -m pytest tests/infra/modules/managed-cache/ -x -q` → 25 passed (2026-05-27).

## Security Review

### Credential non-persistence (NFR-SEC-001)
- `managed_cache_apply.sh` writes `managed_cache_runtime.env` via `write_state_file` with keys `profile`, `stack`, `host`, `port`, `uri` only. `MANAGED_CACHE_PASSWORD` MUST NOT appear in the state file.
- On STACKIT: `managed_cache_password()` reads from the sensitive foundation TF output at runtime via `stackit_foundation_output_value_or_default`. It is never persisted to disk in cleartext.
- On local lane: `managed_cache_password()` returns `$MANAGED_CACHE_PASSWORD` from the in-process shell environment, seeded by `managed_cache_seed_env_defaults`. Same single-developer threat model exception as bitnami/postgresql, bitnami/rabbitmq, and bitnami/opensearch local lanes.
- Test assertion `test_runtime_state_does_not_contain_password` enforces this constraint.

### Network ACL (NFR-SEC-002)
- `stackit_redis_instance` declares `parameters = { sgw_acl = var.managed_cache_sgw_acl }`. The `managed_cache_sgw_acl` variable is required in the foundation workspace (no default) — operators must supply SKE egress CIDR ranges. Default open-world access (`0.0.0.0/0`) as the sole ACL entry is not permitted by convention and not set as a default. Confirmed at Slice 3 implementation (2026-05-27).

### K8s Secret reconciliation (local lane)
- `managed_cache_reconcile_runtime_secret()` is called by the apply script (helm driver only) before Helm install. It creates or updates the `blueprint-managed-cache-auth` Secret in the `managed-cache` namespace with `redis-password=$MANAGED_CACHE_PASSWORD`. This follows the same pattern as rabbitmq and postgres local lane secret reconciliation.
- ESO ExternalSecret delivery to consumer namespaces is tracked under issue #172 — out of scope for this module.

## Observability and Diagnostics Changes
- No additional in-repo instrumentation required (NFR-OPS-001 scope only).
- Redis connection failures surface via consumer application logs.
- STACKIT Managed Redis instance metrics are available in STACKIT Observability if the observability module is also enabled.
- `make infra-managed-cache-smoke` validates `MANAGED_CACHE_URI` scheme reachability only — no data-plane smoke test.

## Architecture and Code Quality Compliance
- Module follows the established optional module pattern: rabbitmq (PR #221), opensearch (PR #243), postgres (PR #261). Same shell lib + bin scripts + module.contract.yaml + make targets + local Helm values + docs + tests structure.
- `is_stackit_profile` lane branching (from `scripts/lib/infra/profile.sh:69`) is the correct mechanism for STACKIT vs. local divergence in shell lib functions.
- `resolve_optional_module_execution` routes STACKIT apply to the foundation workspace — TF module is never called directly.
- `write_state_file` helper enforces state file structure — password exclusion is a call-site responsibility enforced by the test.
- Bootstrap template sync follows the same `ensure_infra_template_file` pattern used for all other local helm values and TF foundation files.

## Accessibility Gate (Normative — non-UI reviewers mark non-applicable items N/A)
- N/A — no UI surfaces introduced or modified (NFR-A11Y-001).

## Proposals Only (Not Implemented)
- Proposal A (bitnami/redis local lane migration): Deferred — tracked under issue #324 scope for bitnami chart migration; this module should follow the same migration pattern as postgres (#324) when that lands. Trigger: on-scope: managed-cache local lane migration.
- Proposal B (Redis Cluster/HA): Out of scope for issue #171 — requires separate capacity planning. Single-instance provisioning only.
- Proposal C (KMS envelope encryption of Redis password): Out of scope — KMS module concern; same deferral as issue #312 Proposal C.
