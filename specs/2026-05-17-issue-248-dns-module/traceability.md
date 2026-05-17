# Traceability Matrix

## Requirement-to-Delivery Mapping

| Requirement ID | Control IDs | WCAG SC | Design Element | Implementation Path(s) | Test Evidence | Documentation Evidence | Operational Evidence |
|---|---|---|---|---|---|---|---|
| FR-001 | SDD-C-005, SDD-C-011 | — | `stackit_dns_zone.this` as `for_each` over `dns_zone_fqdns`; name=`{dns_naming_prefix}-dns-{sha1(fqdn)[0:8]}`; dns_name=trimsuffix | `infra/cloud/stackit/terraform/modules/dns/main.tf` | AC-001: test_contract.py assertions (for_each, sha1, trimsuffix, no create_before_destroy) | ADR-issue-248-dns-module.md | n/a |
| FR-002 | SDD-C-005, SDD-C-011 | — | `variables.tf` with five variables: stackit_project_id, stackit_region, dns_zone_fqdns (list), dns_naming_prefix, dns_record_ttl | `infra/cloud/stackit/terraform/modules/dns/variables.tf` | AC-002: test_contract.py assertion | n/a | n/a |
| FR-003 | SDD-C-005, SDD-C-008 | — | `outputs.tf` with zone_ids (map), dns_names (list), primary_name_servers (map) | `infra/cloud/stackit/terraform/modules/dns/outputs.tf` | AC-003: test_contract.py assertions | n/a | n/a |
| FR-004 | SDD-C-005, SDD-C-011 | — | `versions.tf` with stackitcloud/stackit = 0.88.0 | `infra/cloud/stackit/terraform/modules/dns/versions.tf` | AC-004: test_contract.py assertion | n/a | n/a |
| FR-004b | SDD-C-005, SDD-C-011 | — | DNS_ZONE_IDS, DNS_ZONE_COUNT, DNS_PRIMARY_NAME_SERVERS in module.contract.yaml + dns_zone_ids(), dns_zone_count(), dns_primary_name_servers() helpers + apply.sh state write | `blueprint/modules/dns/module.contract.yaml`, `scripts/lib/infra/dns.sh`, `scripts/bin/infra/dns_apply.sh` | AC-011: test_contract.py assertions (3 contract yaml + 3 shell lib + 3 apply state tests) | module.contract.yaml | n/a |
| FR-005 | SDD-C-005, SDD-C-010 | — | `dns_smoke.sh` validates zone_count≥1, zone_ids non-empty, primary_name_servers non-empty; writes zone_ids, zone_fqdns, zone_count, primary_name_servers to smoke state | `scripts/bin/infra/dns_smoke.sh` | AC-005, AC-006, AC-012: test_contract.py assertions | n/a | n/a |
| FR-006 | SDD-C-005, SDD-C-012 | — | `test_pyramid_contract.json` entry | `scripts/lib/quality/test_pyramid_contract.json` | AC-008: pre-commit PASS | n/a | n/a |
| FR-007 | SDD-C-005, SDD-C-012 | — | `test_contract.py` with 26 assertions (≥ 10) | `tests/infra/modules/dns/test_contract.py` | AC-009: pytest 26/26 PASS | n/a | n/a |
| NFR-SEC-001 | SDD-C-009 | — | zone_ids treated as non-sensitive identifiers; no secret store interaction | `dns_apply.sh` state write | n/a — no negative requirement | n/a | n/a |
| NFR-OBS-001 | SDD-C-010 | — | zone_ids, zone_fqdns, zone_count, primary_name_servers in state; smoke validates zone_count≥1 and zone_ids/primary_name_servers non-empty | `dns_smoke.sh` + `dns_apply.sh` | AC-005, AC-006, AC-012 smoke checks | n/a | n/a |
| NFR-REL-001 | SDD-C-012 | — | NO lifecycle { create_before_destroy } on dns zone | `main.tf` (absence of lifecycle block) | AC-001: structural check confirms absence | ADR D-1 | n/a |
| NFR-OPS-001 | SDD-C-010 | — | zone_ids, zone_fqdns, zone_count in runtime state artifact | `dns_apply.sh` | AC-010: state key assertions | n/a | n/a |
| NFR-A11Y-001 | — | — | N/A — no UI changes | — | — | — | — |
| AC-001 | SDD-C-012 | — | main.tf: for_each over dns_zone_fqdns, sha1 naming, trimsuffix, required_version, no create_before_destroy | test_contract.py | pytest PASS (6 assertions) | — | n/a |
| AC-002 | SDD-C-012 | — | variables.tf: dns_zone_fqdns (list), dns_naming_prefix, stackit_project_id, stackit_region, dns_record_ttl | test_contract.py | pytest PASS | — | n/a |
| AC-003 | SDD-C-012 | — | outputs.tf: zone_ids (map), dns_names (list), primary_name_servers (map) | test_contract.py | pytest PASS (3 assertions) | — | n/a |
| AC-004 | SDD-C-012 | — | versions.tf: stackitcloud/stackit = 0.88.0 | test_contract.py | pytest PASS | — | n/a |
| AC-005 | SDD-C-012 | — | dns_smoke.sh validates zone_count is a positive integer | test_contract.py | pytest PASS | — | n/a |
| AC-006 | SDD-C-012 | — | dns_smoke.sh validates zone_ids is non-empty | test_contract.py | pytest PASS | — | n/a |
| AC-007 | SDD-C-012 | — | terraform validate passes from modules/dns/ | infra-validate make target | infra-validate PASS | — | n/a |
| AC-008 | SDD-C-012 | — | test_contract.py in test_pyramid_contract.json unit scope | scripts/lib/quality/test_pyramid_contract.json | pre-commit PASS | — | n/a |
| AC-009 | SDD-C-012 | — | test_contract.py passes with ≥ 10 assertions — 26 assertions total | test_contract.py | pytest 26/26 PASS | — | n/a |
| AC-010 | SDD-C-012 | — | runtime state contains zone_ids, zone_fqdns, zone_count, primary_name_servers | dns_apply.sh + mock fixture | test_contract.py assertion (4 keys) | — | n/a |
| AC-011 | SDD-C-012 | — | module.contract.yaml: DNS_ZONE_IDS, DNS_ZONE_COUNT, DNS_PRIMARY_NAME_SERVERS; dns.sh: dns_zone_ids(), dns_zone_count(), dns_primary_name_servers(); dns_apply.sh: zone_ids, zone_count, primary_name_servers in state | blueprint/modules/dns/module.contract.yaml + dns.sh + dns_apply.sh | test_contract.py assertions (9 assertions across 3 classes) | module.contract.yaml | n/a |
| AC-012 | SDD-C-012 | — | dns_smoke.sh validates primary_name_servers non-empty + writes zone_ids, zone_fqdns, zone_count, primary_name_servers to dns_smoke state | dns_smoke.sh | test_contract.py assertion | — | n/a |

## Graph Linkage
- Graph file: `graph.json`
- Every `FR-###`, `NFR-*-###`, and `AC-###` listed in this file MUST have a corresponding node in `graph.json`.
- Node IDs referenced:
  - FR-001, FR-002, FR-003, FR-004, FR-004b, FR-005, FR-006, FR-007
  - NFR-SEC-001, NFR-OBS-001, NFR-REL-001, NFR-OPS-001, NFR-A11Y-001
  - AC-001, AC-002, AC-003, AC-004, AC-005, AC-006, AC-007, AC-008, AC-009, AC-010, AC-011, AC-012

## Validation Summary
- Required bundles executed: 2026-05-17 (post multi-zone refactor)
- Result summary:
  - `PYTHONPATH="$(pwd)" uv run pytest tests/infra/modules/dns/test_contract.py -v` — 26/26 PASSED
  - `make infra-validate` — PASS
  - `make quality-docs-check-changed` — PASS (contract_metadata + module README regenerated)
  - `make quality-sdd-check-all` — PASS
  - `tests/infra/test_optional_modules.py::OptionalModulesTests::test_dns_module_flow` — PASS (two-zone fixture: marketplace-web-dev + marketplace-auth-dev)
  - Graph linkage: 25 nodes, 20 edges, 0 orphans
- Documentation validation:
  - `make docs-build`: deferred to step-06 document-sync
  - `make docs-smoke`: deferred to step-06 document-sync

## Evidence Manifest
- Manifest file: `evidence_manifest.json`
- Context export: `context_pack.md`
- PR context export: `pr_context.md`
- Hardening review export: `hardening_review.md`

## Open Risks and Follow-Ups
- Follow-up: Q-2 — if provider gains a `dnssec_enabled` attribute, add it as a configurable variable.
- Follow-up: external-DNS module — dynamic DNS record management via K8s controller (parked proposal in AGENTS.backlog.md, scope `infra`).
- Follow-up: domain contract JSON pattern — cross-cutting refactor of all optional modules to use a single SSOT JSON file per environment (parked proposal in AGENTS.backlog.md, scope `blueprint`).
- Follow-up: DNS naming uses `runs.onstackit.local.` suffix in local test fixtures; real consumer FQDNs follow `{prefix}-{env}.runs.onstackit.cloud.` pattern as observed in sbonoc/agentic-graphrag.
