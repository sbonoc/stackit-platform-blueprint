# DNS Module (Optional)

## Purpose
Provision managed DNS zones for marketplace public endpoints.

## Stack Execution Model
- Optional module Make targets are materialized by `make blueprint-render-makefile` (or `make blueprint-bootstrap`) when `DNS_ENABLED=true`.
- Scaffolding paths are materialized by `make infra-bootstrap` only when `DNS_ENABLED=true`.
- `stackit-*` profiles: managed by Terraform `foundation` layer (`infra/cloud/stackit/terraform/foundation`) with `DNS_ENABLED` contract flag.
  - `DNS_ZONE_FQDN` is the canonical provisioning input passed to foundation.
  - `DNS_ZONE_NAME` remains the consumer-facing alias used in runtime artifacts, and `DNS_ZONE_ID` resolves from foundation outputs after apply.
- `local-*` profiles: no managed DNS counterpart; module plan/apply is a no-op contract stub.

## Enable
```bash
export DNS_ENABLED=true
```

## Required Inputs
- `DNS_ZONE_NAME`
- `DNS_ZONE_FQDN`

## Commands
- `make infra-dns-plan`
- `make infra-dns-apply`
- `make infra-dns-smoke`
- `make infra-dns-destroy`

## Outputs
- `DNS_ZONE_ID`
- `DNS_ZONE_NAME`
- `DNS_ZONE_FQDN`
