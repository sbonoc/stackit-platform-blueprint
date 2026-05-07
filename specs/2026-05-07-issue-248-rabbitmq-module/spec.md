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
- ADR path: docs/blueprint/architecture/decisions/ADR-issue-248-rabbitmq-module.md
- ADR status: proposed

## Applicable Guardrail Controls (Normative)
- Applicable control IDs: SDD-C-001, SDD-C-002, SDD-C-003, SDD-C-004, SDD-C-005, SDD-C-006, SDD-C-007, SDD-C-008, SDD-C-009, SDD-C-010, SDD-C-011, SDD-C-012, SDD-C-013, SDD-C-014, SDD-C-015, SDD-C-016, SDD-C-017, SDD-C-018, SDD-C-019, SDD-C-020, SDD-C-021
- Control exception rationale:
  - SDD-C-015: No app onboarding make-target contract changes — this work item affects only infra module wrappers, not app delivery workflows.
  - SDD-C-018: No blueprint upstream defect escalation — this is a blueprint-internal implementation.
  - SDD-C-022: Not applicable — no HTTP route handlers or new API endpoints in scope.
  - SDD-C-023: Not applicable — no filter or payload-transform logic in scope.
  - SDD-C-024: Not applicable — no pre-PR smoke/curl/deterministic-check findings to translate; no reproducible failures exist at intake time.

## Implementation Stack Profile (Normative)
- Backend stack profile: python_plus_fastapi_pydantic_v2
- Frontend stack profile: none
- Test automation profile: pytest_vitest_playwright_pact
- Agent execution model: specialized-subagents-isolated-worktrees
- Managed service preference: stackit-managed-first
- Managed service exception rationale: local lane uses Bitnami rabbitmq Helm chart (dev-only, not production-managed); this is the established blueprint pattern for local lane provisioning
- Runtime profile: local-first-docker-desktop-kubernetes
- Local Kubernetes context policy: docker-desktop-preferred
- Local provisioning stack: crossplane-plus-helm
- Runtime identity baseline: eso-plus-argocd-plus-keycloak
- Local-first exception rationale: none

## Objective
- Business outcome: Elevate the rabbitmq module from partial scaffold to production-grade optional module: complete STACKIT standalone Terraform module (`stackit_rabbitmq_instance` + `stackit_rabbitmq_credential` resources), two missing contract output keys added to `module.contract.yaml` (`RABBITMQ_VHOST` and `RABBITMQ_MANAGEMENT_URL`), two new shell functions (`rabbitmq_vhost()` and `rabbitmq_management_url()`), expanded state file to all seven contract output keys, hardened smoke validations, updated `rabbitmq_apply.sh` state file write, and complete module documentation with verified test coverage.
- Success metric: `pytest tests/infra/modules/rabbitmq/ -v` passes (≥ 20 assertions); `QUALITY_HOOKS_KEEP_GOING=true make quality-hooks-fast` passes; local lane state file contains all seven contract keys including `vhost` and `management_url`.

## Normative Requirements

### Functional Requirements (Normative)

- FR-001 MUST implement the STACKIT standalone Terraform module at `infra/cloud/stackit/terraform/modules/rabbitmq/` with two resources: `stackit_rabbitmq_instance` and `stackit_rabbitmq_credential`; the module MUST mirror the foundation pattern already in `infra/cloud/stackit/terraform/foundation/main.tf`.
- FR-002 MUST add `RABBITMQ_VHOST` and `RABBITMQ_MANAGEMENT_URL` to the `outputs.produced` list in `blueprint/modules/rabbitmq/module.contract.yaml`, bringing the total produced outputs to seven.
- FR-003 MUST add `rabbitmq_vhost()` to `scripts/lib/infra/rabbitmq.sh`; on both lanes the function MUST return the literal string `/` (the RabbitMQ default vhost); STACKIT `stackit_rabbitmq_credential` exposes no `vhost` attribute, so the constant `/` is the only correct value.
- FR-004 MUST add `rabbitmq_management_url()` to `scripts/lib/infra/rabbitmq.sh`; on the STACKIT lane it MUST read `stackit_foundation_output_value_or_default "rabbitmq_management_url" ""` (provider attribute is named `management`; the foundation output key MUST be named `rabbitmq_management_url`); on the local lane it MUST construct the URL from `rabbitmq_host` and the management port (default `15672`).
- FR-005 MUST update `scripts/bin/infra/rabbitmq_apply.sh` to write all seven contract-declared keys to the runtime state file: existing keys (`host`, `port`, `uri`, `username`, `password`) plus two new keys (`vhost` and `management_url`); the `write_state_file` call MUST include `"vhost=$(rabbitmq_vhost)"` and `"management_url=$(rabbitmq_management_url)"`.
- FR-006 MUST add explicit smoke validations beyond URI format: `host` MUST be non-empty, `port` MUST be non-empty, `vhost` MUST be non-empty, and `management_url` MUST be non-empty in `scripts/bin/infra/rabbitmq_smoke.sh` state file checks.
- FR-007 MUST implement `variables.tf` and `outputs.tf` for the STACKIT Terraform module; `variables.tf` MUST declare all inputs (`rabbitmq_instance_name`, `rabbitmq_version`, `rabbitmq_plan_name`, `stackit_project_id`, `stackit_region`); `outputs.tf` MUST expose `rabbitmq_host`, `rabbitmq_port`, `rabbitmq_username`, `rabbitmq_password`, `rabbitmq_uri`, `rabbitmq_management_url`.
- FR-008 MUST update `infra/cloud/stackit/terraform/foundation/outputs.tf` (or the equivalent foundation outputs file) to expose `rabbitmq_management_url` from `stackit_rabbitmq_credential.foundation[0].management` so it is reachable via `stackit_foundation_output_value_or_default`.

### Non-Functional Requirements (Normative)

- NFR-SEC-001 MUST NOT expose plaintext credentials in rendered Helm values; the existing K8s Secret `blueprint-rabbitmq-auth` created by `rabbitmq_reconcile_runtime_secret` MUST remain the sole credential delivery path for the local lane; the `rabbitmq_render_values_file()` function MUST NOT introduce new plaintext credential bindings.
- NFR-OBS-001 All four scripts (`rabbitmq_{plan,apply,smoke,destroy}.sh`) MUST emit metric events via the existing `start_script_metric_trap` framework call; no new metric emitters are required beyond the framework guarantee.
- NFR-REL-001 The Terraform module MUST include `lifecycle { create_before_destroy = true }` on the `stackit_rabbitmq_instance` resource to minimize downtime during instance replacement.
- NFR-OPS-001 The runtime state file MUST contain all seven contract output keys (`host`, `port`, `username`, `password`, `uri`, `vhost`, `management_url`); `rabbitmq_smoke.sh` MUST validate `host`, `port`, `vhost`, `management_url`, and the `uri` AMQP prefix.
- NFR-A11Y-001 N/A — no UI component; rabbitmq is an infrastructure module with no browser-facing surface.

## Normative Option Decision

Q-1 resolved: `RABBITMQ_VHOST` defaults to the constant `/` on both lanes — Decision by owner at intake 2026-05-07.

State file key naming (Q-1): The STACKIT `stackit_rabbitmq_credential` resource exposes no `vhost` attribute (confirmed from provider source). The RabbitMQ default vhost is `/`, which is the correct value for the generic module use case. Consumer-side vhost customisation is out of scope. Both lanes return `/` from `rabbitmq_vhost()`. The prefix-strip convention (`RABBITMQ_VHOST` → `vhost`, `RABBITMQ_MANAGEMENT_URL` → `management_url`) is applied to new state file keys; existing keys (`host`, `port`, `username`, `password`, `uri`) are unchanged.

- Option A: Expose `vhost` as a configurable input variable in `module.contract.yaml` and thread it through both lanes.
- Option B: Return constant `/` from `rabbitmq_vhost()` on both lanes; no configurable input needed; consumer manages vhost at consumer level (default vhost `/` is the broker default and correct for generic use).
- Selected option: OPTION_B
- Rationale: The STACKIT provider exposes no `vhost` attribute on credential resources (confirmed from provider source). Making it configurable creates a false promise since the STACKIT lane cannot honour a non-default vhost at the credential level. The constant `/` is always correct for a default-vhost consumer; any non-default vhost scenario is consumer-side configuration. Decision by owner at intake 2026-05-07.

## Contract Changes (Normative)
- Config/Env contract: `RABBITMQ_VHOST` and `RABBITMQ_MANAGEMENT_URL` added to `module.contract.yaml` `outputs.produced`; corresponding runtime state file keys `vhost` and `management_url` added to `artifacts/infra/rabbitmq_runtime.env`; no existing keys renamed; no consumer-visible env var changes to previously produced outputs.
- API contract: none
- OpenAPI / Pact contract path: none
- Event contract: none
- Make/CLI contract: `infra-rabbitmq-{plan,apply,smoke,destroy}` targets unchanged; no new targets.
- Module execution contract: `OPTIONAL_MODULE_EXECUTION_CLASS` unchanged — rabbitmq local lane is already `fallback_runtime`, STACKIT lane is already `provider_backed`; no changes to `module_execution.sh`.
- Docs contract: `docs/platform/modules/rabbitmq/README.md` completed with both-lanes usage, credentials section, vhost section, management URL section, smoke section, and destroy section.

## Blueprint Upstream Defect Escalation (Normative)
- Upstream issue URL: none
- Temporary workaround path: none
- Replacement trigger: none
- Workaround review date: none

## Normative Acceptance Criteria

- AC-001 MUST: STACKIT Terraform module declares `stackit_rabbitmq_instance` and `stackit_rabbitmq_credential` resources in `main.tf` — verified by unit test.
- AC-002 MUST: Terraform `variables.tf` binds all contract inputs (`rabbitmq_instance_name`, `rabbitmq_version`, `rabbitmq_plan_name`, `stackit_project_id`, `stackit_region`) — verified by unit test.
- AC-003 MUST: Terraform `outputs.tf` exposes all contract output keys (`rabbitmq_host`, `rabbitmq_port`, `rabbitmq_username`, `rabbitmq_password`, `rabbitmq_uri`, `rabbitmq_management_url`) — verified by unit test.
- AC-004 MUST: `module.contract.yaml` includes `RABBITMQ_VHOST` and `RABBITMQ_MANAGEMENT_URL` in `outputs.produced` — verified by contract test.
- AC-005 MUST: `rabbitmq_vhost()` returns `/` in both local and STACKIT profile — verified by unit test.
- AC-006 MUST: `rabbitmq_management_url()` returns a non-empty string in local profile and reads foundation output in STACKIT profile — verified by unit test.
- AC-007 MUST: `rabbitmq_apply.sh` state file write includes `vhost` and `management_url` keys — verified by unit test.
- AC-008 MUST: Smoke passes with valid runtime state containing all seven keys — verified by unit test.
- AC-009 MUST: Smoke fails when `uri` does not start with `amqp://` or `amqps://` — verified by unit test.
- AC-010 MUST: Smoke fails when `host` is empty — verified by unit test.
- AC-011 MUST: Smoke fails when `vhost` is empty — verified by unit test.
- AC-012 MUST: Contract test confirms runtime state has all seven declared output keys (`host`, `port`, `username`, `password`, `uri`, `vhost`, `management_url`) — verified by contract test.
- AC-013 MUST: Foundation outputs expose `rabbitmq_management_url` from `stackit_rabbitmq_credential.foundation[0].management` — verified by unit test on Terraform outputs file.
- AC-014 MUST: Smoke fails when `management_url` is empty — verified by unit test.

## Informative Notes (Non-Normative)
- Context: The rabbitmq module is more complete than postgres was: execution class is already correct (`fallback_runtime` for local, `provider_backed` for STACKIT), Secret-backed credential pattern is already implemented (`existingPasswordSecret` in Helm values, `rabbitmq_reconcile_runtime_secret`/`rabbitmq_delete_runtime_secret` in the lib). The main gaps are: the STACKIT standalone Terraform module (stub), two missing contract outputs (`RABBITMQ_VHOST` and `RABBITMQ_MANAGEMENT_URL`), the corresponding shell functions, the state file expansion, hardened smoke checks, test coverage, and docs.
- Tradeoffs: The STACKIT `stackit_rabbitmq_credential` resource exposes a `management` attribute (the management dashboard URL) but no `vhost` attribute. Using the constant `/` for `rabbitmq_vhost()` is accurate for the generic module case and avoids a false configurable-vhost promise. The `management_url` on the local lane is computed from the service host and the Bitnami RabbitMQ management port (15672), which is consistently exposed by the Bitnami chart.
- Clarifications:
  - The STACKIT provider credential resource for RabbitMQ is `stackit_rabbitmq_credential` (not `stackit_rabbitmq_user`) — confirmed from foundation Terraform.
  - The `management` attribute on `stackit_rabbitmq_credential` is the management dashboard URL. The foundation output MUST be named `rabbitmq_management_url` to match the shell function naming convention.
  - The existing `rabbitmq_render_values_file()` already uses `RABBITMQ_PASSWORD_SECRET_NAME` and `RABBITMQ_USERNAME` as template bindings, not plaintext password — the function is already compliant with NFR-SEC-001; no changes to it are required.
  - Q-1 resolved: `rabbitmq_vhost()` returns constant `/` on both lanes. Decision by owner at intake 2026-05-07.

## Explicit Exclusions
- Vhost configuration (beyond the default `/`) for the local or STACKIT lane; consumer-managed vhosts are out of scope and handled at consumer level.
- High-availability replica configuration for the STACKIT lane (configurable via `stackit_rabbitmq_instance.replicas` defaulted to 1; a separate work item covers multi-replica).
- SSL/TLS termination configuration in the local lane (consumers connect via in-cluster service DNS; TLS required only on STACKIT where the provider handles it).
- Shovel, federation, or per-consumer virtual host isolation (deferred to separate work items).
- Connection pooling or consumer-side retry configuration.
