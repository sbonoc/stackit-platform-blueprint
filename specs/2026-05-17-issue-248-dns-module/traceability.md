# Traceability Matrix

## Requirement-to-Delivery Mapping

| Requirement ID | Control IDs | WCAG SC | Design Element | Implementation Path(s) | Test Evidence | Documentation Evidence | Operational Evidence |
|---|---|---|---|---|---|---|---|
| FR-001 | SDD-C-005, SDD-C-011 | — | `stackit_dns_zone.this` in standalone TF module | `infra/cloud/stackit/terraform/modules/dns/main.tf` | AC-001: test_contract.py assertion | ADR-issue-248-dns-module.md | n/a |
| FR-002 | SDD-C-005, SDD-C-011 | — | `variables.tf` with five required variables | `infra/cloud/stackit/terraform/modules/dns/variables.tf` | AC-002: test_contract.py assertion | n/a | n/a |
| FR-003 | SDD-C-005, SDD-C-008 | — | `outputs.tf` with zone_id, dns_name | `infra/cloud/stackit/terraform/modules/dns/outputs.tf` | AC-003: test_contract.py assertion | n/a | n/a |
| FR-004 | SDD-C-005, SDD-C-011 | — | `versions.tf` with stackitcloud/stackit = 0.88.0 | `infra/cloud/stackit/terraform/modules/dns/versions.tf` | AC-004: test_contract.py assertion | n/a | n/a |
| FR-004b | SDD-C-005, SDD-C-011 | — | `DNS_PRIMARY_NAME_SERVER` in module.contract.yaml + dns_primary_name_server() helper + apply.sh state write | `blueprint/modules/dns/module.contract.yaml`, `scripts/lib/infra/dns.sh`, `scripts/bin/infra/dns_apply.sh` | AC-011: test_contract.py assertion | module.contract.yaml | n/a |
| FR-005 | SDD-C-005, SDD-C-010 | — | `dns_smoke.sh` non-empty checks for zone_id, zone_fqdn, primary_name_server + smoke state write includes all four | `scripts/bin/infra/dns_smoke.sh` | AC-005, AC-006, AC-012: test_contract.py assertions | n/a | n/a |
| FR-006 | SDD-C-005, SDD-C-012 | — | `test_pyramid_contract.json` entry | `scripts/lib/quality/test_pyramid_contract.json` | AC-008: pre-commit PASS | n/a | n/a |
| FR-007 | SDD-C-005, SDD-C-012 | — | `test_contract.py` with ≥ 10 assertions | `tests/infra/modules/dns/test_contract.py` | AC-009: pytest PASS | n/a | n/a |
| NFR-SEC-001 | SDD-C-009 | — | zone_id treated as non-sensitive identifier; no secret store interaction | `dns_apply.sh` state write | n/a — no negative requirement | n/a | n/a |
| NFR-OBS-001 | SDD-C-010 | — | zone_id, zone_name, zone_fqdn, primary_name_server in state; smoke validates all four non-empty | `dns_smoke.sh` + `dns_apply.sh` | AC-005, AC-006, AC-012 smoke checks | n/a | n/a |
| NFR-REL-001 | SDD-C-012 | — | NO lifecycle { create_before_destroy } on dns zone | `main.tf` (absence of lifecycle block) | AC-001: structural check confirms absence | ADR D-1 | n/a |
| NFR-OPS-001 | SDD-C-010 | — | zone_id, zone_name, zone_fqdn in runtime state artifact | `dns_apply.sh` | AC-010: state key assertions | n/a | n/a |
| NFR-A11Y-001 | — | — | N/A — no UI changes | — | — | — | — |
| AC-001 | SDD-C-012 | — | main.tf stackit_dns_zone.this with project_id, name, dns_name | test_contract.py | pytest PASS | — | n/a |
| AC-002 | SDD-C-012 | — | variables.tf five variables | test_contract.py | pytest PASS | — | n/a |
| AC-003 | SDD-C-012 | — | outputs.tf zone_id and dns_name | test_contract.py | pytest PASS | — | n/a |
| AC-004 | SDD-C-012 | — | versions.tf stackitcloud/stackit = 0.88.0 | test_contract.py | pytest PASS | — | n/a |
| AC-005 | SDD-C-012 | — | dns_smoke.sh validates zone_id non-empty | test_contract.py | pytest PASS | — | n/a |
| AC-006 | SDD-C-012 | — | dns_smoke.sh validates zone_fqdn non-empty | test_contract.py | pytest PASS | — | n/a |
| AC-007 | SDD-C-012 | — | terraform validate passes from modules/dns/ | infra-validate make target | infra-validate PASS | — | n/a |
| AC-008 | SDD-C-012 | — | test_contract.py in test_pyramid_contract.json unit scope | scripts/lib/quality/test_pyramid_contract.json | pre-commit PASS | — | n/a |
| AC-009 | SDD-C-012 | — | test_contract.py passes with ≥ 10 assertions | test_contract.py | pytest PASS | — | n/a |
| AC-010 | SDD-C-012 | — | runtime state contains zone_id, zone_name, zone_fqdn | dns_apply.sh + mock fixture | test_contract.py assertion | — | n/a |
| AC-011 | SDD-C-012 | — | module.contract.yaml includes DNS_PRIMARY_NAME_SERVER + dns_apply.sh writes primary_name_server | blueprint/modules/dns/module.contract.yaml + dns_apply.sh | test_contract.py assertion | module.contract.yaml | n/a |
| AC-012 | SDD-C-012 | — | dns_smoke.sh validates primary_name_server non-empty + writes to dns_smoke state | dns_smoke.sh | test_contract.py assertion | — | n/a |

## Graph Linkage
- Graph file: `graph.json`
- Every `FR-###`, `NFR-*-###`, and `AC-###` listed in this file MUST have a corresponding node in `graph.json`.
- Node IDs referenced:
  - FR-001, FR-002, FR-003, FR-004, FR-004b, FR-005, FR-006, FR-007
  - NFR-SEC-001, NFR-OBS-001, NFR-REL-001, NFR-OPS-001, NFR-A11Y-001
  - AC-001, AC-002, AC-003, AC-004, AC-005, AC-006, AC-007, AC-008, AC-009, AC-010, AC-011, AC-012

## Validation Summary
- Required bundles executed: pending
- Result summary: pending
- Documentation validation:
  - `make docs-build`: pending
  - `make docs-smoke`: pending

## Evidence Manifest
- Manifest file: `evidence_manifest.json`
- Context export: `context_pack.md`
- PR context export: `pr_context.md`
- Hardening review export: `hardening_review.md`

## Open Risks and Follow-Ups
- Follow-up: Q-1 — if `stackit_dns_zone` exposes nameservers in a future provider version, add `DNS_NAMESERVERS` to `outputs.tf` and `module.contract.yaml`.
- Follow-up: Q-2 — if provider gains a `dnssec_enabled` attribute, add it as a configurable variable.
- Follow-up: DNS record management (`stackit_dns_record_set`) may be required by public-endpoints module; tracked as a separate work item dependency.
