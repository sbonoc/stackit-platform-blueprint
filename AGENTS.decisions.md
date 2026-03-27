# Decisions Log

## 2026-03-27
- STACKIT fallback runtime delivery for `rabbitmq`, `public-endpoints`, and `identity-aware-proxy` is now chart-backed and secret-aware.
  - Replaced generic optional `ConfigMap` placeholders with module-specific ArgoCD `Application` templates for `bitnami/rabbitmq`, `ingress-nginx/ingress-nginx`, and `oauth2-proxy/oauth2-proxy`, and expanded ArgoCD `AppProject` repo/namespace/resource allowlists to match the real chart footprint.
  - Local fallback profiles now render deterministic Helm values artifacts under `artifacts/infra/rendered/*.values.yaml` from the scaffold contract, while secret-bearing modules reconcile runtime Kubernetes secrets from wrapper inputs instead of embedding sensitive values in GitOps YAML.
  - Refreshed pinned fallback chart versions to currently resolvable stable releases (`rabbitmq` `16.0.14`, `ingress-nginx` `4.15.1`, `oauth2-proxy` `10.4.0`) and corrected RabbitMQ fallback host outputs to the in-cluster service contract.
  - Identity-Aware Proxy now has an explicit `IAP_COOKIE_SECRET` contract requirement, and shared test reset helpers restore both the default generated Make surface and app manifest state after observability-enabled paths.
  - Rationale: make fallback runtime delivery truthful and production-grade, remove placeholder-only GitOps surfaces, avoid secret leakage into repo-managed manifests, and keep full-suite/test-consumer validation deterministic.

- Generated-repo consumer conformance is now enforced as a scenario matrix.
  - `make blueprint-template-smoke` now accepts profile/module flag inputs, seeds deterministic module env defaults for dry-run generated repos, runs the canonical provision/deploy/smoke/status chain in a temp copy, and asserts contract-driven artifacts, targets, and optional-module scaffolding outcomes.
  - CI `consumer-golden-conformance` now spans representative generated-repo scenarios across `local-lite`, `local-full`, and `stackit-dev`, covering observability/data, runtime-edge, managed-services, fallback-runtime, and workflows combinations.
  - Rationale: keep template-consumer onboarding green across representative profile/module combinations instead of only the default baseline path.

- Optional-module wrappers now resolve execution modes through a shared infra library.
  - Added `scripts/lib/infra/module_execution.sh` to centralize provider-backed, fallback, and external-contract driver selection for optional modules, including consistent path resolution and `optional_module_execution_mode_total` metrics.
  - Optional-module plan/apply/destroy wrappers now keep module-specific actions/state outputs but delegate stack/profile branching to the shared resolver.
  - Rationale: remove duplicated branch logic across wrappers, reduce drift as module coverage grows, and keep execution semantics consistent across stackit/local profiles.

## 2026-03-26 (Template Baseline)
- Blueprint-managed second-wave Make/script hardening is now part of the baseline operating contract.
  - Added canonical quality targets for docs lint/sync (`quality-docs-lint`, `quality-docs-{sync,check}-core-targets`, `quality-docs-{sync,check}-contract-metadata`) and structural test-pyramid enforcement (`quality-test-pyramid`).
  - Namespaced shared helper ownership under `scripts/lib/shell/**` and `scripts/lib/quality/**`, while keeping root shim entrypoints delegating to the new canonical libraries.
  - `docs-build` now refreshes tracked generated references (`docs/reference/generated/core_targets.generated.md`, `docs/reference/generated/contract_metadata.generated.md`), and infra smoke/status flows emit machine-readable diagnostics artifacts (`artifacts/infra/smoke_result.json`, `artifacts/infra/smoke_diagnostics.json`).
  - Rationale: keep Make/docs/contracts synchronized, reduce shared-shell helper drift, and improve CI/operator diagnostics without expanding platform-owned surfaces.

- Execution-ready E2E hardening is the active top-priority lane and is now complete in baseline.
  - Fixed template consumer onboarding drift by excluding init-mutated ArgoCD identity files from strict bootstrap byte-sync validation (`infra/gitops/argocd/environments/dev/platform-application.yaml`, local overlay `appproject.yaml`, and `application-platform-local.yaml`), while keeping identity correctness enforced by `blueprint-check-placeholders`.
  - Rationale: keep template governance strict for static assets without breaking deterministic GitHub-template initialization.

- STACKIT optional-module execution now follows explicit contract modes instead of placeholder Terraform module roots.
  - Provider-backed modules (`observability`, `postgres`, `object-storage`, `dns`, `secrets-manager`) now reconcile through STACKIT `foundation` layer contracts; module destroy performs flag-driven foundation reconciliation (`<MODULE>_ENABLED=false` + foundation apply) rather than standalone per-module destroy.
  - Fallback runtime modules (`rabbitmq`, `public-endpoints`, `identity-aware-proxy`) now reconcile through ArgoCD optional manifests; `kms` is explicit external-automation contract in MVP.
  - Workflows plan/apply/destroy no longer depend on placeholder Terraform module paths; they are API/runtime-contract based.
  - Rationale: eliminate false-positive “successful” module operations against non-functional Terraform roots and make execution semantics truthful.

- Optional manifest scaffolding/prune coverage was extended for STACKIT fallback modules.
  - `infra-bootstrap` now materializes/prunes `infra/gitops/argocd/optional/${ENV}/{rabbitmq,public-endpoints,identity-aware-proxy}.yaml` when corresponding flags toggle.
  - Blueprint and module contracts/docs/tests were synchronized to this behavior.
  - Rationale: keep module enable/disable lifecycle deterministic and lean, with no stale fallback runtime manifests.

- Runtime core bootstrap is now execution-ready and profile-aware.
  - Added `scripts/bin/infra/core_runtime_bootstrap.sh` to install/upgrade ArgoCD and External Secrets Operator before ArgoCD topology apply, and `scripts/bin/infra/core_runtime_smoke.sh` for state-level smoke validation.
  - Added `scripts/bin/infra/local_crossplane_bootstrap.sh` and wired local `infra-provision` to install Crossplane (Helm) in addition to local crossplane kustomize baseline.
  - Rationale: close bootstrap gap where ArgoCD CRDs/operators were assumed but not provisioned, and make local profile explicitly Crossplane-backed for core provisioning.

- Optional-module wrapper skeleton templates are now explicit fail-fast stubs.
  - `scripts/lib/blueprint/generate_module_wrapper_skeletons.py` now emits a consistent not-implemented contract (`status=not_implemented`, metric label, and stable exit code `64`) instead of TODO placeholders.
  - Rationale: avoid false-positive success when a consumer copies a skeleton without implementing module-specific logic.

- Added canonical destroy-before-prune orchestration for disabled optional modules.
  - Introduced `infra-destroy-disabled-modules` (`scripts/bin/infra/destroy_disabled_modules.sh`) and wired it into blueprint-managed Make target generation/contract/docs/tests.
  - Extended module lifecycle runner with `run_disabled_modules_action` metrics (`module_action_disabled_count`, `module_action_disabled_script_count`) to keep execution visibility consistent with enabled-module flows.
  - Rationale: provide an explicit, repeatable teardown step before `infra-bootstrap` pruning when module flags are toggled off after resources already exist.

- STACKIT Terraform identity/state contracts are now init-driven and template-rendered.
  - Added explicit STACKIT init inputs (`BLUEPRINT_STACKIT_REGION`, tenant/platform slugs, project id, tfstate bucket/key prefix) to template bootstrap contract and init flows (interactive + env-file).
  - Converted STACKIT `bootstrap/foundation` tfvars and backend hcl scaffolding to rendered templates, with backend endpoint derived from region and placeholder validation enforced by `blueprint-check-placeholders`.
  - Rationale: remove hardcoded project-specific defaults from committed scaffold, keep generated repositories deterministic, and ensure Stackit state/backend wiring is consumer-specific from day 0.

- STACKIT execution path is now layered and backend-aware by default (`bootstrap` + `foundation`).
  - Added concrete Terraform roots under `infra/cloud/stackit/terraform/{bootstrap,foundation}` with environment tfvars, backend hcl contracts, and managed-service MVP resources (SKE, DNS, Postgres Flex, Object Storage, Secrets Manager, Observability).
  - Updated STACKIT wrappers to run backend-aware Terraform (`init -backend-config ...` + layer var-files), enforce backend compatibility guards, and export richer state/inventory metadata.
  - Rationale: close the execution-readiness gap so STACKIT make targets operate on real Terraform topology instead of placeholder directories.

- ArgoCD STACKIT delivery topology now has an explicit app-of-apps baseline.
  - Added `infra/gitops/argocd/root`, per-environment roots under `infra/gitops/argocd/environments/{dev,stage,prod}`, and stackit overlays with `AppProject` + environment-scoped `ApplicationSet`.
  - Repository init now rewrites ArgoCD GitHub `repoURL` fields together with contract/docs identity updates.
  - Rationale: make GitOps deployment artifacts immediately usable in generated repositories and keep identity wiring deterministic after `make blueprint-init-repo`.

- Added Data Marketplace P0 optional modules to the contract/runtime/tests:
  - `object-storage`, `rabbitmq`, `dns`, `public-endpoints`, `secrets-manager`, `kms`, `identity-aware-proxy`.
  - Makefile materialization, infra bootstrap/prune, module lifecycle, and smoke flows were extended for all modules.
  - Rationale: provide a lean-by-default managed-services baseline for marketplace-style platform bootstraps while keeping modules strictly conditional.

- Keycloak remains a core platform capability; IAP depends on Keycloak OIDC configuration.
  - Modeled in both blueprint/module contracts and runtime wrappers via required `KEYCLOAK_ISSUER_URL`, `KEYCLOAK_CLIENT_ID`, and `KEYCLOAK_CLIENT_SECRET`.
  - Rationale: enforce one canonical identity source and avoid divergent auth models when enabling Identity-Aware Proxy.

- Backlog prioritization is release-driven with explicit template milestones (`v1.0`, `v1.1`, `v1.2`).
  - Rationale: keep roadmap execution focused on consumer adoption outcomes instead of implementation-history tracking.

- Completed P0/P1 template-adoption execution slice:
  - added blueprint lifecycle targets (`blueprint-check-placeholders`, `blueprint-template-smoke`, `blueprint-release-notes`, `blueprint-migrate`),
  - added template release workflow and release-notes generation,
  - enforced template-version compatibility contract in `repository.template_bootstrap`,
  - added migration tooling and upgrade conformance tests for `v1.0.0` baseline no-op/fail-fast behavior.
  - Rationale: make template onboarding, upgradeability, and release operations deterministic before expanding scope.

- Hardened template consistency and optional-module observability:
  - added contract validation for bootstrap static-template drift (live file vs namespaced roots under `scripts/templates/{blueprint,infra}/bootstrap`),
  - synchronized bootstrap docs templates with canonical docs content,
  - added optional-module execution/scaffolding metrics for better run traceability.
  - Rationale: prevent silent template drift and improve operational visibility when module actions are conditionally executed.

- CI quality gating is centralized through `make quality-hooks-run`.
  - Removed duplicated direct CI calls for shellcheck/infra-audit/apps-audit that were already covered by `quality-hooks-run`.
  - Rationale: keep CI deterministic with a single canonical quality gate and reduce maintenance drift between workflow steps.

- Contract-first governance is the canonical operating model.
  - `blueprint/contract.yaml` is the executable source of truth and all automation validates against it.
  - Rationale: keep implementation, docs, tests, and operations synchronized through one contract.

- GitHub Template is the canonical repository generation strategy.
  - Consumers create repos via GitHub template, then run `make blueprint-init-repo`.
  - Rationale: remove manual cloning/copying flows and make onboarding deterministic.

- Repository identity initialization is explicit and automated.
  - `blueprint-init-repo` updates contract metadata and docs identity/edit-link fields from canonical inputs.
  - Rationale: enforce consistent repo naming and ownership metadata in generated repositories.

- Optional modules follow a lean-by-default scaffolding policy.
  - Workflows/Langfuse/Postgres/Neo4j scaffolding is materialized only when corresponding flags are enabled.
  - Rationale: keep generated repos minimal and avoid dead scaffolding.

- Infra execution remains explicitly split by responsibility.
  - Local provisioning: `infra/local/*` (Crossplane/Helm)
  - STACKIT provisioning: `infra/cloud/stackit/terraform/*`
  - Runtime deployment: `infra/gitops/argocd/*`
  - Rationale: preserve deterministic execution boundaries and operational clarity.

- Branch naming follows GitHub Flow purpose prefixes.
  - Policy is enforced through contract validation (`feature/`, `fix/`, `chore/`, `docs/`, etc.).
  - Rationale: keep branch intent explicit and machine-validated.

- STACKIT foundation/runtime operational wrappers are first-class contract targets.
  - Added canonical Make targets for kubeconfig fetch/refresh, runtime prerequisites/inventory/deploy, stackit-specific smoke checks, and an end-to-end stackit provision+deploy chain.
  - Rationale: make STACKIT day-2 operator workflows explicit, reproducible, and discoverable via `make help` while keeping contract/docs/tests synchronized.

- Optional-module Make targets are now materialized conditionally via template rendering.
  - `blueprint-render-makefile` renders `make/blueprint.generated.mk` from `scripts/templates/blueprint/bootstrap/make/blueprint.generated.mk.tmpl` and materializes module targets only when corresponding module flags are enabled.
  - Rationale: keep generated repositories lean and make command surface deterministic to active module scope.

- STACKIT operator lifecycle and diagnostics targets are part of the core contract.
  - Added canonical targets for STACKIT bootstrap/foundation preflight-plan-apply-destroy flows, global STACKIT destroy chain, ArgoCD topology render/validate, infra doctor/context/status snapshots, and `apps-publish-ghcr`.
  - Rationale: align template operational surface with proven STACKIT runbooks from production repository patterns while keeping optional modules conditionally materialized.

- Root infra crossplane scaffold is placeholder-free by default.
  - Removed `provider-helm-placeholder.yaml` from root `infra/local/crossplane` and synchronized bootstrap template/validation logic.
  - Rationale: keep blueprint scaffolding lean and avoid shipping non-executable placeholder manifests in core infra paths.

- Optional-module destroy wrappers execute real cleanup paths in execution mode.
  - Langfuse/Neo4j destroy now delete ArgoCD optional manifests; Postgres/Observability destroy now execute profile-specific terraform/helm cleanup (and observability manifest cleanup) before state cleanup.
  - Rationale: avoid false-positive "destroy" operations that only removed local artifacts and ensure operational targets map to real teardown behavior.

- Runtime execution toggle is canonically `DRY_RUN`.
  - Replaced `BLUEPRINT_EXECUTE_TOOLING` with `DRY_RUN` across scripts and docs, with default `DRY_RUN=true` and live execution enabled via `DRY_RUN=false`.
  - Rationale: use positive dry-run intent and clearer operator ergonomics for safe-by-default execution.

- Reused STACKIT operational ergonomics from `agentic-graphrag` in blueprint form.
  - Added canonical targets/scripts for prerequisites (`infra-prereqs`), full Make reference (`infra-help-reference`), GitHub STACKIT CI setup (`infra-stackit-ci-github-setup`), cached audits (`infra-audit-version-cached`, `apps-audit-versions-cached`), and enhanced redacted runtime inventory exports.
  - Rationale: improve day-0 onboarding, operator usability, and local feedback-loop speed while keeping contract-driven behavior and safe defaults.

- Optional-module scaffolding is now pruned on `infra-bootstrap` when a module flag is disabled.
  - `infra-bootstrap` removes stale module-specific Terraform/Helm/tests/manifest assets (including `dags/` for Workflows) to keep repositories lean after flag toggles.
  - Rationale: enforce lean-by-default continuously, not only on fresh bootstrap runs, and reduce stale-scope confusion in generated repositories.

- Blueprint and infra bootstrap responsibilities are explicitly split.
  - Added blueprint-scoped bootstrap/render targets (`blueprint-bootstrap`, `blueprint-render-makefile`) and moved Makefile materialization and template/hygiene docs sync out of `infra-bootstrap`.
  - `infra-bootstrap` is now infra-only scaffolding/pruning, while blueprint concerns are handled under `scripts/bin/blueprint/*`.
  - Rationale: keep command ownership clear (`blueprint-*` configures blueprint/template assets, `infra-*` configures infra assets) and reduce namespace ambiguity for template consumers.

- Contract validator Python ownership moved from infra to blueprint namespace.
  - Moved `scripts/bin/infra/validate_contract.py` to `scripts/bin/blueprint/validate_contract.py` and updated callers.
  - Rationale: align Python script placement with domain ownership and mirror the shell namespace split.

- Conservative migration-compatibility test policy is the default cleanup strategy.
  - Kept explicit `blueprint-migrate` no-op/fail-fast smoke coverage at `v1.0.0` baseline and retained transition-registry hooks for future releases.
  - Rationale: preserve upgrade safety rails now, while avoiding fabricated pre-release transitions.

- Migration execution is now path-planned and transition-registered.
  - `scripts/lib/blueprint/migrate_repo.py` now resolves source template version, plans transitions from an explicit registry (`from_version -> to_version`), and fails fast on unsupported paths.
  - Rationale: prevent silent/best-effort mutation for unsupported upgrades and make future release migrations explicit and auditable.

- CI now enforces contract-critical matrix and explicit migration/consumer smoke lanes.
  - Added `contract-matrix` (`local-full`/`stackit-dev` x `OBSERVABILITY_ENABLED=false/true`), `consumer-golden-conformance` (`make blueprint-template-smoke`), and explicit `blueprint-migrate` E2E smoke execution in CI.
  - Rationale: catch profile/flag regressions and template-consumer onboarding/upgrade regressions before release.

- Tooling tests now share canonical helper utilities.
  - Added `tests/_shared/helpers.py` and refactored tooling suites to reuse common run/env/bootstrap/prune functions.
  - Rationale: reduce duplicate harness logic and keep test behavior changes localized.

- Tooling test namespace now mirrors blueprint domain ownership.
  - Replaced `tests/tooling/*` with namespaced test layout (`tests/blueprint`, `tests/infra`, `tests/docs`, `tests/e2e`, `tests/_shared`) and updated contract/bootstrap/module paths accordingly.
  - Rationale: align tests with repository namespaces, reduce ambiguity, and keep contract ownership explicit.

- Template version remains `1.0.0` until first public release.
  - Current repository hardening is folded into the initial GA baseline; migration registry is intentionally empty until a post-`1.0.0` template is published.
  - Rationale: avoid fictitious pre-release upgrade paths and keep contract/docs/tests aligned with actual release state.

- Tests namespace is an explicit Python package in baseline `1.0.0`.
  - Added `tests/**/__init__.py` package markers and contract `required_files` entries to keep `pytest` and `unittest` import behavior deterministic (`tests._shared.helpers`).
  - Rationale: prevent runner-dependent import failures in generated repositories without introducing migration-only coupling.

- Documentation ownership is split into blueprint vs platform spaces with different lifecycle policies.
  - `docs/blueprint/**` is strict template-synchronized, while `docs/platform/**` is seeded by `make blueprint-bootstrap` only when missing (`create_if_missing`) and then remains consumer-editable.
  - Rationale: enforce consistent blueprint governance docs while allowing generated repositories to evolve their platform/solution documentation after initialization.

- Docusaurus navigation follows the same split contract through sidebars (without overlapping docs plugins).
  - A single docs plugin serves `docs/` with explicit include patterns and dedicated sidebars for Blueprint/Platform/Reference, exposing platform docs under `/platform/**`.
  - Rationale: keep template-maintainer docs and generated-solution docs clearly separated in UX while avoiding double-MDX processing from overlapping plugin paths.

- Make and script ownership is now explicitly split between blueprint-managed and platform-owned surfaces.
  - `Makefile` is a loader, blueprint-managed targets live in rendered `make/blueprint.generated.mk`, and platform targets live in `make/platform.mk` (seeded create-if-missing, consumer-editable).
  - Platform execution scripts moved to `scripts/bin/platform/**` and shared platform libs to `scripts/lib/platform/**`; core blueprint wrappers remain in blueprint/infra/docs/quality namespaces.
  - Rationale: provide unambiguous modification boundaries for template consumers while keeping blueprint upgrade surfaces deterministic.

- Conservative pre-release cleanup favors stable docs/tests over compatibility scaffolding.
  - Simplified README/docs command inventories to canonical discovery entrypoints (`make help`, `make infra-help-reference`), updated upgrade wording to the explicit `1.0.0` no-transition baseline, hardened template-smoke excludes, and replaced hardcoded bootstrap template-count metric with dynamic counting.
  - Rationale: reduce maintenance drift and brittle assertions before first release while preserving contract-driven behavior.

- Repository identity init now supports dual-mode onboarding: interactive wizard and env-file automation.
  - Added `blueprint-init-repo-interactive` with validated prompts/default inference and dry-run support; kept `blueprint-init-repo` as canonical non-interactive path for CI/automation.
  - Updated contract/Make/docs/tests to include the interactive target while preserving env-file required inputs as the deterministic bootstrap contract.
  - Rationale: improve day-0 user experience without weakening scriptable, contract-driven initialization.

- Bootstrap template assets are now split into blueprint-owned vs infra-owned roots.
  - Moved blueprint seeds (`Makefile`, hygiene files, docs, `blueprint/repo.init.example.env`, `make/*`) to `scripts/templates/blueprint/bootstrap`.
  - Kept infra/dags/module-test scaffolding under `scripts/templates/infra/bootstrap` and updated template helper API to require explicit namespace (`blueprint` or `infra`).
  - Rationale: enforce clear ownership boundaries in template sources, mirroring runtime script namespaces and reducing mixed-scope drift.

- Documentation onboarding is now role-oriented with explicit consumer and maintainer tracks.
  - Reworked root/portal docs to answer what the blueprint is, how generation works, and what is editable vs blueprint-managed; added `platform/consumer/first_30_minutes.md` and `blueprint/governance/ownership_matrix.md`.
  - Updated bootstrap seed contract to include these docs in baseline materialization and keep blueprint docs strict-template synchronized.
  - Rationale: reduce first-day ambiguity for template consumers and make ownership boundaries discoverable early.

- Docs local-server target naming is now `docs-run` (no legacy alias).
  - Renamed `docs-dev` to `docs-run` in Make template/generated surface, contract required targets, docs script path (`scripts/bin/docs/run.sh`), and corresponding tests/docs metadata generation.
  - Rationale: use an imperative verb aligned with existing target naming style and avoid ambiguous environment label semantics.

- Local git-hook baseline now includes pre-push cached audits and shell/YAML hygiene checks.
  - Expanded `.pre-commit-config.yaml` (and its bootstrap template seed) with `check-yaml`, `check-added-large-files`, local `bash -n` syntax checks, and pre-push hooks for `infra-audit-version-cached` and `apps-audit-versions-cached`.
  - Updated `blueprint-bootstrap` to install both pre-commit and pre-push hook types in one deterministic step.
  - Rationale: shift common quality drift detection left (before push) while keeping push-time audits fast through cached targets.

- Wrapper instrumentation and command docs were normalized for pre-release consistency.
  - Replaced manual script-duration trap boilerplate with canonical `start_script_metric_trap` across core infra/apps/docs wrappers (including `infra-{validate,provision,deploy,smoke,provision-deploy}`, observability wrappers, `apps-{bootstrap,smoke}`, and `docs-{build,smoke}`).
  - Added `make docs-run` to docs command-reference pages (live docs + bootstrap template seed) and removed a duplicated final state log line in `infra-prereqs`.
  - Rationale: reduce wrapper drift, keep metrics instrumentation uniform, and make command discovery consistent before first release.

- Contract parsing is now schema-driven and shared across validator and docs generation.
  - Added `scripts/lib/blueprint/contract_schema.py` with typed loaders for blueprint/module contracts and replaced ad-hoc YAML extraction in `scripts/bin/blueprint/validate_contract.py` and `scripts/lib/docs/generate_contract_docs.py`.
  - Rationale: remove duplicate parsing logic, reduce drift risk, and enforce one contract-reading path.

- Generated-artifact lifecycle is now explicit and namespaced.
  - Added `make blueprint-clean-generated` (`scripts/bin/blueprint/clean_generated.sh`) for deterministic cleanup of generated artifacts/caches.
  - Split state artifacts by domain via `set_state_namespace` (`artifacts/infra`, `artifacts/apps`, `artifacts/docs`) and updated wrappers/tests accordingly.
  - Rationale: make cleanup predictable and prevent cross-domain state collisions.

- Optional-module wrapper skeletons are generated from module contracts.
  - Added `make blueprint-render-module-wrapper-skeletons` and generator tooling to materialize `scripts/templates/infra/module_wrappers/<module>/*.sh.tmpl` from `blueprint/modules/*.yaml`.
  - Wired rendering into `blueprint-bootstrap` and added contract validation for expected skeleton coverage.
  - Rationale: reduce manual template duplication and keep optional-module wrappers aligned with contract metadata.

- CI now runs pre-push hook gates in addition to pre-commit.
  - Added explicit `pre-commit run --hook-stage pre-push --all-files` lane in `.github/workflows/ci.yml`.
  - Rationale: enforce push-time policy checks in CI, matching local hook behavior.

- STACKIT backend now follows a strict remote-first contract from first execution.
  - `bootstrap` and `foundation` both run with remote S3 backend (`backend "s3"` + per-layer backend files); bootstrap no longer provisions tfstate bucket/credentials and no wrapper auto-loads credentials from terraform outputs.
  - Execution mode now requires explicit `STACKIT_TFSTATE_ACCESS_KEY_ID` and `STACKIT_TFSTATE_SECRET_ACCESS_KEY`; docs/tests/template assets were aligned accordingly.
  - Rationale: enforce Terraform state best practices from day one, remove hidden credential coupling, and keep teardown/provision semantics explicit.

- ArgoCD topology now deploys real platform resources, not only configuration placeholders.
  - Added `infra/gitops/platform/**` kustomize tree and wired ArgoCD `Application` resources for stackit env roots plus local overlay parity (`platform-local-core`).
  - Rationale: make runtime delivery path execution-ready with concrete sync targets for local and STACKIT profiles.

- STACKIT deploy now seeds a runtime foundation contract secret before app sync.
  - Added `infra-stackit-foundation-seed-runtime-secret` (auto-invoked by `infra-deploy` on stackit profiles) to materialize `platform-foundation-contract` from Terraform outputs and metadata.
  - Rationale: close the handoff gap between foundation provisioning outputs and runtime workloads expecting deterministic in-cluster credentials/config contract.

- Removed remaining backward-compatibility shim from infra stack path routing.
  - Dropped `stackit_terraform_env_dir`/`profile_env` helper indirections and moved `infra-doctor` to canonical layered path resolution (`stackit_terraform_layer_dir foundation`).
  - Rationale: enforce no-alias/no-shim governance and keep all STACKIT path contracts explicit to layered bootstrap/foundation model.
