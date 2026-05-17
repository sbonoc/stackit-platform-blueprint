# Architecture

## Context
- Work item: 2026-05-17-issue-248-dns-module
- Owner: sbonoc
- Date: 2026-05-17

## Stack and Execution Model
- Backend stack profile: n/a — tooling/infrastructure-only change
- Frontend stack profile: n/a — tooling/infrastructure-only change
- Test automation profile: pytest
- Agent execution model: specialized-subagents-isolated-worktrees

## Problem Statement
- What needs to change and why: `infra/cloud/stackit/terraform/modules/dns/main.tf` is a 7-line stub with no `stackit_dns_zone` resource. The module cannot be used standalone for isolated DNS zone provisioning. Additionally, `dns_smoke.sh` validates only `zone_name`, leaving `zone_id` and `zone_fqdn` unchecked. No test contract file exists for the DNS module.
- Scope boundaries: Standalone Terraform module implementation, smoke check strengthening, and test contract. All four DNS scripts and the `dns.sh` library are already in place.
- Out of scope: DNS record management, local-lane equivalent, multi-zone provisioning. Q-1 resolved (primary_name_server added). Q-2 resolved (DNSSEC not configurable in v0.88.0; platform-managed).

## Bounded Contexts and Responsibilities

- **Standalone TF module** (`infra/cloud/stackit/terraform/modules/dns/`): Isolated provisioning context. Declares one `stackit_dns_zone.this` resource. Accepts caller-supplied `stackit_project_id`, `dns_zone_name`, `dns_zone_fqdn`. Exposes `zone_id`, `dns_name`, and `primary_name_server` as outputs. No dependency on the foundation layer.
- **Shell layer** (`scripts/lib/infra/dns.sh`, `scripts/bin/infra/dns_*.sh`): Orchestration context. Already implemented. Reads zone contract from foundation outputs (STACKIT lane) or returns defaults (local lane). Writes `zone_id`, `zone_name`, `zone_fqdn`, `primary_name_server` to runtime state. Smoke validates all four keys are non-empty.
- **Test contract** (`tests/infra/modules/dns/test_contract.py`): Quality context. Static assertions against TF module file structure, state key presence, and smoke logic — no live infrastructure required.

## High-Level Component Design

```mermaid
flowchart TD
    A["infra-dns-apply\n(dns_apply.sh)"] -->|foundation_contract driver| B["Foundation TF layer\n(stackit_dns_zone.foundation)"]
    A -->|noop driver| C["No-op\n(local profiles)"]
    B --> D["foundation outputs\ndns_zone_ids map"]
    D --> E["dns_zone_id()\n(dns.sh)"]
    E --> F["dns_runtime.env\nzone_id, zone_name, zone_fqdn, primary_name_server"]
    F --> G["dns_smoke.sh\nvalidates zone_id, zone_name, zone_fqdn, primary_name_server"]
    H["Standalone TF module\n(dns/main.tf)"] -->|isolated use| I["stackit_dns_zone.this\nzone_id, dns_name outputs"]
```

_Foundation flow (left): apply.sh drives foundation TF and reads zone_id from the output map. Standalone module (right): isolated direct provisioning without the foundation layer._

## Integration and Dependency Edges
- Upstream dependencies: `stackit_project_access` capability (confirmed via `dns_service_available` dependency in module.contract.yaml); STACKIT provider v0.88.0.
- Downstream dependencies: `public-endpoints` module references `DNS_ZONE_ID` and `DNS_ZONE_FQDN` for CNAME/A record creation via ingress controller.
- Data/API/event contracts touched: `artifacts/infra/dns_runtime.env` (keys: `zone_id`, `zone_name`, `zone_fqdn`, `primary_name_server`); `blueprint/modules/dns/module.contract.yaml` (DNS_PRIMARY_NAME_SERVER added to outputs.produced in this work item via FR-004b).

## Non-Functional Architecture Notes
- Security: DNS zones carry no credentials. `zone_id` is a non-sensitive identifier. No secret store interaction required.
- Observability: Smoke check validates four state keys (zone_id, zone_name, zone_fqdn, primary_name_server). Script output prefixed `[dns]`. Runtime state file is the operational artifact for operators.
- Reliability and rollback: `lifecycle { create_before_destroy = true }` MUST NOT be used on `stackit_dns_zone.this` — zone recreation requires coordinated record migration. Rollback is destroy + re-apply with confirmed record re-registration.
- Monitoring/alerting: No alerting additions. Smoke exit code is the operational health signal.

## Risks and Tradeoffs

- Risk 1 — Provider schema (resolved): Q-1 confirmed `primary_name_server` (single Computed FQDN) is the only nameserver attribute in v0.88.0. Q-2 confirmed no DNSSEC attribute exists; DNSSEC is STACKIT platform-managed. Both resolutions are now implemented in the spec and will be implemented in the module.
- Risk 2 — DNS zone deletion is destructive: Unlike most resources, deleting a DNS zone that has live records propagated to external resolvers causes immediate resolution failures. The destroy sequence has no grace period. Consumers must be warned in the module README.
- Tradeoff 1 — Single zone per module invocation vs. multi-zone: The foundation uses `for_each` to provision multiple zones. The standalone module provisions exactly one. This is simpler and sufficient for isolated use; multi-zone support is a future follow-up if needed.
