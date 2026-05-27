# PR Context

## Summary

Implements the STACKIT DNS optional module as a production-capable, multi-zone standalone Terraform module (FR-001 through FR-007). Scope was expanded mid-work from single-zone to multi-zone `for_each` after reviewing an existing consumer reference implementation that provisions multiple DNS zones per environment (e.g., `marketplace-web-dev.runs.onstackit.cloud.` and `marketplace-auth-dev.runs.onstackit.cloud.`). The main deliverables are: (1) `stackit_dns_zone.this` using `for_each = toset(var.dns_zone_fqdns)` with SHA1 collision-resistant display names; (2) multi-zone shell contract layer (`dns_zone_ids()`, `dns_zone_count()`, `dns_primary_name_servers()`); (3) runtime state and smoke validation for all four contract keys; (4) 26-assertion test contract; and (5) full module documentation. External DNS record management (K8s-native dynamic record lifecycle) and domain contract JSON pattern are explicitly out of scope and parked in AGENTS.backlog.md. Part of #248 — umbrella issue stays open until all remaining stub modules ship.

## Requirement Coverage

| Requirement ID | Implementation File(s) | Test Evidence |
|---|---|---|
| FR-001 | `infra/cloud/stackit/terraform/modules/dns/main.tf` | `test_ac001_*` (6 assertions) |
| FR-002 | `infra/cloud/stackit/terraform/modules/dns/variables.tf` | `test_ac002_variables_tf_declares_all_five_variables` |
| FR-003 | `infra/cloud/stackit/terraform/modules/dns/outputs.tf` | `test_ac003_*` (3 assertions) |
| FR-004 | `infra/cloud/stackit/terraform/modules/dns/versions.tf` | `test_ac004_*` (2 assertions) |
| FR-004b | `blueprint/modules/dns/module.contract.yaml`, `scripts/lib/infra/dns.sh`, `scripts/bin/infra/dns_apply.sh` | `test_ac011_*` (9 assertions across 3 test classes) |
| FR-005 | `scripts/bin/infra/dns_smoke.sh` | `test_ac005_*`, `test_ac006_*`, `test_ac012_*` (3 assertions) |
| FR-006 | `scripts/lib/quality/test_pyramid_contract.json` | `test_ac008_test_contract_in_pyramid_contract_json` |
| FR-007 | `tests/infra/modules/dns/test_contract.py` | `test_ac009_*` (26 total — ≥ 10 required) |
| NFR-SEC-001 | `scripts/bin/infra/dns_apply.sh` (zone_ids written as non-sensitive state key) | Structural: no Vault/ESO write |
| NFR-OBS-001 | `scripts/bin/infra/dns_apply.sh` + `scripts/bin/infra/dns_smoke.sh` | `test_ac005_*`, `test_ac006_*`, `test_ac012_*` |
| NFR-REL-001 | `infra/cloud/stackit/terraform/modules/dns/main.tf` (absence of lifecycle block) | `test_ac001_main_tf_no_create_before_destroy` |
| NFR-OPS-001 | `scripts/bin/infra/dns_apply.sh` (zone_ids, zone_fqdns, zone_count, primary_name_servers in state) | `test_ac010_runtime_state_fixture_has_all_contract_keys` |
| NFR-A11Y-001 | N/A — no UI changes | N/A |

- **Contract surfaces changed:**
  - `blueprint/modules/dns/module.contract.yaml` — required env: `DNS_ZONE_FQDNS`, `DNS_NAMING_PREFIX` (replaces `DNS_ZONE_NAME`, `DNS_ZONE_FQDN`); outputs: `DNS_ZONE_IDS`, `DNS_ZONE_COUNT`, `DNS_PRIMARY_NAME_SERVERS` (replaces `DNS_ZONE_ID`)
  - `scripts/lib/infra/stackit_layers.sh` — foundation `require_env_vars` and emit call updated to new vars
  - `scripts/lib/blueprint/init_repo_env.py` — `MODULE_REQUIRED_ENV_DEFAULTS` updated to `DNS_NAMING_PREFIX` / `DNS_ZONE_FQDNS`
  - `docs/platform/modules/dns/README.md` — fully rewritten for multi-zone API
  - `docs/blueprint/architecture/decisions/ADR-issue-248-dns-module.md` — rewritten for multi-zone design (D-1, D-3, D-5 updated)
  - `blueprint/contract.yaml` — not changed (DNS_ENABLED flag pre-existed)
  - Generated consumer behavior: consumers that had `DNS_ENABLED=true` with the old `DNS_ZONE_NAME` / `DNS_ZONE_FQDN` vars would need to migrate to `DNS_NAMING_PREFIX` / `DNS_ZONE_FQDNS`. No generated consumer currently has DNS enabled (module was a provisioning stub before this PR).

## Key Reviewer Files

- Primary files to review first:
  - `infra/cloud/stackit/terraform/modules/dns/main.tf` — core TF resource: `for_each`, SHA1 naming pattern, NFR-REL-001 enforcement (no `create_before_destroy`), `trimsuffix` for provider compatibility
  - `scripts/lib/infra/dns.sh` — shell contract layer: `dns_zone_ids()`, `dns_zone_count()`, `dns_primary_name_servers()`, `dns_naming_prefix_with_stack()` — primary shell interface for DNS consumers
  - `blueprint/modules/dns/module.contract.yaml` — required env (`DNS_ZONE_FQDNS`, `DNS_NAMING_PREFIX`) and outputs (`DNS_ZONE_IDS`, `DNS_ZONE_COUNT`, `DNS_PRIMARY_NAME_SERVERS`) — API surface blueprint renders into consumer `.envrc` and Makefile targets
  - `tests/infra/modules/dns/test_contract.py` — 26 assertions across 7 test classes covering all ACs
- High-risk files:
  - `scripts/lib/infra/stackit_layers.sh` (lines 224–228) — foundation layer: `${DNS_ZONE_FQDNS// /,}` space-to-comma conversion for TF `-var=dns_zone_fqdns=[...]` list — subtle but load-bearing for foundation apply
  - `infra/cloud/stackit/terraform/modules/dns/outputs.tf` — multi-zone output types: `zone_ids` map(string), `dns_names` list(string), `primary_name_servers` map(string) — consumer contract shapes
  - `scripts/bin/infra/dns_apply.sh` — multi-zone state write: all four contract keys (`zone_ids`, `zone_fqdns`, `zone_count`, `primary_name_servers`) — downstream modules read these
  - `scripts/bin/infra/dns_smoke.sh` — smoke validations: `zone_count ≥ 1`, `zone_ids` non-empty, `primary_name_servers` non-empty — apply correctness gate

## Validation Evidence

| Command | Result |
|---|---|
| `PYTHONPATH="$(pwd)" uv run pytest tests/infra/modules/dns/test_contract.py -v` | **26/26 PASSED** |
| `make infra-validate` | **PASS** |
| `make quality-docs-check-changed` | **PASS** |
| `make quality-sdd-check-all` | **PASS** |
| `PYTHONPATH="$(pwd)" uv run pytest tests/infra/test_optional_modules.py::OptionalModulesTests::test_dns_module_flow -v` | **PASS** (two-zone fixture: `marketplace-web-dev.runs.onstackit.local.` + `marketplace-auth-dev.runs.onstackit.local.`; `zone_count=2` verified) |
| `make docs-build` | **PASS** |
| `make docs-smoke` | **PASS** |
| `PYTHONPATH="$(pwd)" uv run pytest tests/blueprint/test_optional_module_required_env_contract.py tests/blueprint/test_tooling_contracts.py::ToolingContractsTests::test_stackit_provider_backed_helpers_prefer_foundation_outputs tests/blueprint/contract_refactor_runtime_identity_cases.py -v` | **PASS** (3 previously failing tests fixed by multi-zone API propagation commit `cf5a8bb`) |

- **Traceability:** 25 nodes, 20 edges, 0 orphans — graph integrity verified.
- **Spec artifacts:** `evidence_manifest.json` SHA256s current for all 7 tracked files.

## Risk and Rollback

- **Main risks:**
  - DNS zone destruction (`make infra-dns-destroy`) is irreversible — all records deleted, zone IDs invalidated, registrar re-delegation required (propagation up to 48 hours). Documented in module README with destroy warning.
  - API rename (`DNS_ZONE_NAME`/`DNS_ZONE_FQDN` → `DNS_NAMING_PREFIX`/`DNS_ZONE_FQDNS`): any consumer with DNS enabled must update their env. No generated consumer currently has `DNS_ENABLED=true` — blast radius is zero for existing consumers.
  - `stackit_layers.sh` space-to-comma conversion (`${DNS_ZONE_FQDNS// /,}`) is a new pattern; if an FQDN contained an embedded space (impossible in a valid FQDN) it would break silently. FQDNs cannot contain spaces by DNS specification — no practical risk.

- **Rollback strategy:**
  - Revert TF module files (`main.tf`, `variables.tf`, `outputs.tf`, `versions.tf`) — they are entirely new; no deployed resources to destroy.
  - Revert `scripts/lib/infra/dns.sh`, `scripts/bin/infra/dns_apply.sh`, `scripts/bin/infra/dns_smoke.sh`, `scripts/bin/infra/dns_plan.sh` to pre-PR state.
  - Revert `blueprint/modules/dns/module.contract.yaml`, `scripts/lib/infra/stackit_layers.sh`, `scripts/lib/blueprint/init_repo_env.py`.
  - No state file migration needed — no consumer has applied DNS zones with the old API.
  - Feature flag: `DNS_ENABLED` defaults to `false`. Rolling back does not affect any running system.

## Deferred Proposals (Not Implemented)

1. **DNSSEC `dnssec_enabled` variable** — STACKIT provider v0.88.0 exposes no `dnssec_enabled` attribute on `stackit_dns_zone`. DNSSEC is STACKIT platform-managed.
   Parked — trigger: `on-scope: infra` — surfaces when STACKIT Terraform provider is next upgraded and the attribute becomes available.

2. **External-DNS K8s controller module** — K8s-native dynamic DNS record management via external-dns controller; analogous to ESO for secrets. Zone-only TF module is the correct separation; dynamic record lifecycle belongs in the cluster operator layer.
   Parked — trigger: `on-scope: infra` — backlog entry: `proposal(issue-248-dns-module): external-DNS module`.

3. **Domain contract JSON pattern** — per-environment SSOT JSON driving TF tfvars + ArgoCD Helm values via a renderer with `--check` mode. Cross-cutting refactor of all optional modules; requires blueprint multi-module configuration surface to be in scope.
   Parked — trigger: `on-scope: blueprint` — backlog entry: `proposal(issue-248-dns-module): domain contract JSON pattern`.

## Follow-Up

- Issue #248 umbrella remains open — remaining optional module candidates: `public-endpoints`, `observability`, `workflows`, `identity-aware-proxy`.
- All three deferred proposals have trigger-based backlog entries in `AGENTS.backlog.md`.
