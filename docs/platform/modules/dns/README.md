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
- `stackit-*` profiles: managed by Terraform `foundation` layer (`infra/cloud/stackit/terraform/foundation`) with `DNS_ENABLED` contract flag.
  - `DNS_ZONE_FQDN` is the canonical provisioning input passed to foundation.
  - The consumer-facing FQDN may keep its trailing dot; foundation trims it only when calling STACKIT provider resources.
  - `DNS_ZONE_NAME` is the consumer-facing alias used in runtime artifacts, and `DNS_ZONE_ID` resolves from foundation outputs after apply.
- `local-*` profiles: no managed DNS counterpart; module plan/apply is a no-op contract stub.
