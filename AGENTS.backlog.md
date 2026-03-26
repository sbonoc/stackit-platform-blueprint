# Blueprint Backlog

## Baseline Status
- [x] Contract-first validation flow (`infra-validate`) is aligned with `blueprint/contract.yaml`.
- [x] Canonical execution targets exist for quality, infra, apps, tests, and docs.
- [x] Optional modules are lean-by-default and scaffold on enable.
- [x] `infra-bootstrap` prunes stale optional-module scaffolding when module flags are disabled.
- [x] Bootstrap ownership is split by domain: `blueprint-*` for template/config assets, `infra-*` for infra scaffolding.
- [x] Root infra scaffold is lean and free of placeholder-only manifests.
- [x] Optional-module destroy targets execute profile-specific cleanup (not artifact-only teardown).
- [x] Dry-run/live execution toggle is standardized as `DRY_RUN` (safe-by-default).
- [x] Reused STACKIT operator targets for prereqs/help/CI setup/cached audits/runtime inventory redaction.
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
- [ ] Add golden conformance matrix across profile/module combinations for newly generated repos.

## P2 - v1.2 Scale
- [x] Add optional interactive init UX (prompt mode), keeping env-file mode canonical.
- [ ] Add opinionated governance starter assets for generated repos (issue templates, PR template, CODEOWNERS).
