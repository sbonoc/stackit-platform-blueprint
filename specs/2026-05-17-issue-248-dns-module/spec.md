# Specification

## Spec Readiness Gate (Blocking)
<!-- SPEC_PRODUCT_READY=true: intake gate — Product sign-off only; unlocks agent ADR drafting.
     SPEC_READY=true: implementation gate — all sign-offs required; unlocks coding. -->
- SPEC_READY: true
- SPEC_PRODUCT_READY: true
- Open questions count: 0
- Unresolved alternatives count: 0
- Unresolved TODO markers count: 0
- Pending assumptions count: 0
- Open clarification markers count: 0
- Product sign-off: approved
- Architecture sign-off: approved
- Security sign-off: approved
- Operations sign-off: approved
- Missing input blocker token: none
- ADR path: docs/blueprint/architecture/decisions/ADR-issue-248-dns-module.md
- ADR status: approved
- SPEC_READY_EXCEPTION: none
- authorized-by: sbonoc

## Applicable Guardrail Controls (Normative)
- Applicable control IDs: SDD-C-001, SDD-C-002, SDD-C-003, SDD-C-004, SDD-C-005, SDD-C-006, SDD-C-007, SDD-C-008, SDD-C-009, SDD-C-010, SDD-C-011, SDD-C-012, SDD-C-013, SDD-C-014, SDD-C-015, SDD-C-016, SDD-C-017, SDD-C-018, SDD-C-019, SDD-C-020, SDD-C-021
- Control exception rationale: none

## Implementation Stack Profile (Normative)
- Backend stack profile: n/a — tooling/infrastructure-only change
- Frontend stack profile: n/a — tooling/infrastructure-only change
- Test automation profile: pytest
- Agent execution model: specialized-subagents-isolated-worktrees
- Managed service preference: stackit-managed-first
- Managed service exception rationale: none
- Runtime profile: local-first-docker-desktop-kubernetes
- Local Kubernetes context policy: docker-desktop-preferred
- Local provisioning stack: crossplane-plus-helm
- Runtime identity baseline: eso-plus-argocd-plus-keycloak
- Local-first exception rationale: STACKIT DNS has no local-lane equivalent; the local driver is `noop` by design, consistent with all other STACKIT-only optional modules. Local DNS is handled by `/etc/hosts` + port-forward.

## Objective
- Business outcome: Blueprint consumers can provision one or more STACKIT-managed DNS zones via a single optional-module invocation and obtain a canonical zone contract (`DNS_ZONE_IDS`, `DNS_ZONE_COUNT`, `DNS_ZONE_FQDNS`, `DNS_PRIMARY_NAME_SERVERS`) through the standard optional-module flow, eliminating manual STACKIT console steps and enabling downstream modules (public-endpoints, ingress TLS, Keycloak) to reference zones by FQDN.
- Success metric: `make infra-dns-apply` succeeds on the STACKIT lane, writes all required state keys, and `make infra-dns-smoke` exits 0 with zone_count ≥ 1, zone_ids, and primary_name_servers all validated non-empty. `test_contract.py` passes with ≥ 10 assertions.

## Normative Requirements

### Functional Requirements (Normative)

- FR-001 MUST implement `infra/cloud/stackit/terraform/modules/dns/main.tf` declaring `stackit_dns_zone.this` as a `for_each` resource iterating over `toset(var.dns_zone_fqdns)`. Each zone MUST use `name = substr("${var.dns_naming_prefix}-dns-${substr(sha1(each.value), 0, 8)}", 0, 63)` for a human-readable, collision-resistant display name, and `dns_name = trimsuffix(each.value, ".")` to strip the trailing dot. The file MUST include a `terraform` block with `required_version = ">= 1.13.0"` and a `locals { contract = "blueprint" }` block, consistent with all other standalone modules (kms, secrets-manager). NFR-REL-001 applies: no `lifecycle { create_before_destroy }`.
- FR-002 MUST implement `infra/cloud/stackit/terraform/modules/dns/variables.tf` declaring: `stackit_project_id` (required string), `stackit_region` (string, default `"eu01"`, declared for API consistency — not forwarded to the resource as `stackit_dns_zone` does not accept a region attribute), `dns_zone_fqdns` (required `list(string)`, FQDNs with trailing dot, replaces the former single `dns_zone_fqdn`), `dns_naming_prefix` (required string, used as the zone display name prefix combined with the active stack by the shell layer before being passed to TF, replaces the former `dns_zone_name`), `dns_record_ttl` (number, default `300`).
- FR-003 MUST implement `infra/cloud/stackit/terraform/modules/dns/outputs.tf` declaring: `zone_ids` (map of string: FQDN → zone_id, from `stackit_dns_zone.this[*].zone_id`), `dns_names` (list of string: dns_name per zone, without trailing dot), and `primary_name_servers` (map of string: FQDN → primary_name_server FQDN, from `stackit_dns_zone.this[*].primary_name_server`). Each provider zone exposes exactly one `primary_name_server` (String, FQDN); no plural nameservers attribute exists in v0.88.0.
- FR-004 MUST implement `infra/cloud/stackit/terraform/modules/dns/versions.tf` declaring the `stackitcloud/stackit` required provider with the pinned version constraint `= 0.88.0`, matching all other modules.
- FR-004b MUST update `blueprint/modules/dns/module.contract.yaml` outputs.produced to include `DNS_ZONE_IDS`, `DNS_ZONE_COUNT`, and `DNS_PRIMARY_NAME_SERVERS` (replacing the former singular outputs). The `dns_apply.sh` MUST write `zone_ids=$(dns_zone_ids)`, `zone_count=$(dns_zone_count)`, and `primary_name_servers=$(dns_primary_name_servers)` to the runtime state file. `dns.sh` MUST expose `dns_zone_ids()`, `dns_zone_count()`, and `dns_primary_name_servers()` helpers (all plural). The shell layer constructs the full TF naming prefix as `${DNS_NAMING_PREFIX}-${active_stack}` before invoking TF, so `dns_naming_prefix` TF variable receives e.g. `myapp-dev` when `DNS_NAMING_PREFIX=myapp` and the active stack is `dev`.
- FR-005 MUST update `scripts/bin/infra/dns_smoke.sh` to validate: `zone_count` is a positive integer (≥ 1), `zone_ids` is non-empty, and `primary_name_servers` is non-empty in the runtime state file. The smoke script MUST write `zone_ids`, `zone_fqdns`, `zone_count`, and `primary_name_servers` to the `dns_smoke` state artifact, consistent with the KMS pattern where smoke writes all validated keys.
- FR-006 MUST add `tests/infra/modules/dns/test_contract.py` to `scripts/lib/quality/test_pyramid_contract.json` under the `unit` scope before creating the test file, so the pre-commit pyramid gate does not block the commit.
- FR-007 MUST implement `tests/infra/modules/dns/test_contract.py` with ≥ 10 assertions covering: (a) TF module structure (`main.tf` `for_each` + `sha1` naming + `trimsuffix`, `variables.tf` variables including `dns_zone_fqdns` and `dns_naming_prefix`, `outputs.tf` outputs `zone_ids`/`dns_names`/`primary_name_servers`, `versions.tf` provider pin); (b) shell library function presence — `dns_primary_name_servers()` (plural) MUST be explicitly asserted to exist in `dns.sh`; (c) state contract keys in `dns_apply.sh` write (`zone_ids`, `zone_count`, `primary_name_servers`); (d) smoke validation logic (`zone_count`, `zone_ids`, `primary_name_servers` non-empty checks); and (e) quality gate registration in `test_pyramid_contract.json`.

### Non-Functional Requirements (Normative)

- NFR-SEC-001 DNS zones carry no credentials. No secret handling is required. The `zone_id` output MUST be treated as a non-sensitive identifier and MUST NOT be written to any secret store.
- NFR-OBS-001 MUST ensure `zone_ids`, `zone_fqdns`, `zone_count`, and `primary_name_servers` are present in the runtime state artifact and that `dns_smoke.sh` validates zone_count ≥ 1 and zone_ids/primary_name_servers are non-empty. All script output MUST be prefixed with `[dns]`.
- NFR-REL-001 MUST NOT declare `lifecycle { create_before_destroy = true }` on `stackit_dns_zone.this`. DNS zone recreation requires coordinated record migration; silent create-before-destroy would orphan existing DNS records and break downstream consumers.
- NFR-OPS-001 MUST write `zone_ids`, `zone_fqdns`, and `zone_count` to the runtime state file so operators and downstream modules (`public-endpoints`) can reference zones without manual console access.
- NFR-A11Y-001 N/A — no UI or frontend changes in this work item.

### Open Questions — Resolved

**Q-1 — Nameservers (RESOLVED):** Provider v0.88.0 schema confirmed via stackitcloud/terraform-provider-stackit source. `stackit_dns_zone` exposes exactly one computed attribute: `primary_name_server` (String, FQDN). No plural `nameservers` list exists. Decision: add `primary_name_server` to `outputs.tf` and add `DNS_PRIMARY_NAME_SERVER` to `module.contract.yaml` outputs.produced. Issue #248's `DNS_NAMESERVERS` (plural) is satisfied by the single `primary_name_server` output — this is the only nameserver the STACKIT provider exposes.

**Q-2 — DNSSEC (RESOLVED):** Provider v0.88.0 schema confirmed. No DNSSEC-related attribute (`dnssec`, `dnssec_enabled`, `dnssec_config`, or similar) exists on `stackit_dns_zone`. DNSSEC is not configurable via Terraform in v0.88.0. Decision: document in module README that DNSSEC is managed at the STACKIT platform level and is not a Terraform-configurable attribute. No implementation change required.

## Normative Option Decision

### Option Decision 1: `dns_name` attribute value in `main.tf`

- Option A: Use `dns_name = trimsuffix(var.dns_zone_fqdn, ".")` — strip trailing dot before passing to provider, consistent with foundation `local.dns_zone_dns_names`.
- Option B: Pass `var.dns_zone_fqdn` directly and rely on provider normalisation.
- Selected option: OPTION_A
- Rationale: Foundation strips the trailing dot explicitly via `trimsuffix` in locals. Keeping the standalone module consistent prevents provider validation errors and divergence from the tested pattern.

### Option Decision 2: zone display name strategy

- Option A: Consumer supplies `dns_zone_name` directly as the display name (one per zone required for multi-zone).
- Option B: Compute from a consumer prefix + FQDN hash: `substr("{dns_naming_prefix}-dns-{substr(sha1(fqdn), 0, 8)}", 0, 63)`.
- Option C (selected): Shell layer constructs the full prefix as `{DNS_NAMING_PREFIX}-{active_stack}`, passes it to TF as `dns_naming_prefix`. TF derives the zone display name as `substr("{dns_naming_prefix}-dns-{substr(sha1(each.value), 0, 8)}", 0, 63)`.
- Selected option: OPTION_C
- Rationale: Multi-zone `for_each` requires a deterministic per-zone name without consumer-supplied lists. The naming prefix is DRY — the consumer sets only `DNS_NAMING_PREFIX` (e.g., `dhe-marketplace-web`), the blueprint shell appends the active stack (`dev`/`stage`/`prod`), and TF appends the FQDN hash for uniqueness. Result: `dhe-marketplace-web-dev-dns-a3b4c5d6` — human-readable and collision-resistant. Mirrors the pattern used in `sbonoc/agentic-graphrag` foundation module.

## Contract Changes (Normative)
- Config/Env contract inputs: `blueprint/modules/dns/module.contract.yaml` — replace `DNS_ZONE_NAME` + `DNS_ZONE_FQDN` (single zone) with `DNS_ZONE_FQDNS` (space-separated list of FQDNs with trailing dot) and `DNS_NAMING_PREFIX` (consumer+app slug, e.g. `dhe-marketplace-web`; shell appends active stack before passing to TF).
- Config/Env contract outputs: replace `DNS_ZONE_ID`, `DNS_ZONE_NAME`, `DNS_ZONE_FQDN`, `DNS_PRIMARY_NAME_SERVER` with `DNS_ZONE_IDS` (space-separated zone IDs), `DNS_ZONE_COUNT` (integer), `DNS_ZONE_FQDNS` (echo of input), `DNS_PRIMARY_NAME_SERVERS` (space-separated primary NS FQDNs).
- API contract: none
- OpenAPI / Pact contract path: none
- Event contract: none
- Make/CLI contract: none — `infra-dns-{plan,apply,smoke,destroy}` targets already exist
- Docs contract: `docs/platform/modules/dns/README.md` to be expanded with a standalone TF module section, multi-zone runtime state contract table, naming pattern documentation, and smoke check documentation.

## Blueprint Upstream Defect Escalation (Normative)
- Upstream issue URL: none
- Temporary workaround path: none
- Replacement trigger: none
- Workaround review date: none

## Normative Acceptance Criteria

- AC-001 `infra/cloud/stackit/terraform/modules/dns/main.tf` declares `stackit_dns_zone.this` as a `for_each` resource over `toset(var.dns_zone_fqdns)`. Each zone uses `name = substr("${var.dns_naming_prefix}-dns-${substr(sha1(each.value), 0, 8)}", 0, 63)` and `dns_name = trimsuffix(each.value, ".")`. The file includes `required_version = ">= 1.13.0"` and does NOT include `lifecycle { create_before_destroy }` (NFR-REL-001).
- AC-002 `infra/cloud/stackit/terraform/modules/dns/variables.tf` declares all five variables: `stackit_project_id`, `stackit_region`, `dns_zone_fqdns` (list of string), `dns_naming_prefix` (string), `dns_record_ttl`.
- AC-003 `infra/cloud/stackit/terraform/modules/dns/outputs.tf` declares `zone_ids` (map FQDN→zone_id), `dns_names` (list of dns_name strings), and `primary_name_servers` (map FQDN→primary_name_server).
- AC-004 `infra/cloud/stackit/terraform/modules/dns/versions.tf` declares the `stackitcloud/stackit` required provider at version `= 0.88.0`.
- AC-005 `scripts/bin/infra/dns_smoke.sh` validates `zone_count` is a positive integer (≥ 1) in the runtime state file.
- AC-006 `scripts/bin/infra/dns_smoke.sh` validates `zone_ids` is non-empty in the runtime state file.
- AC-007 `terraform validate` passes from `infra/cloud/stackit/terraform/modules/dns/`.
- AC-008 `tests/infra/modules/dns/test_contract.py` has an entry in `scripts/lib/quality/test_pyramid_contract.json` under the `unit` scope, added before the test file is created.
- AC-009 `tests/infra/modules/dns/test_contract.py` passes with ≥ 10 assertions, all green.
- AC-010 The runtime state file (`artifacts/infra/dns_runtime.env`) contains `zone_ids`, `zone_fqdns`, `zone_count`, and `primary_name_servers` keys after a STACKIT-lane apply (validated by AC-005 + AC-006 + AC-012 smoke checks).
- AC-011 `blueprint/modules/dns/module.contract.yaml` includes `DNS_ZONE_IDS`, `DNS_ZONE_COUNT`, and `DNS_PRIMARY_NAME_SERVERS` under `outputs.produced`. `dns_apply.sh` writes `zone_ids`, `zone_count`, and `primary_name_servers` to the runtime state file. `dns.sh` declares `dns_zone_ids()`, `dns_zone_count()`, and `dns_primary_name_servers()` helper functions.
- AC-012 `scripts/bin/infra/dns_smoke.sh` validates `primary_name_servers` is non-empty in the runtime state file, and writes `zone_ids`, `zone_fqdns`, `zone_count`, and `primary_name_servers` to the `dns_smoke` state artifact.

## Informative Notes (Non-Normative)
- Context: This is one of 5 remaining stub modules under issue #248. The other 4 (public-endpoints, observability, workflows, identity-aware-proxy) will be implemented in separate work items after this one.
- Shell layer completeness: All four DNS scripts and `dns.sh` already exist and are partially complete. Implementation updates the TF module (four `.tf` files), the shell helpers (multi-zone functions), smoke checks, and the test contract file.
- Foundation alignment: The foundation `main.tf` uses `for_each` across multiple zones via a list input — the standalone module now follows the same pattern. Zone naming (`{prefix}-dns-{hash}`) mirrors the foundation naming strategy from `sbonoc/agentic-graphrag`.
- DNS_NAMING_PREFIX shell convention: The shell layer constructs the full TF naming prefix as `${DNS_NAMING_PREFIX}-${active_stack}` and passes it to TF as `dns_naming_prefix`. The TF variable receives e.g. `dhe-marketplace-web-dev` when `DNS_NAMING_PREFIX=dhe-marketplace-web` and the active stack is `dev`. Zone display name in STACKIT: `dhe-marketplace-web-dev-dns-a3b4c5d6`.
- DNS record management: External-DNS (K8s operator, analogous to ESO) is the recommended approach for managing DNS records dynamically. The blueprint module manages zones only; record creation via external-DNS annotations on Gateway/Ingress resources is documented as a follow-up module scope. `stackit_dns_record_set` (TF records) is appropriate only for static records (MX, SPF).
- DNSSEC: STACKIT manages DNSSEC at the platform level per Q-2 resolution (Option A). No TF attribute controls it in v0.88.0.

## Explicit Exclusions
- DNS record management (`stackit_dns_record_set`) — zone provisioning only; dynamic record management via external-DNS is the recommended pattern and is a separate module scope.
- External-DNS module — cluster-level controller for dynamic record management; separate work item (analogous to ESO module).
- Domain contract JSON pattern — cross-cutting refactor of all optional modules; deferred to a separate spec (backlog, scope `blueprint`).
- `public-endpoints`, `observability`, `workflows`, `identity-aware-proxy` modules — separate work items.
- Local-lane equivalent — STACKIT-only module; local lane remains `noop`.
- `DNS_NAMESERVERS` output (original issue #248 plural) — satisfied by `DNS_PRIMARY_NAME_SERVERS` (one per zone from provider `primary_name_server` attribute).
