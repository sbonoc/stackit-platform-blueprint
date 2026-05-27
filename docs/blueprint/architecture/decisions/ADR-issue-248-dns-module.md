# ADR: Issue #248 — DNS Module Implementation (STACKIT-Only, Multi-Zone)

- **Status**: approved
- **ADR technical decision sign-off**: approved
- **Date**: 2026-05-17
- **Issue**: #248
- **Work item**: `specs/2026-05-17-issue-248-dns-module/`

## Context

`infra/cloud/stackit/terraform/modules/dns/main.tf` was a 7-line stub with no `stackit_dns_zone` resource declared. All four DNS scripts (`dns_plan.sh`, `dns_apply.sh`, `dns_smoke.sh`, `dns_destroy.sh`) and the `dns.sh` library already existed. Three gaps remained:

1. The standalone Terraform module had no provider resources — it could not be used for isolated DNS zone provisioning.
2. `dns_smoke.sh` validated only `zone_name` — `zone_id` and `zone_fqdn` were not checked, leaving the runtime contract partially unvalidated.
3. No automated test contract existed (`tests/infra/modules/dns/test_contract.py` was missing).

STACKIT DNS has no local-lane equivalent. The local driver is `noop` by design, consistent with other STACKIT-only optional modules (kms, secrets-manager).

Two open questions were resolved by direct inspection of the stackitcloud/terraform-provider-stackit source at v0.88.0: `stackit_dns_zone` exposes `primary_name_server` as a single computed FQDN per zone (no plural nameservers attribute); no DNSSEC attribute exists in v0.88.0. Both resolutions are recorded in spec.md Q-1 and Q-2.

The scope was subsequently expanded to multi-zone support (for_each over a list of FQDNs) after reviewing an existing consumer reference implementation that provisions multiple DNS zones per consumer environment. Decisions D-1 and D-3 were updated accordingly.

## Decisions

### D-1: Multi-zone `for_each` over `dns_zone_fqdns` — mirrors foundation pattern

Implement `infra/cloud/stackit/terraform/modules/dns/main.tf` with `stackit_dns_zone.this` using `for_each = toset(var.dns_zone_fqdns)`. Attributes per zone: `project_id`, `name`, `dns_name = trimsuffix(each.value, ".")`, and `default_ttl`. The `region` attribute is not used — it is not exposed by the STACKIT DNS provider in v0.88.0 and not used by the foundation.

This mirrors the foundation pattern exactly (`infra/cloud/stackit/terraform/foundation/main.tf` uses the same `for_each = toset(local.dns_zone_fqdns)` structure).

**Rejected alternative:** Single-zone module provisioning exactly one zone via a string variable (`dns_zone_fqdn`). Rejected because consumer reference implementations provision multiple zones per environment (e.g., web + auth zones); a single-zone module requires callers to wrap it in their own `for_each`, which is worse than providing the multi-zone API directly.

### D-2: `dns_name` uses `trimsuffix(each.value, ".")` — trailing dot stripped before provider call

The STACKIT provider expects `dns_name` without a trailing dot. The foundation strips the dot via `trimsuffix` in `local.dns_zone_dns_names`. The standalone module applies the same transformation inline in the resource block, keeping the caller API (`DNS_ZONE_FQDNS` with trailing dots) consistent with how FQDNs are declared in the module contract.

**Rejected alternative:** Accept the FQDN with trailing dot and rely on provider normalisation — rejected; the foundation explicitly strips it, suggesting provider validation rejects the trailing dot.

### D-3: Zone display name uses `{dns_naming_prefix}-dns-{sha1(fqdn)[0:8]}` — hash suffix for collision resistance

With multi-zone `for_each`, each zone must have a unique display name within the STACKIT project. The display name is derived as `substr("${var.dns_naming_prefix}-dns-${substr(sha1(each.value), 0, 8)}", 0, 63)` — matching the foundation's pattern exactly.

The consumer controls the `dns_naming_prefix` part (e.g., `dhe-marketplace-web-dev` — the shell layer constructs this as `${DNS_NAMING_PREFIX}-${active_stack}`). The SHA1 suffix over the FQDN ensures uniqueness when multiple zones share the same prefix. The full name is capped at 63 characters.

**Rejected alternative (original single-zone):** Use `var.dns_zone_name` directly without a hash suffix. This was correct for single-zone because the consumer controls uniqueness; it is not correct for multi-zone `for_each` where multiple zones with the same prefix would collide.

**Rejected alternative (full SHA1):** Use the full 40-character SHA1 hash. Rejected; 8 characters provide sufficient collision resistance for the zone counts expected within a single STACKIT project and keep the display name human-readable.

### D-4: No `lifecycle { create_before_destroy = true }` on `stackit_dns_zone.this`

DNS zones must not be silently recreated. Zone recreation:
- Invalidates zone IDs referenced by downstream modules (`public-endpoints`).
- Requires re-delegating nameservers at the registrar, which has propagation delays of up to 48 hours.
- Drops all existing DNS records until re-provisioned.

Create-before-destroy would attempt to create a new zone with the same FQDN while the old one still exists — this would fail at the provider level (duplicate zone name). Deliberate zone replacement requires an explicit destroy + apply with coordinated record migration.

**Rejected alternative:** Include `lifecycle { create_before_destroy = true }` for consistency with other modules — rejected; the risks of silent zone recreation outweigh the consistency benefit. The secrets-manager module's `create_before_destroy` applies to credential resources where short overlap is safe; DNS zones have no such overlap window.

### D-5: Smoke validates `zone_count`, `zone_ids`, and `primary_name_servers` (multi-zone contract)

The runtime state after apply contains `zone_ids` (space-separated), `zone_fqdns` (space-separated), `zone_count`, and `primary_name_servers` (space-separated). The smoke script validates:

- `zone_count` is a positive integer (≥ 1) — confirms at least one zone was provisioned.
- `zone_ids` is non-empty — confirms STACKIT assigned IDs to all zones.
- `primary_name_servers` is non-empty — confirms all zones are fully provisioned (Q-1 resolution).

This extends the original single-key smoke to a multi-zone contract, consistent with the KMS pattern (which validates `key_ring_id`, `key_id`, and `endpoint`). The strengthening is additive — it does not change the smoke exit code for correctly applied zones.

**Rejected alternative:** Validate each zone ID individually by iterating the space-separated list in bash. Rejected; non-empty string check on the joined value is sufficient to confirm provisioning success. Per-zone validation adds bash complexity without additional safety guarantee for the common failure mode (TF apply error before any zone is created).

## Consequences

- Standalone Terraform module enables isolated multi-zone DNS provisioning without the foundation layer.
- `zone_ids`, `zone_fqdns`, `zone_count`, and `primary_name_servers` are written to runtime state and validated by smoke — strengthens the operational contract for multi-zone consumers.
- Q-1 resolved: `primary_name_server` (per-zone, Computed) exposed as `primary_name_servers` map output; added to `outputs.tf`, `module.contract.yaml`, `dns_apply.sh`, and `dns_smoke.sh`. Q-2 resolved: DNSSEC not configurable in v0.88.0; documented in module README.
- DNS zone destruction is destructive — module README warns consumers explicitly with propagation delay and record loss details.
- Shell layer (`dns.sh`) constructs `{DNS_NAMING_PREFIX}-{active_stack}` as the naming prefix and exposes `dns_zone_ids()`, `dns_zone_count()`, `dns_primary_name_servers()` helper functions for consumers.
- External DNS record management (K8s-native dynamic record lifecycle) is explicitly out of scope — deferred to a separate external-DNS module proposal (parked in AGENTS.backlog.md under `on-scope: infra`).
