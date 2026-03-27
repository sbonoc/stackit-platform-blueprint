# Blueprint Backlog

## Baseline Status
- [x] Contract-first validation flow (`infra-validate`) is aligned with `blueprint/contract.yaml`.
- [x] Canonical execution targets exist for quality, infra, apps, tests, and docs.
- [x] Optional modules are lean-by-default and scaffold on enable.
- [x] Data Marketplace P0 optional modules are contract-driven and conditional (`object-storage`, `rabbitmq`, `dns`, `public-endpoints`, `secrets-manager`, `kms`, `identity-aware-proxy`).
- [x] Identity-Aware Proxy contract enforces Keycloak OIDC dependency (Keycloak remains core capability).
- [x] `infra-bootstrap` prunes stale optional-module scaffolding when module flags are disabled.
- [x] Bootstrap ownership is split by domain: `blueprint-*` for template/config assets, `infra-*` for infra scaffolding.
- [x] Root infra scaffold is lean and free of placeholder-only manifests.
- [x] Optional-module destroy targets execute profile-specific cleanup (not artifact-only teardown).
- [x] Dry-run/live execution toggle is standardized as `DRY_RUN` (safe-by-default).
- [x] Reused STACKIT operator targets for prereqs/help/CI setup/cached audits/runtime inventory redaction.
- [x] STACKIT execution path is layered and backend-aware (`bootstrap` + `foundation` Terraform roots with env tfvars/backend hcl and wrapper wiring).
- [x] STACKIT init contract now seeds project-specific tfvars/backend identity (region/tenant/platform/project/tfstate) and placeholder checks enforce resolution.
- [x] ArgoCD STACKIT app-of-apps topology baseline exists (`root`, environment roots, and per-environment overlays with AppProject/ApplicationSet).
- [x] Runtime core bootstrap is execution-ready: ArgoCD + External Secrets are installed in deploy flow, and local provisioning installs Crossplane baseline.
- [x] STACKIT Terraform backend contract is strict from first run: bootstrap and foundation both use remote S3 backend files, and tfstate credentials are explicit required inputs.
- [x] ArgoCD runtime topology deploys concrete platform resources via `infra/gitops/platform/**` applications for stackit and local profiles.
- [x] STACKIT deploy seeds runtime foundation contract secret (`platform-foundation-contract`) from Terraform outputs before app sync.
- [x] Optional-module wrapper skeleton templates are explicit fail-fast stubs (`status=not_implemented`, stable exit code) instead of TODO placeholders.
- [x] Disabled optional-module teardown has a dedicated contract-driven orchestration target (`infra-destroy-disabled-modules`) for destroy-before-prune workflows.
- [x] Local git hooks include YAML/large-file/shell syntax pre-commit checks and cached version audits on pre-push.
- [x] CI executes both pre-commit and pre-push hook stages (`pre-commit run --hook-stage pre-push --all-files`).
- [x] Core wrappers use canonical `start_script_metric_trap` instrumentation and docs command reference includes `docs-run`.
- [x] Blueprint contract parsing is centralized in a schema-driven shared loader used by validator and docs generator.
- [x] Generated state artifacts are namespaced by domain (`artifacts/infra`, `artifacts/apps`, `artifacts/docs`).
- [x] Generated optional-module wrapper templates are contract-driven (`make blueprint-render-module-wrapper-skeletons`).
- [x] Deterministic generated-artifact cleanup is available via `make blueprint-clean-generated`.
- [x] GitHub-template onboarding flow exists (`make blueprint-init-repo` + example input file).
- [x] Core docs and namespaced tooling tests are synchronized with template usage.
- [x] Docs are split by ownership and lifecycle: `docs/blueprint` (strict template sync) and `docs/platform` (bootstrap seed `create_if_missing`, then consumer-editable).
- [x] Make/script ownership boundaries are explicit: blueprint-managed generated surfaces vs platform-owned editable surfaces (`make/platform.mk`, `scripts/bin/platform`, `scripts/lib/platform`).
- [x] STACKIT operator lifecycle/diagnostic and GHCR publish targets are contract-driven and template-generated.
- [x] Migration framework is transition-registered and fails fast on unsupported upgrade paths.
- [x] CI includes migration smoke, contract-critical profile/observability matrix, and golden template-consumer conformance lanes.
- [x] Tooling tests share canonical helper utilities for run/env/bootstrap/prune flows.
- [x] Test suite layout follows blueprint namespaces (`tests/blueprint`, `tests/infra`, `tests/docs`, `tests/e2e`, `tests/_shared`).
- [x] Test namespace package markers keep `pytest` and `unittest` imports consistent (`tests/**/__init__.py`).
- [x] Template scaffold roots are split by ownership: `scripts/templates/blueprint/bootstrap` (blueprint docs/make/hygiene seeds) vs `scripts/templates/infra/bootstrap` (infra/dags/tests scaffolding).
- [x] Documentation IA is role-oriented with explicit consumer/maintainer tracks and first-day onboarding (`docs/platform/consumer/first_30_minutes.md`, ownership matrix).
- [x] Blueprint-managed second-wave Make/script hardening is in place: docs drift gates, generated core-targets/contract metadata sync, test-pyramid enforcement, namespaced shell/quality helpers, and machine-readable infra smoke/status diagnostics.
- [x] Optional-module wrappers resolve provider-backed/fallback/external execution modes through a shared infra library, keeping driver selection consistent across scripts.

## Top Priority - Execution-Ready E2E (Current)
- [x] Fix GitHub-template onboarding smoke drift by excluding init-mutated ArgoCD identity files from strict byte-sync validation while keeping identity checks enforced (`blueprint-template-smoke` green).
- [x] Remove false-positive STACKIT optional-module Terraform execution on placeholder module roots; provider-backed modules now reconcile through `foundation` layer contract.
- [x] Make STACKIT fallback modules explicit and executable:
  - `workflows`: API contract path (no placeholder Terraform dependency).
  - `langfuse`, `neo4j`, `public-endpoints`, `identity-aware-proxy`: fallback runtime/API reconciliation.
  - `rabbitmq`, `kms`: STACKIT foundation provider-backed reconciliation.
- [x] Extend optional manifest materialization/prune contracts for `rabbitmq`, `public-endpoints`, and `identity-aware-proxy`.
- [x] Synchronize docs/tests/contracts to the new execution model and keep full validation bundles green.
- [x] Fold live `/tmp` validation findings back into the blueprint:
  - STACKIT consumer repos must run `make blueprint-init-repo` before first remote bootstrap so backend/tfvars placeholders are initialized.
  - DNS zones keep trailing dots in consumer input contracts but are trimmed at the provider boundary.
  - PostgreSQL provider-backed defaults stay aligned at version `16` across wrappers and foundation.
  - STACKIT runtime deploy now waits explicitly for kube API hostname resolution and API readiness before the first `kubectl` operation, with troubleshooting updated for operator-side DNS blockers.

## Release Plan
- Current state: pre-release baseline `template_version: 1.0.0` (no published upgrade transitions yet).
- Milestones P1/P2 represent post-GA roadmap slices; they do not imply already published template versions.

## P0 - v1.0 Template GA
- [x] Define template release workflow (tagging, release notes, support policy).
- [x] Add CI smoke that validates fresh-template onboarding (`make blueprint-init-repo`, `make infra-bootstrap`, `make infra-validate`).
- [x] Add placeholder-token guard in CI for generated repos.
- [x] Publish consumer quickstart + troubleshooting doc focused on first-day onboarding failures.
- [x] Define version compatibility contract for generated repos (`template_version`, minimum supported upgrade path).

## P1 - v1.1 Upgradeability
- [x] Add migration command for repos generated from older template versions.
- [x] Add upgrade runbook with before/after validation bundles.
- [x] Add golden conformance tests for migration no-op behavior and fail-fast unsupported upgrade paths.
- [x] Add blueprint-managed quality/docs drift guardrails and deterministic smoke/status artifacts without expanding platform-owned surfaces.
- [x] Add golden conformance matrix across profile/module combinations for newly generated repos.
- [x] Expand Terraform provider-backed coverage for optional modules as official STACKIT provider resources mature; `rabbitmq` and `kms` now reconcile through foundation, while `workflows`, `langfuse`, `neo4j`, `public-endpoints`, and `identity-aware-proxy` remain fallback/API contracts until provider support exists.
- [x] Refactor optional-module wrappers onto a shared execution-mode library (provider-backed/fallback/external) to remove duplicated branch logic across scripts.
- [x] Replace generic optional ConfigMap manifests with module-specific ArgoCD applications/charts for fallback modules (`rabbitmq`, `public-endpoints`, `identity-aware-proxy`) to reach production-grade runtime delivery.

## P2 - v1.2 Scale
- [x] Add optional interactive init UX (prompt mode), keeping env-file mode canonical.
- [ ] Add opinionated governance starter assets for generated repos (issue templates, PR template, CODEOWNERS).
- [ ] Continue migrating remaining fallback/API optional modules (`workflows`, `langfuse`, `neo4j`, `public-endpoints`, `identity-aware-proxy`) to provider-backed STACKIT execution when official resources become available.
- [x] Normalize module input contracts so STACKIT foundation Terraform variables are sourced from canonical module env inputs (remove duplicated naming defaults across wrappers/foundation).
