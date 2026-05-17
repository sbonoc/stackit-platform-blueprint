# Hardening Review

## Repository-Wide Findings Fixed

- Finding 1 (resolved — commit `cf5a8bb`): single-zone API vars (`DNS_ZONE_NAME`, `DNS_ZONE_FQDN`, `dns_zone_id()`) still referenced in `scripts/lib/infra/stackit_layers.sh`, `scripts/lib/blueprint/init_repo_env.py`, `tests/blueprint/test_tooling_contracts.py`, and `tests/blueprint/contract_refactor_runtime_identity_cases.py` after the multi-zone rename — three pre-push test regressions caught and fixed before CI. No other repository-wide findings introduced or pre-existed.

## Observability and Diagnostics Changes

- **Runtime state (`dns_runtime.env`):** After `infra-dns-apply`, the following keys are written: `zone_ids` (space-separated STACKIT zone IDs), `zone_fqdns` (space-separated input FQDNs), `zone_count` (integer), `primary_name_servers` (space-separated STACKIT-assigned nameserver FQDNs), `timestamp_utc`. This is the operational signal for downstream modules (e.g., `public-endpoints`) that depend on zone IDs.
- **Smoke state (`dns_smoke.env`):** After `infra-dns-smoke`, the same four contract keys are written alongside `status=passed`. The smoke exit code is the health signal — no separate alerting.
- **Smoke validations (additive, non-breaking):** `zone_count ≥ 1`, `zone_ids` non-empty, `primary_name_servers` non-empty. All three are guards against partial-apply or provider-side provisioning failure.
- **Script logging:** Output prefixed `[dns]` (inherited from existing script scaffolding — no new prefix required).
- **No new metrics, traces, or alerting added.** Smoke exit code is sufficient as the health gate for this module tier.

## Architecture and Code Quality Compliance

- **SOLID / Clean Architecture / DDD:** Single-responsibility enforced — `dns.sh` is the shell contract layer (exposes accessors), `dns_apply.sh` orchestrates the Terraform lifecycle, `dns_smoke.sh` validates runtime state, `dns_plan.sh` records plan artifacts. No cross-cutting concerns violated. No new abstraction layers introduced.
- **Simplicity gate:** 4 TF files (main, variables, outputs, versions) + 4 shell script updates + 1 test file + 1 contract YAML update. No wrapper functions beyond the module pattern requires.
- **Anti-abstraction gate:** Direct `stackit_dns_zone` resource with no wrapper. Mirrors the foundation pattern exactly (`for_each = toset(...)`, `sha1(each.value)` naming, `trimsuffix`).
- **NFR-REL-001 enforced by test:** `test_ac001_main_tf_no_create_before_destroy` confirms `lifecycle { create_before_destroy }` is absent. Zone recreation requires explicit destroy + apply + registrar re-delegation.
- **Test pyramid:** 26 unit assertions in `test_contract.py`; 1 integration test (`test_dns_module_flow` with two-zone fixture). Pyramid ratio: 97.1% unit — within the 60%–100% bound.
- **Documentation consistency:** Module README (blueprint + bootstrap template) updated for multi-zone API. ADR rewritten for multi-zone decisions (D-1 `for_each`, D-3 hash-suffix required, D-5 multi-zone smoke contract). Bootstrap template mirror synchronized.
- **Backward compatibility:** No existing generated consumer has `DNS_ENABLED=true`. Blast radius of API rename (`DNS_ZONE_NAME` / `DNS_ZONE_FQDN` → `DNS_NAMING_PREFIX` / `DNS_ZONE_FQDNS`) is zero for deployed systems.
- **Module contract YAML parity:** `module.contract.yaml` required env and outputs match the shell layer and TF module — verified by `test_optional_module_required_env_contract.py` pre-push gate.

## Accessibility Gate (Normative — non-UI reviewers mark non-applicable items N/A)

- [x] SC 4.1.2 (Name, Role, Value): N/A — no UI or interactive elements
- [x] SC 2.1.1 (Keyboard): N/A — no UI
- [x] SC 2.4.7 (Focus Visible): N/A — no UI
- [x] SC 1.4.1 (Use of Color): N/A — no UI
- [x] SC 3.3.1 (Error Identification): N/A — no UI
- [x] axe-core WCAG 2.1 AA scan evidence: N/A — no UI; NFR-A11Y-001 declared in spec.md as "N/A — no UI or frontend changes"

## Proposals Only (Not Implemented)

- Proposal 1: DNSSEC `dnssec_enabled` variable — provider v0.88.0 has no `dnssec_enabled` attribute; STACKIT manages DNSSEC at the platform level; a no-op variable would mislead consumers (KMS `rotation_period` precedent). Park — `on-scope: infra`.
- Proposal 2: External-DNS K8s controller module — K8s-native dynamic DNS record management via external-dns controller (analogous to ESO for secrets); zone-only TF is the correct separation; no active consumer need for static `stackit_dns_record_set` management. Park — `on-scope: infra` (backlog entry exists).
- Proposal 3: Domain contract JSON pattern — per-env SSOT JSON driving TF tfvars + ArgoCD Helm values; cross-cutting refactor of all optional modules; requires dedicated spec. Park — `on-scope: blueprint` (backlog entry exists).
