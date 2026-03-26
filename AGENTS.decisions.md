# Decisions Log

## 2026-03-26 (Template Baseline)
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
