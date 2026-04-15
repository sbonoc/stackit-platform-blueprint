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
2. During `Discover`, `High-Level Architecture`, `Specify`, and `Plan`, do not use assumptions as substitutes for missing requirements; resolve ambiguity explicitly or mark the work item blocked.
3. For non-trivial changes, execute the Spec-Driven Development lifecycle in this order: `Discover -> High-Level Architecture -> Specify -> Plan -> Implement -> Verify -> Document -> Operate -> Publish`.
4. Implement with strict boundary contracts and deterministic behavior.
5. Update/add automated tests for every behavior change.
6. Refactor touched scope immediately (code/tests/docs/scripts/contracts).
7. Run required validation bundles for changed scope before finishing.
8. Update `AGENTS.decisions.md` when scope/contracts/priorities change.
9. Update `AGENTS.backlog.md` when status/priorities change.
10. Do not run `git commit`/`git push` unless explicitly requested in the current conversation.

## Spec-Driven Development (SDD) Lifecycle
- Canonical phase order:
  - `Discover`: define user/problem context, scope boundaries, assumptions, constraints, and cross-cutting non-functional requirements.
  - `High-Level Architecture`: decide bounded contexts, module boundaries, integration edges, and technology-specific architecture shape before low-level specs.
  - `Specify`: define behavioral contracts, acceptance criteria, data/API/event contracts, and guardrail constraints.
  - `Plan`: define executable work slices, sequence, ownership, risks, and validation strategy.
  - `Implement`: deliver code/scripts/docs/contracts according to the approved plan.
  - `Verify`: run shift-left validation at the lowest valid test layer first, then boundary/integration/e2e checks as required.
  - `Document`: update and synchronize blueprint and consumer docs (Docusaurus + Mermaid) to reflect the implemented and verified behavior.
  - `Operate`: define operational readiness (runbooks, dashboards/alerts, diagnostics, rollback guidance).
  - `Publish`: package reviewer-ready PR context with key files, requirement/contract coverage, validation evidence, risk/rollback notes, and deferred proposals.
- Trivial typo-only or wording-only updates may use a lightweight subset, but any behavioral, architectural, or contract change must follow the full lifecycle.

## Generated SDD Policy Snapshot
<!-- BEGIN GENERATED:SDD_POLICY_SNAPSHOT -->
- Lifecycle order (contract): Discover -> High-Level Architecture -> Specify -> Plan -> Implement -> Verify -> Document -> Operate -> Publish
- Readiness gate: `SPEC_READY=true`
- Missing-input blocker token: `BLOCKED_MISSING_INPUTS`
- Required zero-count fields: `Open questions count`, `Unresolved alternatives count`, `Unresolved TODO markers count`, `Pending assumptions count`, `Open clarification markers count`
- Required sign-offs: `Product`, `Architecture`, `Security`, `Operations`
- Allowed normative keywords: `MUST`, `MUST NOT`, `SHALL`, `EXACTLY ONE OF`
- Forbidden ambiguous terms: `should`, `may`, `could`, `might`, `either`, `and/or`, `as needed`, `approximately`, `etc.`
<!-- END GENERATED:SDD_POLICY_SNAPSHOT -->

## SDD Readiness Gate (Mandatory Before Implementation)
- `Implement` may start only when `SPEC_READY=true` is explicitly recorded in the work-item spec.
- A work item is implementation-ready only when all are true:
  - Open questions count is `0`.
  - Unresolved alternatives count is `0`.
  - Unresolved TODO/TBD/TBC markers count is `0`.
  - Pending assumptions count is `0`.
  - Required sign-offs are recorded as approved (`Product`, `Architecture`, `Security`, `Operations`).
  - `ADR path` points to an existing ADR file and `ADR status` is approved.
  - Requirement IDs and acceptance criteria IDs are mapped in traceability artifacts.
- If required inputs are missing, the work item must be marked with `BLOCKED_MISSING_INPUTS` and remain `SPEC_READY=false`.
- Code assistants must not silently fill missing business or non-functional requirements in spec artifacts.

## SDD Artifact Contract
- Canonical work-item location: `specs/<YYYY-MM-DD>-<work-item-slug>/`.
- Required work-item documents:
  - `architecture.md`
  - `spec.md`
  - `plan.md`
  - `tasks.md`
  - `traceability.md`
  - `graph.yaml`
  - `evidence_manifest.json`
  - `context_pack.md`
  - `pr_context.md`
  - `hardening_review.md`
- Optional (complex work): `research.md`, `data-model.md`, `contracts/`, `quickstart.md`.
- Canonical template packs:
  - blueprint maintainer track: `.spec-kit/templates/blueprint/`
  - generated-consumer track: `.spec-kit/templates/consumer/`
- `.spec-kit/policy-mapping.md` defines how governance guardrails map into SDD artifacts and must stay aligned with this file and `blueprint/contract.yaml`.
- `.spec-kit/control-catalog.yaml` is the machine-readable control source; `.spec-kit/control-catalog.md` is generated from it.
- `architecture.md` is the high-level exploration workspace for each work item.
- Finalized architecture outcomes are recorded as ADRs:
  - blueprint track: `docs/blueprint/architecture/decisions/`
  - generated-consumer track: `docs/platform/architecture/decisions/`
- North-star reference docs for architecture/stack baselines:
  - blueprint track: `docs/blueprint/architecture/north_star.md`, `docs/blueprint/architecture/tech_stack.md`
  - generated-consumer track: `docs/platform/architecture/north_star.md`, `docs/platform/architecture/tech_stack.md`

## Guardrail Control Statements (Mandatory)
- Guardrails must be written and maintained as control statements with stable IDs (`SDD-C-###`) in `.spec-kit/control-catalog.yaml` and rendered to `.spec-kit/control-catalog.md`.
- Every control statement must include:
  - deterministic normative requirement text (`MUST`/`MUST NOT`/`SHALL`)
  - phase scope
  - validation command
  - expected evidence artifact(s)
  - owner
  - gate severity (`fail` or `warn`)
- Work-item `spec.md` files must declare applicable control IDs in the normative controls section.

## Cross-Cutting Guardrails (Must Be Captured in Discover + Specify)
- Security and privacy controls (authn/authz, secret handling, least privilege, data protection).
- Observability baseline (structured logs, metrics, traces, audit fields where applicable).
- Monitoring and alerting expectations (signals, thresholds/SLO alignment, ownership).
- Reliability/resilience and rollback policy (failure modes, blast radius, recovery strategy).
- Operability and diagnostics (runbooks, troubleshooting artifacts, deterministic commands).
- Compliance with architecture style mandates (SOLID, Clean Architecture, Clean Code, DDD) adapted to the selected runtime stack.
- Local-first baseline for local execution (Docker Desktop Kubernetes context policy + Crossplane/Helm provisioning + ESO/Argo/Keycloak runtime identity) with explicit approved exception rationale when deviating.
- App-onboarding minimum Make-target contract (including canonical `infra-port-forward-start|stop|cleanup` wrappers) in `plan.md` and `tasks.md` when app delivery scope is affected.
- Managed-service-first policy for generated-consumer runtime capabilities: when `BLUEPRINT_PROFILE=stackit-*`, prefer STACKIT managed services by default; any non-managed/self-managed alternative requires an explicit normative option decision, rationale, and approval record in `spec.md` + ADR + `AGENTS.decisions.md`.
- Blueprint-defect escalation policy for generated-consumer work: when a defect is attributable to blueprint-managed behavior, record an upstream issue plus workaround lifecycle fields (`Upstream issue URL`, `Temporary workaround path`, `Replacement trigger`, `Workaround review date`) in the work-item spec and consumer docs until replaced by upstream fix.

## Normative Language Policy (Spec Artifacts)
- Normative sections must use deterministic language: `MUST`, `MUST NOT`, `SHALL`, `EXACTLY ONE OF`.
- In normative sections, ambiguous wording is forbidden, including:
  - `should`
  - `may`
  - `could`
  - `might`
  - `either`
  - `and/or`
  - `as needed`
  - `approximately`
  - `etc.`
- Informative sections may explain context and tradeoffs, but implementation behavior is defined only by normative statements and selected options.

## Clarification Marker Policy
- Use `[NEEDS CLARIFICATION: ...]` markers during `Discover`, `High-Level Architecture`, `Specify`, and `Plan` whenever requirements are not explicit.
- Do not replace missing inputs with assumptions; unresolved clarification markers keep `SPEC_READY=false`.
- `Open clarification markers count` in the readiness gate must be `0` before implementation starts.

## Hardening Review Gate
- After implementation and before publish, run a repository-wide hardening review and capture results in `hardening_review.md`.
- Hardening review must include:
  - `Repository-Wide Findings Fixed`
  - `Observability and Diagnostics Changes`
  - `Architecture and Code Quality Compliance`
  - `Proposals Only (Not Implemented)`
- Canonical execution target: `make quality-hardening-review`.

## Publish Gate
- `Publish` is required before requesting review/merge.
- Generate and maintain `pr_context.md` containing:
  - `Summary`
  - `Requirement Coverage`
  - `Key Reviewer Files`
  - `Validation Evidence`
  - `Risk and Rollback`
  - `Deferred Proposals`
- Pull requests must follow repository templates and include equivalent sections for deterministic review context.

## Specialized Agent Collaboration (When Used)
- Partition ownership by bounded context and dependency direction, not by arbitrary files.
- Backend/API contributors (for example FastAPI stacks) should preserve `domain -> application -> infrastructure -> presentation` flow and explicit contract boundaries.
- Frontend contributors (for example Vue stacks) should preserve feature boundaries, typed API contracts, state/event flow clarity, and testability.
- Always preserve deterministic handoffs: each task must map to SDD artifacts, validation evidence, and a clear owner.

## Assistant Interoperability
- SDD artifacts (`specs/**`, `.spec-kit/**`) and Make targets are the canonical, tool-agnostic execution contract for any code assistant.
- Bundled Codex skills under `.agents/skills/**` are accelerators, not alternative governance; they must resolve to the same lifecycle/order/validation contract.
- For assistants that do not support Codex skill loading (for example Claude Code), use the corresponding `SKILL.md` files as plain-text runbooks and still execute canonical repository commands.
- When specialized subagents are used, assign each one to an isolated worktree and bounded-context ownership slice to prevent write collisions.
- The work-item spec must explicitly declare the selected stack profile and agent execution model before implementation.

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
  - blueprint-managed shell entrypoints and rendered shell templates must source bootstrap via `SCRIPT_DIR`-relative paths only.
  - repository root resolution must remain centralized in `scripts/lib/shell/root_dir.sh`; do not add inline per-script `ROOT_DIR` resolver blocks.
  - any bootstrap prelude change must update templates and root-resolution drift checks/tests in the same change.
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
