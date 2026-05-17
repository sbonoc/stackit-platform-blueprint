# ADR: Issue #248 — DNS Module Implementation (STACKIT-Only)

- **Status**: approved
- **ADR technical decision sign-off**: approved
- **Date**: 2026-05-17
- **Issue**: #248
- **Work item**: `specs/2026-05-17-issue-248-dns-module/`

## Context

`infra/cloud/stackit/terraform/modules/dns/main.tf` is a 7-line stub with no `stackit_dns_zone` resource declared. All four DNS scripts (`dns_plan.sh`, `dns_apply.sh`, `dns_smoke.sh`, `dns_destroy.sh`) and the `dns.sh` library already exist and are functional. Two gaps remain:

1. The standalone Terraform module has no provider resources — it cannot be used for isolated DNS zone provisioning.
2. `dns_smoke.sh` validates only `zone_name` — `zone_id` and `zone_fqdn` are not checked, leaving the runtime contract partially unvalidated.
3. No automated test contract exists (`tests/infra/modules/dns/test_contract.py` is missing).

STACKIT DNS has no local-lane equivalent. The local driver is `noop` by design, consistent with other STACKIT-only optional modules (kms, observability, secrets-manager).

Two open questions were resolved by direct inspection of the stackitcloud/terraform-provider-stackit source at v0.88.0: `stackit_dns_zone` exposes `primary_name_server` as a single computed FQDN (no plural nameservers attribute); no DNSSEC attribute exists in v0.88.0. Both resolutions are recorded in spec.md Q-1 and Q-2.

## Decisions

### D-1: Standalone Terraform module mirrors foundation pattern (`project_id`, `name`, `dns_name` only)

Implement `infra/cloud/stackit/terraform/modules/dns/main.tf` with `stackit_dns_zone.this` using attributes `project_id`, `name`, and `dns_name = trimsuffix(var.dns_zone_fqdn, ".")`. This mirrors `infra/cloud/stackit/terraform/foundation/main.tf` exactly.

The foundation does not pass `region`, nameservers, or DNSSEC attributes to `stackit_dns_zone` — their absence in the foundation is strong evidence these attributes are either not supported or not required by the provider in v0.88.0.

**Rejected alternative:** Include plural nameservers output or DNSSEC variable. Q-1 resolved: `primary_name_server` (single FQDN, Computed) is the only nameserver attribute in v0.88.0 — added to `outputs.tf` and `module.contract.yaml` as `DNS_PRIMARY_NAME_SERVER`. Q-2 resolved: no DNSSEC attribute in v0.88.0; DNSSEC is STACKIT platform-managed and documented in the module README.

### D-2: `dns_name` uses `trimsuffix(var.dns_zone_fqdn, ".")` — trailing dot stripped before provider call

The STACKIT provider expects `dns_name` without a trailing dot. The foundation strips the dot via `trimsuffix` in `local.dns_zone_dns_names`. The standalone module applies the same transformation inline in the resource block, keeping the caller API (`dns_zone_fqdn` with trailing dot) consistent with how `DNS_ZONE_FQDN` is declared in the module contract and used by `dns.sh`.

**Rejected alternative:** Accept the FQDN with trailing dot and rely on provider normalisation — rejected; the foundation explicitly strips it, suggesting provider validation rejects the trailing dot.

### D-3: `name` attribute uses `var.dns_zone_name` directly (no hash suffix)

The foundation uses a computed name with a SHA1 hash suffix (`"${naming_prefix}-dns-${substr(sha1(each.value), 0, 8)}"`) because it manages multiple zones in a `for_each` and needs globally unique display names. The standalone module provisions exactly one zone; the consumer controls the display name via `dns_zone_name` and is responsible for uniqueness within their STACKIT project.

**Rejected alternative:** Apply the same hash suffix as the foundation — rejected; it adds complexity and hides the consumer-specified name, making resource identification in the STACKIT console harder for standalone users.

### D-4: No `lifecycle { create_before_destroy = true }` on `stackit_dns_zone.this`

DNS zones must not be silently recreated. Zone recreation:
- Invalidates the `zone_id` referenced by downstream modules (`public-endpoints`).
- Requires re-delegating nameservers at the registrar, which has propagation delays.
- Drops all existing DNS records until re-provisioned.

Create-before-destroy would attempt to create a new zone with the same FQDN while the old one still exists — this would fail at the provider level (duplicate zone name). Deliberate zone replacement requires an explicit destroy + apply with coordinated record migration.

**Rejected alternative:** Include `lifecycle { create_before_destroy = true }` for consistency with other modules — rejected; the risks of silent zone recreation outweigh the consistency benefit. The secrets-manager module's `create_before_destroy` applies to credential resources where short overlap is safe; DNS zones have no such overlap window.

### D-5: Smoke strengthening adds `zone_id`, `zone_fqdn`, and `primary_name_server` checks (additive, non-breaking)

The existing smoke check validates only `zone_name`. `zone_id` is the primary downstream reference (used by `public-endpoints` to create DNS records), `zone_fqdn` is the canonical contract output, and `primary_name_server` confirms the STACKIT DNS zone is fully provisioned (resolves Q-1). All three MUST be validated non-empty after apply, consistent with the KMS pattern (which validates `key_ring_id`, `key_id`, and `endpoint`). The strengthening is additive — it does not change the smoke exit code for correctly applied zones.

## Consequences

- Standalone Terraform module enables isolated DNS zone provisioning without the foundation layer.
- `zone_id`, `zone_name`, `zone_fqdn`, and `primary_name_server` are all written to runtime state and validated by smoke — strengthens the operational contract.
- Q-1 resolved: `primary_name_server` added to `outputs.tf`, `module.contract.yaml`, `dns_apply.sh`, and `dns_smoke.sh`. Q-2 resolved: DNSSEC not configurable in v0.88.0; documented in module README.
- DNS zone destruction is destructive — module README must warn consumers explicitly.
- No changes to existing shell scripts except `dns_smoke.sh` (additive zone_id, zone_fqdn, and primary_name_server checks) and `dns_apply.sh` (primary_name_server state write).
