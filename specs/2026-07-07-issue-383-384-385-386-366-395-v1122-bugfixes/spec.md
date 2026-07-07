# Specification

## Spec Readiness Gate (Blocking)
- SPEC_READY: true
- SPEC_PRODUCT_READY: true
- Open questions count: 0
- Unresolved alternatives count: 0
- Unresolved TODO markers count: 0
- Pending assumptions count: 0
- Open clarification markers count: 0
- Product sign-off: bonos
- Architecture sign-off: bonos
- Security sign-off: bonos
- Operations sign-off: bonos
- Missing input blocker token: none
- ADR path: none
- ADR status: none
- SPEC_READY_EXCEPTION: bug-fix
- authorized-by: bonos

## Applicable Guardrail Controls (Normative)
- Applicable control IDs: SDD-C-001, SDD-C-002
- Control exception rationale: Bug-fix bypass track; module contract + shell script + Helm values changes with no API, event, or schema impact.

## Implementation Stack Profile (Normative)
- Backend stack profile: none
- Frontend stack profile: none
- Test automation profile: none
- Agent execution model: none
- Managed service preference: stackit-managed-first
- Managed service exception rationale: none
- Runtime profile: local-first-docker-desktop-kubernetes
- Local Kubernetes context policy: docker-desktop-preferred
- Local provisioning stack: crossplane-plus-helm
- Runtime identity baseline: eso-plus-argocd-plus-keycloak
- Local-first exception rationale: none
- Has user-facing flow: false <!-- inferred from intake: no UI/flow signals found — confirm before SPEC_READY -->
- E2E gate classification: N/A

## Objective
- Business outcome: Six P2 infrastructure bugs fixed on the release/v1.12.x branch so consumers on v1.12.1 can upgrade to v1.12.2 without taking factory/orchestrator changes.
- Success metric: All six bugs closed; fresh STACKIT optional-module bootstrap succeeds without placeholder collisions, provider validation errors, or GitOps drift loops; local RabbitMQ provision succeeds without Bitnami image security gate rejection.

## Normative Requirements

### Functional Requirements (Normative)

- FR-001 MUST move `POSTGRES_INSTANCE_NAME` from `required_env` to `optional_env` in `blueprint/modules/postgres/module.contract.yaml`; `stackit_layers.sh` MUST emit `-var=postgres_instance_name=` only when the variable is non-empty (fixes #383).
- FR-002 MUST move `OBJECT_STORAGE_BUCKET_NAME` from `required_env` to `optional_env` in `blueprint/modules/object-storage/module.contract.yaml`; `stackit_layers.sh` MUST emit `-var=object_storage_bucket_name=` only when the variable is non-empty; `object_storage.sh` MUST remove the `require_env_vars OBJECT_STORAGE_BUCKET_NAME` call that is rendered inert by the preceding `set_default_env` (fixes #384).
- FR-003 MUST move `RABBITMQ_INSTANCE_NAME` from `required_env` to `optional_env` in `blueprint/modules/rabbitmq/module.contract.yaml`; `stackit_layers.sh` MUST emit `-var=rabbitmq_instance_name=` only when the variable is non-empty; `rabbitmq.sh` MUST NOT unconditionally require `RABBITMQ_INSTANCE_NAME` (fixes #385, instance-name part).
- FR-004 MUST move `OPENSEARCH_INSTANCE_NAME` from `required_env` to `optional_env` in `blueprint/modules/opensearch/module.contract.yaml`; `stackit_layers.sh` MUST emit `-var=opensearch_instance_name=` only when the variable is non-empty; `opensearch.sh` MUST NOT unconditionally require `OPENSEARCH_INSTANCE_NAME`; the `OPENSEARCH_VERSION` default MUST be corrected to `"2"` and `OPENSEARCH_PLAN_NAME` default MUST be corrected to the current active STACKIT OpenSearch replica plan slug (fixes #385, OpenSearch defaults part).
- FR-005 MUST move `POSTGRES_PASSWORD` from `required_env` to `optional_env` in `blueprint/modules/postgres/module.contract.yaml`; `postgres_init_env()` in `postgres.sh` MUST require `POSTGRES_PASSWORD` only on non-STACKIT provisioning paths; STACKIT profiles MUST NOT require it as an input (fixes #386).
- FR-006 MUST add `global.security.allowInsecureImages: true` to both `infra/local/helm/rabbitmq/values.yaml` and `scripts/templates/infra/bootstrap/infra/local/helm/rabbitmq/values.yaml` so the `bitnami/rabbitmq` chart accepts the pinned `bitnamilegacy/rabbitmq` image (fixes #366).
- FR-007 MUST skip `run_manifest_apply "$gateway_manifest_path"` in `public_endpoints_deploy.sh` when `deploy_driver=argocd_application_chart`; in that mode Gateway objects are managed by GitOps and the direct apply causes a drift/flip loop with ArgoCD self-heal (fixes #395).

### Non-Functional Requirements (Normative)
- NFR-SEC-001 MUST NOT introduce new required secrets or credentials; the `bitnamilegacy` image is the official Bitnami multi-arch image — `allowInsecureImages: true` is safe in this context.
- NFR-REL-001 All `stackit_layers.sh` conditional var-emit changes MUST be safe for re-runs; omitting a Terraform `-var=` flag when the variable is unset MUST NOT cause a plan diff on already-provisioned resources (Terraform falls back to the derived `locals.tf` value, which is identical).
- NFR-OPS-001 Operators MUST NOT be required to set `POSTGRES_INSTANCE_NAME`, `OBJECT_STORAGE_BUCKET_NAME`, `RABBITMQ_INSTANCE_NAME`, or `OPENSEARCH_INSTANCE_NAME` as global defaults in `blueprint/repo.init.env`; removing them from that file after upgrade MUST NOT break `blueprint-check-placeholders`.

## Normative Option Decision
- Option A (FR-007): Skip the gateway manifest apply entirely in `argocd_application_chart` mode — trust GitOps to manage Gateway objects.
- Option B (FR-007): Add `PUBLIC_ENDPOINTS_SKIP_GATEWAY_MANIFEST_APPLY=true` escape hatch for operators who manage Gateway objects via GitOps.
- Selected option: OPTION_A
- Rationale: In `argocd_application_chart` mode GitOps ownership is the invariant; applying the manifest directly is always wrong. An escape hatch implies it is sometimes correct to apply, which it is not. Option A is simpler, produces no false-safe opt-outs, and aligns with the existing `argocd_optional_manifest` pattern where the deploy step defers entirely to GitOps.

## Contract Changes (Normative)
- Config/Env contract: Six module contract YAML files updated (`required_env` → `optional_env`). Consumers who relied on `blueprint-check-placeholders` to enforce these vars will no longer be blocked.
- API contract: none
- OpenAPI / Pact contract path: none
- Event contract: none
- Make/CLI contract: none
- Docs contract: none

## Blueprint Upstream Defect Escalation (Normative)
- Upstream issue URL: https://github.com/bitnami/charts/issues/30850
- Temporary workaround path: Add `global.security.allowInsecureImages: true` to values files
- Replacement trigger: Bitnami publishes `bitnami/rabbitmq` images in the standard namespace, making the `bitnamilegacy` pin unnecessary.
- Workaround review date: 2026-10-01

## Normative Acceptance Criteria

- AC-001 [postgres instance name optional] — `make blueprint-check-placeholders` MUST pass with `POSTGRES_ENABLED=true` and `POSTGRES_INSTANCE_NAME` unset; verified by a test that asserts the placeholder gate exits 0 and emits no FATAL line for `POSTGRES_INSTANCE_NAME`.
- AC-002 [object-storage bucket name optional] — `make blueprint-check-placeholders` MUST pass with `OBJECT_STORAGE_ENABLED=true` and `OBJECT_STORAGE_BUCKET_NAME` unset; verified by a test asserting the placeholder gate exits 0 and emits no FATAL line for `OBJECT_STORAGE_BUCKET_NAME`.
- AC-003 [rabbitmq instance name optional] — `make blueprint-check-placeholders` MUST pass with `RABBITMQ_ENABLED=true` and `RABBITMQ_INSTANCE_NAME` unset; `stackit_layers.sh` MUST NOT emit `-var=rabbitmq_instance_name=` when the variable is unset; verified by a unit assertion on the layer-var emission function output.
- AC-004 [opensearch instance name + defaults] — `make blueprint-check-placeholders` MUST pass with `OPENSEARCH_ENABLED=true` and `OPENSEARCH_INSTANCE_NAME` unset; `OPENSEARCH_VERSION` default value in `module.contract.yaml` MUST equal `"2"`; `OPENSEARCH_PLAN_NAME` default MUST equal the corrected plan slug; verified by module contract content assertions.
- AC-005 [postgres password STACKIT-optional] — sourcing `postgres_init_env()` with `BLUEPRINT_PROFILE=stackit-dev` and `POSTGRES_PASSWORD` unset MUST exit 0; verified by a test asserting the function does not call `require_env_vars POSTGRES_PASSWORD` on STACKIT profiles.
- AC-006 [rabbitmq local provision values] — both `infra/local/helm/rabbitmq/values.yaml` and its bootstrap template MUST contain `allowInsecureImages: true` under `global.security`; verified by a test asserting the key is present in both files.
- AC-007 [public-endpoints no gateway drift] — `public_endpoints_deploy.sh` in `argocd_application_chart` mode MUST NOT invoke `run_manifest_apply` with the gateway manifest path; verified by a test asserting the gateway manifest apply call is absent from the `argocd_application_chart` branch of the script.

## Informative Notes (Non-Normative)
- Context: All six bugs affect v1.12.0/v1.12.1 consumers and are independent of the factory epic.
- #383/#384/#385 share the same root cause: module contracts over-declared required env vars that Terraform derives automatically from `naming_prefix`. The pattern was replicated across four modules.
- The OpenSearch plan slug correction in FR-004 should be verified against the current STACKIT OpenSearch provider plan list before implementation — the exact slug may vary; the principle (major-version string only, active replica plan) is normative.
- #386 (POSTGRES_PASSWORD) is distinct from #383–385: the variable is a provider output, never an input variable, so it cannot be set before provisioning.
- #366 is a Bitnami upstream chart breaking change; `allowInsecureImages: true` is the documented upstream workaround per bitnami/charts#30850.

## Explicit Exclusions
- #394 (kubeconfig TTL / auto-taint) — more complex; targets v1.12.3 or later.
- #346 (upgrade pipeline .pre-commit-config.yaml clobber) — different surface (upgrade tooling); targets v1.12.3 or later.
- No Terraform provider version bumps, no ArgoCD manifest changes, no new make targets.

## Potential Deferred Proposals
- Auto-discovery of current STACKIT OpenSearch plan slug: a future work item could query the STACKIT API at `terraform plan` time and fail-fast with a descriptive error if the configured plan is unavailable. Deferred: requires Terraform provider data source work, out of scope for a patch release.
- Consumer migration guide for removed required vars: a `make blueprint-upgrade-consumer` enhancement that detects now-optional vars in `blueprint/repo.init.env` and emits a migration warning. Deferred to the #167 upgrade tooling track.
