# DNS Module (Optional)

<!-- BEGIN GENERATED MODULE CONTRACT SUMMARY -->
## Contract Summary
- Purpose: Provision managed DNS zones and publish canonical domain contract.
- Enable flag: `DNS_ENABLED` (default: `false`)
- Required inputs:
  - `DNS_ZONE_FQDNS`
  - `DNS_NAMING_PREFIX`
- Make targets:
  - `infra-dns-plan`
  - `infra-dns-apply`
  - `infra-dns-smoke`
  - `infra-dns-destroy`
- Outputs:
  - `DNS_ZONE_IDS`
  - `DNS_ZONE_COUNT`
  - `DNS_ZONE_FQDNS`
  - `DNS_PRIMARY_NAME_SERVERS`
<!-- END GENERATED MODULE CONTRACT SUMMARY -->

## Stack Execution Model

- Optional module Make targets are materialized by `make blueprint-render-makefile` (or `make blueprint-bootstrap`) when `DNS_ENABLED=true`.
- Scaffolding paths are materialized by `make infra-bootstrap` only when `DNS_ENABLED=true`.
- `stackit-*` profiles: managed by the standalone Terraform module (`infra/cloud/stackit/terraform/modules/dns/`) and the `foundation` layer (`infra/cloud/stackit/terraform/foundation`) with `DNS_ENABLED` contract flag.
  - `DNS_ZONE_FQDNS` is the space-separated list of zone FQDNs passed to provisioning (e.g., `marketplace-web-dev.runs.onstackit.cloud. marketplace-auth-dev.runs.onstackit.cloud.`).
  - FQDN subdomain labels must use hyphens — the STACKIT DNS provider does not accept dots within subdomain labels (e.g., `marketplace-web-dev.runs.onstackit.cloud.` not `marketplace.dev.runs.onstackit.cloud.`).
  - `DNS_NAMING_PREFIX` is the consumer-supplied display name prefix (e.g., `dhe-marketplace-web`). The shell layer appends the active stack suffix before passing to Terraform as `dns_naming_prefix`.
  - Each zone's Terraform display name is derived as `{dns_naming_prefix}-dns-{sha1(fqdn)[0:8]}` — collision-resistant and human-readable in the STACKIT console.
  - `DNS_ZONE_IDS`, `DNS_ZONE_COUNT`, and `DNS_PRIMARY_NAME_SERVERS` resolve from TF module outputs after apply.
- `local-*` profiles: no managed DNS counterpart; module plan/apply is a no-op contract stub.

## Standalone Terraform Module

The standalone module (`infra/cloud/stackit/terraform/modules/dns/`) provisions one or more STACKIT DNS zones independently of the foundation layer.

### Module Inputs

| Variable | Type | Required | Default | Description |
|---|---|---|---|---|
| `stackit_project_id` | string | yes | — | STACKIT project UUID |
| `stackit_region` | string | no | `eu01` | STACKIT region |
| `dns_zone_fqdns` | list(string) | yes | — | FQDNs to provision (trailing dot included) |
| `dns_naming_prefix` | string | yes | — | Display name prefix — TF appends `-dns-{hash}` |
| `dns_record_ttl` | number | no | `300` | Default TTL for zone records (seconds) |

### Module Outputs

| Output | Type | Description |
|---|---|---|
| `zone_ids` | map(string) | FQDN → STACKIT zone ID |
| `dns_names` | list(string) | DNS names without trailing dot |
| `primary_name_servers` | map(string) | FQDN → STACKIT-assigned primary nameserver FQDN |

## Runtime State Contract

After `make infra-dns-apply`, the following keys are written to the DNS runtime state file:

| Key | Example value | Description |
|---|---|---|
| `zone_ids` | `abc123 def456` | Space-separated STACKIT zone IDs (one per FQDN) |
| `zone_fqdns` | `marketplace-web-dev.runs.onstackit.cloud. marketplace-auth-dev.runs.onstackit.cloud.` | Space-separated input FQDNs |
| `zone_count` | `2` | Count of provisioned zones |
| `primary_name_servers` | `ns1.stackit.cloud. ns2.stackit.cloud.` | Space-separated STACKIT-assigned nameserver FQDNs |

After `make infra-dns-smoke`, the same keys are written to the DNS smoke state file with the following validations:

- `zone_count` is a positive integer (≥ 1).
- `zone_ids` is non-empty.
- `primary_name_servers` is non-empty.

## Naming Convention

Zone display names in the STACKIT console follow the pattern:

```
{DNS_NAMING_PREFIX}-{active_stack}-dns-{sha1(fqdn)[0:8]}
```

For example, with `DNS_NAMING_PREFIX=dhe-marketplace-web` and active stack `dev`, the zone for `marketplace-web-dev.runs.onstackit.cloud.` gets the display name:

```
dhe-marketplace-web-dev-dns-a3b4c5d6
```

The 8-character SHA1 suffix ensures no collision between zones with similar FQDNs within the same STACKIT project. The full name is capped at 63 characters by `substr(..., 0, 63)`.

## DNSSEC

DNSSEC is not configurable via this module. STACKIT DNS manages DNSSEC at the platform level. No `dnssec_enabled` variable is provided — if a future provider version exposes this attribute, it will be added as a configurable follow-up (tracked in backlog).

## Destroy Warning

> **Warning:** Destroying a DNS zone (`make infra-dns-destroy`) is irreversible and immediately disruptive.
>
> - All DNS records in the zone are deleted.
> - The zone IDs referenced by downstream modules (e.g., `public-endpoints`) become invalid.
> - Re-delegating nameservers at your registrar after zone recreation requires propagation time (up to 48 hours).
>
> Only destroy a live DNS zone after coordinating record migration and registrar re-delegation.
