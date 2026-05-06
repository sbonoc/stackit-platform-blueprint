# Specification

## Spec Readiness Gate (Blocking)
<!-- SPEC_PRODUCT_READY=true: intake gate — Product sign-off only; unlocks agent ADR drafting.
     SPEC_READY=true: implementation gate — all sign-offs required; unlocks coding. -->
- SPEC_READY: false
- SPEC_PRODUCT_READY: false
- Open questions count: 2
- Unresolved alternatives count: 1
- Unresolved TODO markers count: 0
- Pending assumptions count: 0
- Open clarification markers count: 2
- Product sign-off: pending
- Architecture sign-off: pending
- Security sign-off: pending
- Operations sign-off: pending
- Missing input blocker token: none
- ADR path: docs/blueprint/architecture/decisions/ADR-issue-248-opensearch-module.md
- ADR status: proposed

## Applicable Guardrail Controls (Normative)
- Applicable control IDs: SDD-C-001, SDD-C-002, SDD-C-003, SDD-C-004, SDD-C-005, SDD-C-006, SDD-C-007, SDD-C-008, SDD-C-009, SDD-C-010, SDD-C-011, SDD-C-012, SDD-C-013, SDD-C-014, SDD-C-015, SDD-C-016, SDD-C-017, SDD-C-018, SDD-C-019, SDD-C-020, SDD-C-021
- Control exception rationale: none

## Implementation Stack Profile (Normative)
- Backend stack profile: python_plus_fastapi_pydantic_v2
- Frontend stack profile: none — infrastructure-only work item
- Test automation profile: pytest_vitest_playwright_pact
- Agent execution model: specialized-subagents-isolated-worktrees
- Managed service preference: stackit-managed-first
- Managed service exception rationale: local lane uses Bitnami OpenSearch Helm chart (dev-only, not production-managed); this is the established blueprint pattern for local lane provisioning
- Runtime profile: local-first-docker-desktop-kubernetes
- Local Kubernetes context policy: docker-desktop-preferred
- Local provisioning stack: crossplane-plus-helm
- Runtime identity baseline: eso-plus-argocd-plus-keycloak
- Local-first exception rationale: none

## Objective
- Business outcome: Make `infra-opensearch-apply` non-noop on both local and STACKIT lanes so that dhe-marketplace PR #61 can unblock its STACKIT lane, and local development can independently provision OpenSearch without coupling to the OpenMetadata Helm stack.
- Success metric: `infra-opensearch-apply` provisions a live OpenSearch endpoint on both lanes; `infra-opensearch-smoke` validates all 8 declared contract outputs are non-empty; `tests/infra/modules/opensearch/test_contract.py` passes.

## Normative Requirements

### Functional Requirements (Normative)
- FR-001 MUST implement `infra/cloud/stackit/terraform/modules/opensearch/main.tf` with `stackit_opensearch_instance` and `stackit_opensearch_credential` resources that expose all outputs declared in `blueprint/modules/opensearch/module.contract.yaml` (`OPENSEARCH_HOST`, `OPENSEARCH_HOSTS`, `OPENSEARCH_PORT`, `OPENSEARCH_SCHEME`, `OPENSEARCH_URI`, `OPENSEARCH_DASHBOARD_URL`, `OPENSEARCH_USERNAME`, `OPENSEARCH_PASSWORD`).
- FR-002 MUST add `infra/local/helm/opensearch/values.yaml` with a single-node Bitnami OpenSearch chart configuration sized for development (memory limit ≤ 1 GB, persistence disabled, `fullnameOverride: "blueprint-opensearch"`).
- FR-003 MUST update `scripts/lib/infra/module_execution.sh` opensearch cases to route `opensearch:plan | opensearch:apply` and `opensearch:destroy` to `helm` driver when `is_local_profile` (replacing the current `noop` driver).
- FR-004 MUST update `scripts/lib/infra/opensearch.sh` to add local-lane resolution functions: `opensearch_local_service_host()`, `opensearch_local_port()`, `opensearch_local_scheme()`, `opensearch_local_username()`, `opensearch_local_password()`, and update all output functions to branch on `is_local_profile` and return correct local values.
- FR-005 MUST add `OPENSEARCH_HELM_CHART_VERSION_PIN`, `OPENSEARCH_LOCAL_IMAGE_REGISTRY`, `OPENSEARCH_LOCAL_IMAGE_REPOSITORY`, and `OPENSEARCH_LOCAL_IMAGE_TAG` to `scripts/lib/infra/versions.sh`.
- FR-006 MUST update `scripts/lib/infra/opensearch.sh` `opensearch_init_env()` to set local Helm release defaults (`OPENSEARCH_NAMESPACE`, `OPENSEARCH_HELM_RELEASE`, `OPENSEARCH_HELM_CHART`, `OPENSEARCH_HELM_CHART_VERSION`).
- FR-007 MUST add a `render_values_file` capability to `opensearch.sh` analogous to `postgres_render_values_file()` so that `opensearch_apply.sh` can call `run_helm_upgrade_install` with a rendered values file.
- FR-008 MUST add `tests/infra/modules/opensearch/test_contract.py` with a contract test asserting that after local-lane apply, the `opensearch_runtime` state file exists and all 8 declared contract output keys are present and non-empty.
- FR-009 MUST update `docs/platform/modules/opensearch/README.md` to document both lanes with usage examples, env-var reference, and prerequisite notes.
- FR-010 MUST add `scripts/bin/infra/opensearch_smoke.sh` implementation that validates `OPENSEARCH_URI` is non-empty and HTTPS-formatted (STACKIT) or HTTP-formatted with port 9200 (local), and that `OPENSEARCH_DASHBOARD_URL` is non-empty.

### Non-Functional Requirements (Normative)
- NFR-SEC-001 MUST NOT log `OPENSEARCH_PASSWORD` in plain text; all state file writes and log lines MUST treat the password as sensitive (masked or omitted from human-readable output).
- NFR-SEC-002 MUST expose admin-level credentials: `OPENSEARCH_USERNAME` / `OPENSEARCH_PASSWORD` MUST grant sufficient access to call the OpenSearch Security API and create per-app roles/users. On STACKIT, the `stackit_opensearch_credential` resource MUST produce admin-level credentials; if the provider restricts credential level, a stop condition is triggered and issue #248 MUST be updated before proceeding.
- NFR-OBS-001 `opensearch_apply.sh` MUST emit `infra_opensearch_apply` metric with `status=success|failure` and `driver=<driver>` tags at script exit; existing metric trap already covers this — do not remove.
- NFR-REL-001 The Terraform module `infra/cloud/stackit/terraform/modules/opensearch/main.tf` MUST declare `lifecycle { create_before_destroy = true }` on `stackit_opensearch_instance` or document a controlled migration procedure in the module README; silent destroy/recreate on version change is forbidden.
- NFR-OPS-001 The `opensearch_runtime` state file MUST include keys: `profile`, `stack`, `tooling_mode`, `provision_driver`, `host`, `port`, `scheme`, `uri`, `username`, `dashboard_url`, and `timestamp_utc`; `password` MUST be written to the state file (it is read by downstream scripts) but MUST be redacted in any human-readable summary output.
- NFR-A11Y-001 N/A — this is an infrastructure-only work item with no UI components.

## Normative Option Decision

> **[NEEDS CLARIFICATION — Q-1]** The issue requests explicit dual-lane make targets (`infra-opensearch-local-apply`, `infra-opensearch-stackit-apply`). The existing blueprint convention uses a single target per action (`infra-opensearch-apply`) with profile-based routing inside the script. Both patterns are valid; they differ in operator UX and discoverability.
>
> **Options:**
> - **A) Follow existing blueprint convention** — keep `infra-opensearch-{plan,apply,smoke,destroy}` with profile-routing; post a comment on issue #248 explaining the deviation. Zero risk to existing consumers and CI; aligns with postgres/rabbitmq/object-storage patterns already shipped. *(Agent recommendation)*
> - **B) Follow issue-requested naming** — add `infra-opensearch-{local,stackit}-{apply,smoke,destroy}` as the canonical targets and update the module contract, makefile template, and `module_execution.sh` to support the dual-lane naming axis for opensearch specifically.
>
> **Agent recommendation:** Option A — the existing convention is already validated across three other modules (postgres, rabbitmq, object-storage) with local lanes. Introducing a dual-lane naming axis for opensearch only would produce an inconsistent namespace that breaks the `make help` discoverability pattern and the `test_optional_module_make_targets_materialize_only_when_enabled` test. Dual-lane naming MUST be applied as a cross-cutting blueprint change to all modules in a separate work item, not to opensearch alone.

- Option A: Follow existing convention — `infra-opensearch-{plan,apply,smoke,destroy}` with internal profile-routing; post comment on issue #248 explaining deviation
- Option B: Follow issue request — add explicit `infra-opensearch-{local,stackit}-{apply,smoke,destroy}` targets; update contract YAML, makefile template, and `module_execution.sh`
- Selected option: OPTION_UNRESOLVED
- Rationale: [NEEDS CLARIFICATION — Q-1] awaiting maintainer decision before implementation begins

> **[NEEDS CLARIFICATION — Q-2]** The issue requires admin-level credentials (`OPENSEARCH_USERNAME` / `OPENSEARCH_PASSWORD`) with OS Security API access to create per-app roles/users. The `stackit_opensearch_credential` Terraform resource creates a default credential. STACKIT documentation does not explicitly confirm whether this credential has admin-level (Security API) access or is user-scoped.
>
> **Options:**
> - **A) Proceed with `stackit_opensearch_credential`** — assume the provider-generated credential is admin-level based on STACKIT managed-service behavior (confirmed by maintainer or STACKIT docs reference). *(Agent recommendation pending confirmation)*
> - **B) Stop condition** — if STACKIT OpenSearch does not expose admin-level credentials via Terraform, this is a stop condition per CLAUDE.md §Stop conditions; post on issue #248 and await maintainer direction.
>
> **Agent recommendation:** Q-2 must be confirmed before STACKIT lane implementation begins. If the maintainer confirms the credential is admin-level, proceed with Option A. If not, trigger the stop condition.

## Contract Changes (Normative)
- Config/Env contract: No new env variables added. `OPENSEARCH_NAMESPACE`, `OPENSEARCH_HELM_RELEASE`, `OPENSEARCH_HELM_CHART`, `OPENSEARCH_HELM_CHART_VERSION` added as internal defaults in `opensearch_init_env()`; these are not consumer-facing contract outputs.
- API contract: none
- OpenAPI / Pact contract path: none
- Event contract: none
- Make/CLI contract: `infra-opensearch-{plan,apply,smoke,destroy}` targets remain unchanged in naming (per Option A). `infra-opensearch-apply` on local profile changes from `noop` to `helm` driver — this is a behavior addition, not a breaking change.
- Docs contract: `docs/platform/modules/opensearch/README.md` updated with dual-lane documentation.
- Module contract: `blueprint/modules/opensearch/module.contract.yaml` — no changes; outputs are already declared. If Q-1 resolves to Option B, make targets in the contract YAML will also be updated.

## Blueprint Upstream Defect Escalation (Normative)
- Upstream issue URL: none
- Temporary workaround path: none (the noop local lane is the current workaround; this work item replaces it)
- Replacement trigger: none
- Workaround review date: none

## Normative Acceptance Criteria
- AC-001 MUST: `infra-opensearch-apply` executed with `BLUEPRINT_PROFILE=local-*` provisions a Helm release `blueprint-opensearch` in the configured namespace; the resulting `opensearch_runtime` state file MUST contain non-empty values for `host`, `port`, `scheme`, `uri`, `username`, and `password`.
- AC-002 MUST: `infra-opensearch-apply` executed with `BLUEPRINT_PROFILE=stackit-*` provisions a STACKIT managed OpenSearch instance and writes `opensearch_runtime` state with all 8 contract outputs non-empty.
- AC-003 MUST: `infra-opensearch-smoke` passes in `local-*` profile with state file present; MUST validate that `OPENSEARCH_URI` is non-empty and endpoint-formatted, and `OPENSEARCH_DASHBOARD_URL` is non-empty.
- AC-004 MUST: `infra-opensearch-smoke` passes in `stackit-*` profile with the same validations as AC-003.
- AC-005 MUST: `infra-opensearch-destroy` in `local-*` profile uninstalls the `blueprint-opensearch` Helm release and writes a destroy state artifact; no K8s resources in the configured namespace MUST remain after destroy.
- AC-006 MUST: `infra-opensearch-destroy` in `stackit-*` profile triggers `stackit_foundation_apply` with `opensearch_enabled=false` and removes the STACKIT instance.
- AC-007 MUST: `infra/cloud/stackit/terraform/modules/opensearch/main.tf` declares at minimum `stackit_opensearch_instance` and `stackit_opensearch_credential` resources, along with `variables.tf` and `outputs.tf` exposing all 8 contract outputs.
- AC-008 MUST: `tests/infra/modules/opensearch/test_contract.py` passes with at least one test asserting that all 8 contract output keys are present and non-empty in the `opensearch_runtime` state file after a mock or real apply.
- AC-009 MUST: `make quality-hooks-fast` passes with zero violations after all changes are applied.
- AC-010 MUST: `scripts/lib/infra/versions.sh` declares `OPENSEARCH_HELM_CHART_VERSION_PIN`, `OPENSEARCH_LOCAL_IMAGE_REGISTRY`, `OPENSEARCH_LOCAL_IMAGE_REPOSITORY`, and `OPENSEARCH_LOCAL_IMAGE_TAG`.

## Informative Notes (Non-Normative)
- Context: The opensearch module is critical-path for dhe-marketplace PR #61 (STACKIT lane). The local lane decouples OpenSearch lifecycle from the OpenMetadata Helm bundling workaround. Both lanes already have the script skeleton (`opensearch_apply.sh`, `opensearch_destroy.sh`, etc.) — the STACKIT route via `foundation_contract` already works; only the local lane is `noop` today.
- Tradeoffs: Bitnami `bitnamilegacy/opensearch` images are used for the local lane (same pattern as postgres/rabbitmq); despite the `legacy` namespace, the pinned tag is the latest-stable supported image.
- Clarifications:
  - [NEEDS CLARIFICATION — Q-1] Naming convention: single target with profile-routing vs explicit dual-lane targets. See Option Decision above.
  - [NEEDS CLARIFICATION — Q-2] Admin credential level for `stackit_opensearch_credential`. See Option Decision above.

## Explicit Exclusions
- Changes to consumer repositories (dhe-marketplace, others) — separate consumer-side PRs after blueprint release.
- Refactoring OpenMetadata Helm bundling of OpenSearch in `apps-openmetadata-local-apply` — tracked as consumer-side follow-up per issue #248.
- Implementation of any module other than opensearch — sequential, one module per PR.
- Cutting blueprint releases — maintainer responsibility after PR merge.
- `langfuse` and `neo4j` modules — explicitly deferred per issue #248.
