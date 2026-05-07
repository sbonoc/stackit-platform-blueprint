# ADR: Issue #248 — RabbitMQ Module Implementation (Dual-Lane)

- **Status**: proposed
- **ADR technical decision sign-off**: pending
- **Date**: 2026-05-07
- **Issue**: #248
- **Work item**: `specs/2026-05-07-issue-248-rabbitmq-module/`

## Context

The `infra/cloud/stackit/terraform/modules/rabbitmq/main.tf` is a 7-line stub (no provider resources declared). Unlike other modules, the rabbitmq module's script and credential layer is already in a good state: the execution class is correctly set to `fallback_runtime` for the local lane and `provider_backed` for the STACKIT lane; the Helm values already use `existingPasswordSecret` instead of plaintext credentials; and `rabbitmq_reconcile_runtime_secret` / `rabbitmq_delete_runtime_secret` are already implemented.

The remaining gaps are:

1. The STACKIT standalone Terraform module has no resources — `stackit_rabbitmq_instance` and `stackit_rabbitmq_credential` are not declared.
2. Two contract outputs are missing from `module.contract.yaml`: `RABBITMQ_VHOST` and `RABBITMQ_MANAGEMENT_URL`. The STACKIT `stackit_rabbitmq_credential` resource exposes a `management` attribute (the management dashboard URL) but no `vhost` attribute.
3. Shell helper functions `rabbitmq_vhost()` and `rabbitmq_management_url()` do not exist.
4. The `rabbitmq_apply.sh` state file write is missing two keys.
5. Smoke validations are minimal (URI prefix only).
6. No automated tests or module documentation exist.

## Decisions

### D-1: Additive standalone Terraform module mirroring foundation pattern

Implement `infra/cloud/stackit/terraform/modules/rabbitmq/` as a standalone module with `stackit_rabbitmq_instance` and `stackit_rabbitmq_credential` resources, mirroring the foundation pattern in `infra/cloud/stackit/terraform/foundation/main.tf`. The foundation layer continues to manage its own inline resources; the standalone module is for isolated use.

The instance resource includes `lifecycle { create_before_destroy = true }` to minimise downtime during instance replacement.

**Rejected alternative:** Have the foundation call the standalone module — rejected due to Terraform state migration risk with no active consumer driver for the refactor.

### D-2: `RABBITMQ_VHOST` defaults to constant `/` on both lanes (Q-1 resolved 2026-05-07)

The STACKIT `stackit_rabbitmq_credential` resource exposes no `vhost` attribute (confirmed from provider source code and foundation usage). The RabbitMQ default vhost is `/`, which is correct for the generic module use case. `rabbitmq_vhost()` returns the constant string `/` on both lanes. Consumer-side vhost management is out of scope.

Making vhost a configurable input would create a false promise since the STACKIT lane cannot honour a non-default vhost at the credential level; the constant avoids that design trap.

**Rejected alternative:** Expose `vhost` as a configurable input variable — rejected because the STACKIT provider cannot populate this from credential attributes; the value would be user-supplied with no provider-side validation or enforcement.

### D-3: `RABBITMQ_MANAGEMENT_URL` — provider `management` attribute on STACKIT, constructed URL on local lane

The STACKIT `stackit_rabbitmq_credential` resource exposes a `management` attribute containing the management dashboard URL. The foundation outputs file is updated to expose this as `rabbitmq_management_url` (not `rabbitmq_management`) so the shell layer can read it via `stackit_foundation_output_value_or_default "rabbitmq_management_url"`.

The `_url` suffix in the foundation output key name is intentional — it makes the value type explicit and is consistent with the blueprint convention for URL-valued outputs.

On the local lane, `rabbitmq_management_url()` constructs the URL from `rabbitmq_host` and the Bitnami management plugin port (15672), which is the stable default for the Bitnami RabbitMQ Helm chart.

**Rejected alternative:** Name the foundation output `rabbitmq_management` to mirror the provider attribute — rejected because the blueprint shell convention uses `_url` suffix for URL-valued outputs; naming consistency across the blueprint layer takes precedence over mirroring provider attribute names exactly.

### D-4: Additive state file keys — no existing key renames

The two new state file keys (`vhost`, `management_url`) follow the prefix-strip convention from `RABBITMQ_VHOST` and `RABBITMQ_MANAGEMENT_URL`. Existing keys (`host`, `port`, `username`, `password`, `uri`) are unchanged — no breaking change to any existing consumer reading `artifacts/infra/rabbitmq_runtime.env`.

**Rejected alternative:** Rename existing keys to match the prefix-strip convention — rejected because existing consumers may read these keys directly and there is no failing test suite signalling the misalignment; the additive approach is lower risk.

## Consequences

- STACKIT standalone Terraform module enables isolated RabbitMQ provisioning outside the foundation deployment pattern.
- `RABBITMQ_VHOST` is consistently `/` on both lanes; no consumer needs to configure it for the default vhost use case.
- `RABBITMQ_MANAGEMENT_URL` is available in the runtime state artifact and via ESO-synced env vars, enabling operators and consumers to reach the management UI without manual lookup.
- Foundation outputs file gains `rabbitmq_management_url` output — additive, no breaking change to existing foundation consumers.
- Runtime state file gains two new keys — additive, fully backward compatible.
