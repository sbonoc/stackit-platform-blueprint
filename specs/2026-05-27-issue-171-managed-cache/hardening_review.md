# Hardening Review

## Repository-Wide Findings Fixed
- Finding: no repository-wide hardening regressions introduced at intake stage. To be confirmed at implementation time by running `make quality-hooks-fast` and the full pytest suite.

## Security Review

### Credential non-persistence (NFR-SEC-001)
- `managed_cache_apply.sh` writes `managed_cache_runtime.env` via `write_state_file` with keys `profile`, `stack`, `host`, `port`, `uri` only. `MANAGED_CACHE_PASSWORD` MUST NOT appear in the state file.
- On STACKIT: `managed_cache_password()` reads from the sensitive foundation TF output at runtime via `stackit_foundation_output_value_or_default`. It is never persisted to disk in cleartext.
- On local lane: `managed_cache_password()` returns `$MANAGED_CACHE_PASSWORD` from the in-process shell environment, seeded by `managed_cache_seed_env_defaults`. Same single-developer threat model exception as bitnami/postgresql, bitnami/rabbitmq, and bitnami/opensearch local lanes.
- Test assertion `test_runtime_state_does_not_contain_password` enforces this constraint.

### Network ACL (NFR-SEC-002)
- `stackit_redis_instance` MUST declare a network ACL block aligned with SKE egress CIDR ranges. The same `auto_align_with_ske_egress_ranges` policy used for postgres applies here. Default open-world access (`0.0.0.0/0`) MUST NOT be the sole ACL entry.
- To be verified at Slice 3 implementation time against the STACKIT provider schema (blocked on Q-1 resolution).

### ESO credential delivery to consumers
- Consumer workloads receive credentials via ESO ExternalSecret referencing a K8s Secret created by `managed_cache_reconcile_runtime_secret()` in the apply script. The K8s Secret contains `host`, `port`, `uri`, and `password`. This is the correct ESO-compatible pattern — etcd stores the K8s Secret, which is acceptable under the existing blueprint threat model (same pattern as rabbitmq, opensearch).
- `MANAGED_CACHE_URI` is the canonical consumer credential; consumers should prefer URI over individual components.

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
