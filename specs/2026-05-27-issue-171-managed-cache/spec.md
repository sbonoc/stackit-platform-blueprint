# Specification

## Spec Readiness Gate (Blocking)
<!-- SPEC_PRODUCT_READY=true: intake gate — Product sign-off only; unlocks agent ADR drafting.
     SPEC_READY=true: implementation gate — all sign-offs required; unlocks coding. -->
- SPEC_READY: false
- SPEC_PRODUCT_READY: false
- Open questions count: 0
- Unresolved alternatives count: 0
- Unresolved TODO markers count: 0
- Pending assumptions count: 0
- Open clarification markers count: 0
- Product sign-off: pending
- Architecture sign-off: pending
- Security sign-off: pending
- Operations sign-off: pending
- Missing input blocker token: none
- ADR path: docs/blueprint/architecture/decisions/ADR-issue-171-managed-cache.md
- ADR status: proposed
- SPEC_READY_EXCEPTION: none
- authorized-by: none

## Applicable Guardrail Controls (Normative)
- Applicable control IDs: SDD-C-002, SDD-C-003, SDD-C-004, SDD-C-005, SDD-C-006, SDD-C-007, SDD-C-008, SDD-C-009, SDD-C-010, SDD-C-011, SDD-C-012, SDD-C-013, SDD-C-014, SDD-C-015, SDD-C-016, SDD-C-017, SDD-C-019, SDD-C-020, SDD-C-021
- Control exception rationale: SDD-C-001 excluded — no missing inputs blocking the spec; SDD-C-018 excluded — no blueprint upstream workarounds; SDD-C-022/SDD-C-023 excluded — no HTTP route handlers or payload-transform logic; SDD-C-024 excluded — no pre-PR smoke/deterministic failures at intake.

## Implementation Stack Profile (Normative)
- Backend stack profile: n/a — tooling/infrastructure-only change
- Frontend stack profile: n/a — tooling/infrastructure-only change
- Test automation profile: pytest
- Agent execution model: specialized-subagents-isolated-worktrees
- Managed service preference: stackit-managed-first
- Managed service exception rationale: Local lane uses bitnami/redis Helm chart — no STACKIT-equivalent managed Redis service exists for Docker Desktop; same exception class as postgres, rabbitmq, and opensearch local lanes.
- Runtime profile: local-first-docker-desktop-kubernetes
- Local Kubernetes context policy: docker-desktop-preferred
- Local provisioning stack: crossplane-plus-helm
- Runtime identity baseline: eso-plus-argocd-plus-keycloak
- Local-first exception rationale: none

## Objective
- Business outcome: Add a first-class `managed-cache` optional module that provisions STACKIT Managed Redis on the STACKIT lane and a bitnami/redis instance on the local lane, exposing a stable shell and ESO credential contract (`MANAGED_CACHE_HOST`, `MANAGED_CACHE_PORT`, `MANAGED_CACHE_PASSWORD`, `MANAGED_CACHE_URI`) to consumer workloads. Eliminates bespoke Redis wiring in each consumer and establishes the prerequisite for the `platform-email` module (issue #172, which requires Redis as part of Postal's backing infrastructure).
- Success metric: `make infra-managed-cache-apply` on a STACKIT profile provisions an instance and writes a valid `managed_cache_runtime.env`; `MANAGED_CACHE_URI` resolves to a `redis://` URI on both lanes; `python3 -m pytest tests/infra/modules/managed-cache/ -x -q` passes with ≥ 10 new assertions.

## Normative Requirements

### Functional Requirements (Normative)

- FR-001 MUST create `infra/cloud/stackit/terraform/modules/managed-cache/` containing `main.tf`, `variables.tf`, `outputs.tf`, and `versions.tf`. The module MUST provision a `stackit_redis_instance` and a `stackit_redis_credential` resource, conditioned on `var.managed_cache_enabled`. The module MUST follow the foundation-contract execution model: it is invoked by the foundation TF workspace via `resolve_optional_module_execution`, not called directly. Network ACL MUST be set via `parameters.sgw_acl` (CIDR string) aligned with SKE egress ranges — same pattern as `stackit_rabbitmq_instance`.

  > **Q-1 resolved (2026-05-27):** Resource names verified against provider registry (`stackitcloud/stackit` v0.88.x): `stackit_redis_instance` (attrs: `project_id`, `name`, `plan_name`, `version`, `parameters.sgw_acl`) and `stackit_redis_credential` (computed attrs: `host`, `port`, `username`, `password` (sensitive), `uri`). Note: unlike the initial assumption, STACKIT Redis credentials DO include a `username` attribute — the provider wraps Redis with a credential pair. Option A selected.

- FR-002 MUST wire `managed_cache_enabled` as a boolean variable in `infra/cloud/stackit/terraform/foundation/variables.tf` (default `false`). MUST add `managed_cache_*` outputs (`managed_cache_host`, `managed_cache_port`, `managed_cache_password`, `managed_cache_uri`) to `infra/cloud/stackit/terraform/foundation/outputs.tf`. MUST call the managed-cache module from the foundation TF workspace when `var.managed_cache_enabled` is true.

- FR-003 MUST create `infra/local/helm/managed-cache/values.yaml` configuring bitnami/redis with password authentication enabled, a default password, and the `managed-cache` namespace. The local lane Helm release name MUST be `blueprint-managed-cache`.

- FR-004 MUST create `scripts/lib/infra/managed_cache.sh` containing:
  - `managed_cache_seed_env_defaults()` — sets `MANAGED_CACHE_INSTANCE_NAME`, `MANAGED_CACHE_PASSWORD`, `MANAGED_CACHE_PORT` (default `6379`), `MANAGED_CACHE_NAMESPACE` (default `managed-cache`), `MANAGED_CACHE_HELM_RELEASE` (default `blueprint-managed-cache`), `MANAGED_CACHE_HELM_CHART` (default `bitnami/redis`), `MANAGED_CACHE_HELM_CHART_VERSION`.
  - `managed_cache_init_env()` — calls `managed_cache_seed_env_defaults` then `require_env_vars MANAGED_CACHE_INSTANCE_NAME`.
  - `managed_cache_host()` — returns foundation output `managed_cache_host` on STACKIT; returns `${MANAGED_CACHE_HELM_RELEASE}.${MANAGED_CACHE_NAMESPACE}.svc.cluster.local` on local lane.
  - `managed_cache_port()` — returns foundation output `managed_cache_port` on STACKIT; returns `$MANAGED_CACHE_PORT` on local lane.
  - `managed_cache_username()` — returns foundation output `managed_cache_username` on STACKIT; returns empty string on local lane (bitnami/redis uses password-only auth with the default user).
  - `managed_cache_password()` — returns foundation output `managed_cache_password` on STACKIT; returns `$MANAGED_CACHE_PASSWORD` on local lane.
  - `managed_cache_uri()` — on STACKIT: reads foundation output `managed_cache_uri` directly (provider-generated, includes username). On local lane: constructs `redis://:<password>@<host>:<port>/0` (password-only; no username for bitnami/redis default user).

- FR-005 MUST create `scripts/bin/infra/managed_cache_plan.sh`, `managed_cache_apply.sh`, `managed_cache_smoke.sh`, and `managed_cache_destroy.sh` following the rabbitmq bin script pattern. The apply script MUST write `managed_cache_runtime.env` via `write_state_file` with keys: `profile`, `stack`, `host`, `port`, `uri`. The apply script MUST NOT write `password` to the state file (SDD-C-009).

- FR-006 MUST create `blueprint/modules/managed-cache/module.contract.yaml` following the `OptionalModuleContract` schema. MUST declare `MANAGED_CACHE_ENABLED` as `enable_flag`, outputs `MANAGED_CACHE_HOST`, `MANAGED_CACHE_PORT`, `MANAGED_CACHE_PASSWORD`, `MANAGED_CACHE_URI`, make targets `infra-managed-cache-plan/apply/smoke/destroy`, and path entries for terraform, helm, docs, and tests.

- FR-007 MUST register the module in `blueprint/contract.yaml` under `optional_modules`.

- FR-008 MUST add `infra-managed-cache-plan`, `infra-managed-cache-apply`, `infra-managed-cache-smoke`, and `infra-managed-cache-destroy` make targets to `make/blueprint.generated.mk` and its template `scripts/templates/blueprint/bootstrap/make/blueprint.generated.mk.tmpl`. All four MUST appear in `.PHONY`.

- FR-009 MUST create `tests/infra/modules/managed-cache/test_managed_cache_module.py` with ≥ 10 assertions covering: module contract file exists; `MANAGED_CACHE_ENABLED` flag declared; all four outputs declared; `managed_cache_host/port/password/uri` functions present in shell lib; `infra-managed-cache-apply` target in Makefile template; TF module `main.tf` exists; runtime state MUST NOT contain password.

- FR-010 MUST create `docs/platform/modules/managed-cache/README.md` documenting: activation (`MANAGED_CACHE_ENABLED=true`), required inputs, produced outputs, `MANAGED_CACHE_URI` format, make target usage, rollback procedure, and the relationship to `platform-email` (issue #172).

- FR-011 MUST mirror bootstrap template files to `scripts/templates/infra/bootstrap/` for: `infra/local/helm/managed-cache/values.yaml`, Makefile template targets, and `blueprint/modules/managed-cache/module.contract.yaml`.

### Non-Functional Requirements (Normative)

- NFR-SEC-001 The apply script MUST NOT write `MANAGED_CACHE_PASSWORD` to `managed_cache_runtime.env`. Password MUST be retrieved at runtime via `managed_cache_password()` (which reads from foundation TF output on STACKIT or env var on local lane) — never persisted to disk in cleartext.

- NFR-SEC-002 The STACKIT TF module MUST declare a network ACL that aligns with SKE egress CIDR ranges (same `auto_align_with_ske_egress_ranges: true` pattern as postgres). Default open-world access (`0.0.0.0/0`) MUST NOT be the sole ACL entry.

- NFR-OPS-001 The module MUST be disabled by default (`MANAGED_CACHE_ENABLED=false`). Existing consumers that do not set `MANAGED_CACHE_ENABLED=true` MUST be completely unaffected.

- NFR-OPS-002 The smoke script MUST validate that `MANAGED_CACHE_URI` is non-empty and matches the `redis://` URI scheme on both lanes.

- NFR-A11Y-001 N/A — no UI surfaces introduced or modified.

## Normative Option Decision
- Option A: bitnami/redis Helm chart for local lane (consistent with rabbitmq, opensearch, postgres local patterns)
- Option B: custom Redis deployment using official `redis` Docker image with manual K8s manifests
- Selected option: OPTION_A
- Rationale: bitnami/redis is the established local-lane pattern for managed services in this blueprint. Consistency with existing modules reduces cognitive overhead for platform engineers and consumers. The bitnami deprecation concern (see issue #324 for postgres) is noted as a deferred proposal.

## Contract Changes (Normative)
- Config/Env contract: New optional env vars — `MANAGED_CACHE_ENABLED`, `MANAGED_CACHE_INSTANCE_NAME`, `MANAGED_CACHE_PASSWORD`, `MANAGED_CACHE_PORT` (default `6379`), `MANAGED_CACHE_NAMESPACE` (default `managed-cache`), `MANAGED_CACHE_HELM_RELEASE`, `MANAGED_CACHE_HELM_CHART`, `MANAGED_CACHE_HELM_CHART_VERSION`. New outputs — `MANAGED_CACHE_HOST`, `MANAGED_CACHE_PORT`, `MANAGED_CACHE_USERNAME`, `MANAGED_CACHE_PASSWORD`, `MANAGED_CACHE_URI`.
- API contract: none
- OpenAPI / Pact contract path: none
- Event contract: none
- Make/CLI contract: New targets — `infra-managed-cache-plan`, `infra-managed-cache-apply`, `infra-managed-cache-smoke`, `infra-managed-cache-destroy`. All additive; no existing targets changed.
- Docs contract: New `docs/platform/modules/managed-cache/README.md`. No existing docs changed.

## Blueprint Upstream Defect Escalation (Normative)
- Upstream issue URL: none
- Temporary workaround path: none
- Replacement trigger: none
- Workaround review date: none

## Normative Acceptance Criteria

- AC-001 `make infra-managed-cache-apply` on a STACKIT profile with `MANAGED_CACHE_ENABLED=true` provisions a Redis instance and writes `managed_cache_runtime.env` containing `host`, `port`, and `uri` keys (no `password` key).
- AC-002 `MANAGED_CACHE_URI` returned by `managed_cache_uri()` matches `redis://:.+@.+:[0-9]+/0` on both lanes.
- AC-003 `make infra-managed-cache-smoke` passes on both lanes when the module is applied.
- AC-004 An existing consumer with `MANAGED_CACHE_ENABLED=false` (the default) is completely unaffected by the presence of this module.
- AC-005 `python3 -m pytest tests/infra/modules/managed-cache/ -x -q` passes with ≥ 10 assertions.

## Informative Notes (Non-Normative)
- Context: This module is the prerequisite for issue #172 (platform-email / Postal), which requires a Redis backing store. Four independent consumer use cases drive the demand: server-side session store (Keycloak JWT overflow), rate-limiting counter store, inbox idempotency cache, and Postal's internal dependency.
- Tradeoffs: bitnami/redis is used for local lane consistency. The bitnami deprecation concern (tracked in issue #324 for postgres) applies equally here — if a local-lane bitnami migration is eventually done for postgres (#324), this module follows the same migration scope. Noted as a deferred proposal.
- Clarifications:
  - Q-1 resolved: `stackit_redis_instance` + `stackit_redis_credential` confirmed from provider registry. Credential includes `username`, `password`, `host`, `port`, `uri`. Network ACL via `parameters.sgw_acl`. See FR-001 for detail.

## Explicit Exclusions
- Redis Cluster / Sentinel HA mode: single-instance provisioning only; HA requires separate capacity planning.
- Custom Redis ACL users: STACKIT Managed Redis uses password-only auth; per-user ACL is not exposed by the provider.
- Redis Pub/Sub or Stream contract: no blueprint-level contract; consumer-owned concern.
- KMS envelope encryption of the Redis password at rest in Secrets Manager: out of scope; KMS module concern (same deferral as issue #312 Proposal C).
- bitnami/redis local lane migration away from bitnami: tracked by issue #324 pattern; deferred.
