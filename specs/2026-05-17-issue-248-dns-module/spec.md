# Specification

## Spec Readiness Gate (Blocking)
<!-- SPEC_PRODUCT_READY=true: intake gate — Product sign-off only; unlocks agent ADR drafting.
     SPEC_READY=true: implementation gate — all sign-offs required; unlocks coding. -->
- SPEC_READY: false
- SPEC_PRODUCT_READY: false
- Open questions count: 0
- Unresolved alternatives count: 0
- Unresolved TODO markers count: 0
- Pending assumptions count: 0
- Open clarification markers count: 0
- Product sign-off: pending
- Architecture sign-off: pending
- Security sign-off: pending
- Operations sign-off: pending
- Missing input blocker token: none
- ADR path: docs/blueprint/architecture/decisions/ADR-issue-248-dns-module.md
- ADR status: proposed
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
- Business outcome: Blueprint consumers can provision a STACKIT-managed DNS zone and obtain a canonical zone contract (`DNS_ZONE_ID`, `DNS_ZONE_NAME`, `DNS_ZONE_FQDN`) through the standard optional-module flow, eliminating manual STACKIT console steps and enabling downstream modules (public-endpoints, ingress TLS) to reference the zone.
- Success metric: `make infra-dns-apply` succeeds on the STACKIT lane, writes all required state keys, and `make infra-dns-smoke` exits 0 with zone_id, zone_name, and zone_fqdn all validated non-empty. `test_contract.py` passes with ≥ 10 assertions.

## Normative Requirements

### Functional Requirements (Normative)

- FR-001 MUST implement `infra/cloud/stackit/terraform/modules/dns/main.tf` declaring one resource: `stackit_dns_zone.this` with attributes `project_id`, `name`, and `dns_name = trimsuffix(var.dns_zone_fqdn, ".")`, following the structure used in `infra/cloud/stackit/terraform/foundation/main.tf`.
- FR-002 MUST implement `infra/cloud/stackit/terraform/modules/dns/variables.tf` declaring the following variables: `stackit_project_id` (required string), `stackit_region` (string, default `"eu01"`, declared for API consistency — not forwarded to the resource as `stackit_dns_zone` does not accept a region attribute), `dns_zone_name` (required string, display name), `dns_zone_fqdn` (required string, FQDN with trailing dot), `dns_record_ttl` (number, default `300`).
- FR-003 MUST implement `infra/cloud/stackit/terraform/modules/dns/outputs.tf` declaring `zone_id` (from `stackit_dns_zone.this.zone_id`), `dns_name` (from `stackit_dns_zone.this.dns_name`), and `primary_name_server` (from `stackit_dns_zone.this.primary_name_server`, computed). The provider exposes exactly one nameserver via `primary_name_server` (String, FQDN); no plural nameservers attribute exists in v0.88.0.
- FR-004 MUST implement `infra/cloud/stackit/terraform/modules/dns/versions.tf` declaring the `stackitcloud/stackit` required provider with the pinned version constraint `= 0.88.0`, matching all other modules.
- FR-004b MUST add `DNS_PRIMARY_NAME_SERVER` to `blueprint/modules/dns/module.contract.yaml` under `outputs.produced`. The `dns_apply.sh` MUST write `primary_name_server=$(dns_primary_name_server)` to the runtime state file, and `dns.sh` MUST expose a `dns_primary_name_server()` helper that reads from the foundation output or falls back to a local placeholder.
- FR-005 MUST update `scripts/bin/infra/dns_smoke.sh` to add non-empty existence checks for `zone_id` and `zone_fqdn` keys in the runtime state file (the existing check covers `zone_name` only).
- FR-006 MUST add `tests/infra/modules/dns/test_contract.py` to `scripts/lib/quality/test_pyramid_contract.json` under the `unit` scope before creating the test file, so the pre-commit pyramid gate does not block the commit.
- FR-007 MUST implement `tests/infra/modules/dns/test_contract.py` with ≥ 10 assertions covering TF module structure, state contract keys, smoke validation logic, and quality gate registration.

### Non-Functional Requirements (Normative)

- NFR-SEC-001 DNS zones carry no credentials. No secret handling is required. The `zone_id` output MUST be treated as a non-sensitive identifier and MUST NOT be written to any secret store.
- NFR-OBS-001 MUST ensure `zone_id`, `zone_name`, and `zone_fqdn` are present in the runtime state artifact and that `dns_smoke.sh` validates all three keys are non-empty. All script output MUST be prefixed with `[dns]`.
- NFR-REL-001 MUST NOT declare `lifecycle { create_before_destroy = true }` on `stackit_dns_zone.this`. DNS zone recreation requires coordinated record migration; silent create-before-destroy would orphan existing DNS records and break downstream consumers.
- NFR-OPS-001 MUST write `zone_id`, `zone_name`, and `zone_fqdn` to the runtime state file so operators and downstream modules (`public-endpoints`) can reference the zone without manual console access.
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

### Option Decision 2: `name` attribute value strategy

- Option A: Use `var.dns_zone_name` directly as the zone display name.
- Option B: Compute a name with a hash suffix like the foundation (e.g., `"${var.dns_zone_name}-dns-${substr(sha1(var.dns_zone_fqdn), 0, 8)}"`).
- Selected option: OPTION_A
- Rationale: The standalone module provisions exactly one zone per invocation. The foundation uses a hash suffix for uniqueness when managing multiple zones in a single `for_each`. For a single-zone standalone module, passing `dns_zone_name` directly is simpler and gives consumers explicit control over the display name.

## Contract Changes (Normative)
- Config/Env contract: `blueprint/modules/dns/module.contract.yaml` — add `DNS_PRIMARY_NAME_SERVER` to `outputs.produced` (provider exposes `primary_name_server` as a computed FQDN; existing `DNS_ZONE_ID`, `DNS_ZONE_NAME`, `DNS_ZONE_FQDN` already declared). `DNS_NAMESERVERS` (plural) from issue #248 is satisfied by this single nameserver output.
- API contract: none
- OpenAPI / Pact contract path: none
- Event contract: none
- Make/CLI contract: none — `infra-dns-{plan,apply,smoke,destroy}` targets already exist
- Docs contract: `docs/platform/modules/dns/README.md` to be expanded with a standalone TF module section, runtime state contract table, and smoke check documentation.

## Blueprint Upstream Defect Escalation (Normative)
- Upstream issue URL: none
- Temporary workaround path: none
- Replacement trigger: none
- Workaround review date: none

## Normative Acceptance Criteria

- AC-001 `infra/cloud/stackit/terraform/modules/dns/main.tf` declares `stackit_dns_zone.this` with `project_id`, `name`, and `dns_name = trimsuffix(var.dns_zone_fqdn, ".")`.
- AC-002 `infra/cloud/stackit/terraform/modules/dns/variables.tf` declares all five variables: `stackit_project_id`, `stackit_region`, `dns_zone_name`, `dns_zone_fqdn`, `dns_record_ttl`.
- AC-003 `infra/cloud/stackit/terraform/modules/dns/outputs.tf` declares `zone_id` (from `stackit_dns_zone.this.zone_id`), `dns_name` (from `stackit_dns_zone.this.dns_name`), and `primary_name_server` (from `stackit_dns_zone.this.primary_name_server`).
- AC-004 `infra/cloud/stackit/terraform/modules/dns/versions.tf` declares the `stackitcloud/stackit` required provider at version `= 0.88.0`.
- AC-005 `scripts/bin/infra/dns_smoke.sh` validates `zone_id` is non-empty in the runtime state file.
- AC-006 `scripts/bin/infra/dns_smoke.sh` validates `zone_fqdn` is non-empty in the runtime state file.
- AC-007 `terraform validate` passes from `infra/cloud/stackit/terraform/modules/dns/`.
- AC-008 `tests/infra/modules/dns/test_contract.py` has an entry in `scripts/lib/quality/test_pyramid_contract.json` under the `unit` scope, added before the test file is created.
- AC-009 `tests/infra/modules/dns/test_contract.py` passes with ≥ 10 assertions, all green.
- AC-010 The runtime state file (`artifacts/infra/dns_runtime.env`) contains `zone_id`, `zone_name`, and `zone_fqdn` keys after a STACKIT-lane apply (validated by AC-005 + AC-006 smoke checks).
- AC-011 `blueprint/modules/dns/module.contract.yaml` includes `DNS_PRIMARY_NAME_SERVER` under `outputs.produced`, and `dns_apply.sh` writes `primary_name_server` to the runtime state file.

## Informative Notes (Non-Normative)
- Context: This is one of 5 remaining stub modules under issue #248. The other 4 (public-endpoints, observability, workflows, identity-aware-proxy) will be implemented in separate work items after this one.
- Shell layer completeness: All four DNS scripts and `dns.sh` already exist and are mostly complete. The implementation gap is the TF module files (all four `.tf` files), a minor smoke strengthening (adding zone_id and zone_fqdn checks), and the test contract file.
- Foundation alignment: The foundation `main.tf` uses `for_each` across multiple zones; the standalone module provisions exactly one zone. The resource attribute structure is identical.
- DNSSEC: STACKIT manages DNSSEC at the platform level per Q-2 resolution (Option A). No TF attribute controls it in v0.88.0.

## Explicit Exclusions
- DNS record management (`stackit_dns_record_set`) — zone provisioning only; record management is a consumer responsibility.
- `public-endpoints`, `observability`, `workflows`, `identity-aware-proxy` modules — separate work items.
- Local-lane equivalent — STACKIT-only module; local lane remains `noop`.
- `DNS_NAMESERVERS` output — deferred pending Q-1 resolution.
- Multi-zone provisioning via the standalone module — one zone per module invocation.
