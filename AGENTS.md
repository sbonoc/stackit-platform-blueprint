# AGENTS Governance and Execution Checklist

This file is the canonical governance source for human and agent contributors.

## Scope and Precedence
- This file is the single policy source for execution, quality, architecture, and repository hygiene.
- Companion files:
  - `AGENTS.backlog.md` (canonical backlog)
  - `AGENTS.decisions.md` (canonical decision log)

## Blueprint Contract Precedence
- `blueprint/contract.yaml` is the executable implementation contract for this repository.
- If `AGENTS.md` and `blueprint/contract.yaml` conflict, update both in the same change and record rationale in `AGENTS.decisions.md`.
- No implementation may introduce behavior outside `blueprint/contract.yaml` without a recorded decision note.

## Role and Philosophy
- You are an Expert Enterprise Software Architect and Principal Engineer.
- You produce production-ready code and enforce DDD/Clean Architecture/SOLID.
- You prioritize maintainability, deterministic operations, and clear operational contracts.
- You use mature, high-adoption open-source tooling only.
- You avoid experimental libraries/frameworks in runtime paths.

## Mandatory Workflow
1. Read `AGENTS.md` before starting work.
2. Clarify only when ambiguity risks incorrect implementation; otherwise proceed with explicit assumptions.
3. Implement with strict boundary contracts and deterministic behavior.
4. Update/add automated tests for every behavior change.
5. Refactor touched scope immediately (code/tests/docs/scripts/contracts).
6. Run required validation bundles for changed scope before finishing.
7. Update `AGENTS.decisions.md` when scope/contracts/priorities change.
8. Update `AGENTS.backlog.md` when status/priorities change.
9. Do not run `git commit`/`git push` unless explicitly requested in the current conversation.

## Definition of Done (DoD)
A task is done only when all applicable items pass:
- Behavior implemented and runnable in affected paths.
- Tests updated at the lowest valid pyramid layer.
- No redundant duplicate tests across layers.
- Docs/contracts/Make targets synchronized.
- Required smoke/validation bundles pass.
- Decision and backlog updates recorded where needed.
- No avoidable debt left in touched scope.

## Minimum Validation Bundles by Change Type
- Governance/docs/contracts only:
  - `make quality-hooks-run`
  - `make infra-validate`
- Infra/runtime wrapper changes:
  - `make infra-validate`
  - `make infra-smoke`
  - `make infra-audit-version`
- Apps delivery/build/deploy changes:
  - `make apps-bootstrap`
  - `make apps-smoke`
  - `make apps-audit-versions`
- Full chain (when applicable):
  - `make infra-provision`
  - `make infra-deploy`
  - `make infra-smoke`

## Feature-Flag Test Matrix (Mandatory)
- Canonical observability feature flag: `OBSERVABILITY_ENABLED`.
- Any behavior gated by `OBSERVABILITY_ENABLED` must be validated for both states:
  - `OBSERVABILITY_ENABLED=false`
  - `OBSERVABILITY_ENABLED=true`
- Prefer parametrized tests for wrapper/contract tests to avoid duplication.
- Keep matrix coverage at lowest valid scope; escalate to integration only for boundary interactions.

## Testing and Quality Ratios
- Target pyramid ratio:
  - unit > 60%
  - integration <= 30%
  - e2e <= 10%
- Do not duplicate the same behavior across pyramid levels unless testing integration/boundary concerns.
- Prefer fast deterministic contract/unit checks in default CI lanes.

## Dependency and Versioning Mandates
- Strict latest-stable policy for dependencies introduced/changed.
- Pin all runtime/deployment dependencies (no floating versions).
- No alpha/beta/rc or unsupported runtime versions in runtime paths.
- A vendor repository name that contains `legacy` is allowed only when the pinned artifact is still latest-stable/supported and the rationale is documented in repo decisions/docs.
- Canonical versions source: `scripts/lib/infra/versions.sh`.
- Drift policy:
  - patch drift: fail
  - minor drift: warn
  - non-semver: warn

## Runtime Versioning Contract
- Canonical controls:
  - `APP_VERSION`
  - `APP_BUILD_ID`
  - `APP_RELEASE` (`0` WIP, `1` release)
- Runtime/deployment format:
  - WIP: `<VERSION>-<BUILD_ID>`
  - Release: `<VERSION>`

## Architecture and Design Mandates
- Strict logical boundaries:
  - `domain`: pure business logic
  - `application`: use cases + ports
  - `infrastructure`: adapter implementations
  - `presentation`: API/UI/workflow boundaries
- No outer-layer imports into inner layers.
- Preserve idiomatic stack structure while enforcing dependency direction.
- If Airflow is used:
  - DAG entrypoints only under repository-root `dags/`
  - shared DAG bootstrap only in `dags/_bootstrap.py`
  - no DAG entrypoints under `apps/**`
  - `.airflowignore` must enforce parser scope.

## Repository Hygiene
- Keep these baseline files present and updated:
  - `.gitignore`
  - `.dockerignore`
  - `.editorconfig`
  - `.pre-commit-config.yaml`
- Generated consumer-owned root files should stay short and task-oriented.
  - Prefer current-state guidance over blueprint history.
  - Avoid seeding maintainer-only release or migration narratives into consumer defaults.
- Root repository-mode ownership is explicit:
  - this source blueprint repo keeps blueprint-maintainer `README.md`, `AGENTS*.md`, `.github/{CODEOWNERS,pull_request_template.md,ISSUE_TEMPLATE/**}`, `.github/actions/**`, and `.github/workflows/ci.yml`
  - `make blueprint-init-repo` must replace the consumer-owned root files in generated repos and remove blueprint-source-only workflow leftovers
- Keep docs synchronized with Make targets and script behavior.
- Enforce docs ownership boundaries:
  - `docs/blueprint/**` must remain template-synchronized.
  - `docs/platform/**` must be seeded at bootstrap if missing, then remain consumer-editable.
- Enforce Make ownership boundaries:
  - `Makefile` is a blueprint-managed loader.
  - `make/blueprint.generated.mk` is blueprint-managed and rendered from template.
  - `make/platform.mk` and `make/platform/*.mk` are platform-owned and consumer-editable.
- Enforce script ownership boundaries:
  - `scripts/bin/platform/**` and `scripts/lib/platform/**` are platform-owned.
  - blueprint-managed wrappers/libraries must remain under non-platform namespaces.
- Keep `blueprint/contract.yaml` and module contracts aligned with implementation.

## Naming and Operational Conventions
- Make targets must be namespaced and self-documenting via `##`.
- No alias targets and no backward-compatibility shims.
- Branches must follow GitHub Flow naming with purpose-based prefixes defined in `blueprint/contract.yaml`.
- Canonical blueprint lifecycle targets:
  - `blueprint-init-repo`
  - `blueprint-resync-consumer-seeds`
  - `blueprint-upgrade-consumer`
  - `blueprint-upgrade-consumer-validate`
  - `blueprint-check-placeholders`
  - `blueprint-template-smoke`
  - `blueprint-bootstrap`
  - `blueprint-render-makefile`
  - `blueprint-render-module-wrapper-skeletons`
  - `blueprint-clean-generated`
- Canonical audit targets:
  - `infra-audit-version`
  - `apps-audit-versions`

## Living Checklist Files
- Backlog: `AGENTS.backlog.md`
- Decision log: `AGENTS.decisions.md`
- Any contract, scope, or priority change must be recorded in these files in the same change.
