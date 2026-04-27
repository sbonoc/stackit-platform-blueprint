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

## Platform Context
This section provides context for code assistants to understand the blueprint before starting work.

**Purpose:** `stackit-platform-blueprint` is the upstream platform blueprint. It defines governance, tooling, skill catalog, spec-kit templates, and contract validation for all generated consumers.

**Blueprint-managed paths (source of truth here, propagated to consumers on upgrade):**
- `scripts/templates/consumer/init/` — consumer bootstrap templates (new consumers)
- `scripts/templates/blueprint/bootstrap/` — consumer in-repo managed-file templates (drift-checked on upgrade)
- `.agents/skills/` — canonical skill runbooks (`SKILL.md`) and agent wiring (`openai.yaml`, `claude.yaml`)
- `scripts/bin/blueprint/` — validation, bootstrap, and upgrade tooling
- `docs/blueprint/` — blueprint reference documentation

**Key tooling:**
- `scripts/bin/blueprint/validate_contract.py` — contract validation (branch naming, template drift, make targets, shell scripts); `--branch-only` for fast pre-push checks
- `scripts/bin/blueprint/bootstrap_repo.sh` — new consumer initialization
- `.spec-kit/` — SDD template packs and control catalog

**Key make targets:**
- `make infra-validate` — run full contract validation
- `make quality-hooks-fast` — fast pre-commit hook suite

## Mandatory Workflow
1. Read `AGENTS.md` before starting work.
2. During `Discover`, `High-Level Architecture`, `Specify`, and `Plan`, do not use assumptions as substitutes for missing requirements; resolve ambiguity explicitly or mark the work item blocked.
3. Spec-Driven Development is mandatory by default for assistant-executed work; bypass only when the user explicitly says not to follow SDD for the requested task.
4. Start each new SDD work item with `make spec-scaffold ...`, which creates a dedicated non-default branch by default (`codex/<YYYY-MM-DD>-<slug>` unless overridden).
5. Execute the Spec-Driven Development lifecycle in this order: `Discover -> High-Level Architecture -> Specify -> Plan -> Implement -> Verify -> Document -> Operate -> Publish`.
6. Implement with strict boundary contracts and deterministic behavior.
7. Update/add automated tests for every behavior change.
8. Refactor touched scope immediately (code/tests/docs/scripts/contracts).
9. Run required validation bundles for changed scope before finishing.
10. Update `AGENTS.decisions.md` when scope/contracts/priorities change.
11. Update `AGENTS.backlog.md` when status/priorities change.
12. Do not run `git commit`/`git push` unless explicitly requested in the current conversation.

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
- Lightweight subsets are allowed only with explicit user opt-out in the current task context; otherwise the full lifecycle is required.

## Generated SDD Policy Snapshot
<!-- BEGIN GENERATED:SDD_POLICY_SNAPSHOT -->
- Lifecycle order (contract): Discover -> High-Level Architecture -> Specify -> Plan -> Implement -> Verify -> Document -> Operate -> Publish
- Readiness gate: `SPEC_READY=true`
- Intake gate: `SPEC_PRODUCT_READY=true`
- Missing-input blocker token: `BLOCKED_MISSING_INPUTS`
- Required zero-count fields: `Open questions count`, `Unresolved alternatives count`, `Unresolved TODO markers count`, `Pending assumptions count`, `Open clarification markers count`
- Required sign-offs: `Product`, `Architecture`, `Security`, `Operations`
- Intake required sign-offs: `Product`
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

## Sign-off Policy
- Sign-offs (`Product`, `Architecture`, `Security`, `Operations`) are granted explicitly
  by the user or designated reviewers via conversation or pull request review.
- Code assistants MUST NOT self-approve or assume any sign-off is granted.
- Keep `SPEC_READY=false` until each required sign-off is explicitly stated.
- In single-author mode the user holds all sign-off roles. In multi-author mode,
  each sign-off should be traceable to the reviewer's git identity.

### Sign-off Phrases (Deterministic)

Each role grants its sign-off by leaving a PR comment containing the **exact** phrase below.
No other format is recognised — plain-language approval is not sufficient.

| Role | Exact PR comment phrase | Records in `spec.md` |
|---|---|---|
| Product | `SPEC_PRODUCT_READY: approved` | `SPEC_PRODUCT_READY: true` + `Product sign-off: approved` |
| Architecture | `ARCHITECTURE_SIGNOFF: approved` | `Architecture sign-off: approved` |
| Security | `SECURITY_SIGNOFF: approved` | `Security sign-off: approved` |
| Operations | `OPERATIONS_SIGNOFF: approved` | `Operations sign-off: approved` |

All four approvals → agent sets `SPEC_READY: true` and ADR `Status: approved`.

## SDD Artifact Contract
- Canonical work-item location: `specs/<YYYY-MM-DD>-<work-item-slug>/`.
- Canonical start command: `make spec-scaffold SPEC_SLUG=<work-item-slug>` (auto-creates and checks out a dedicated branch by default; explicit opt-out requires `SPEC_NO_BRANCH=true`).
- Required work-item documents:
  - `architecture.md`
  - `spec.md`
  - `plan.md`
  - `tasks.md`
  - `traceability.md`
  - `graph.json`
  - `evidence_manifest.json`
  - `context_pack.md`
  - `pr_context.md`
  - `hardening_review.md`
- Optional (complex work): `research.md`, `data-model.md`, `contracts/`, `quickstart.md`.
- Canonical template packs:
  - blueprint maintainer track: `.spec-kit/templates/blueprint/`
  - generated-consumer track: `.spec-kit/templates/consumer/`
- `.spec-kit/policy-mapping.md` defines how governance guardrails map into SDD artifacts and must stay aligned with this file and `blueprint/contract.yaml`.
- `.spec-kit/control-catalog.json` is the machine-readable control source; `.spec-kit/control-catalog.md` is generated from it.
- `architecture.md` is the high-level exploration workspace for each work item.
- Finalized architecture outcomes are recorded as ADRs:
  - blueprint track: `docs/blueprint/architecture/decisions/`
  - generated-consumer track: `docs/platform/architecture/decisions/`
- North-star reference docs for architecture/stack baselines:
  - blueprint track: `docs/blueprint/architecture/north_star.md`, `docs/blueprint/architecture/tech_stack.md`
  - generated-consumer track: `docs/platform/architecture/north_star.md`, `docs/platform/architecture/tech_stack.md`

## Guardrail Control Statements (Mandatory)
- Guardrails must be written and maintained as control statements with stable IDs (`SDD-C-###`) in `.spec-kit/control-catalog.json` and rendered to `.spec-kit/control-catalog.md`.
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
- API and event contract first: OpenAPI specs and Pact consumer contracts that define new
  or changed service interfaces MUST be drafted in the Specify phase before implementation
  code is written. Record the contract file path in `spec.md` under Contract Impacts.
- Positive-path filter/payload-transform test coverage: any filter or payload-transform logic MUST include at least one unit test with a matching fixture/request value that returns a record and preserves relevant output fields; empty-result-only assertions MUST NOT satisfy coverage.
- Local smoke gate for HTTP/filter scope: work touching HTTP route handlers, query/filter logic, or new API endpoints MUST run `make test-smoke-all-local` and capture the pass/fail result as test evidence in `pr_context.md`; hand-crafted `curl` assertions are no longer sufficient as evidence.
- Reproducible-finding translation gate: any reproducible pre-PR smoke/`curl`/deterministic-check failure MUST be captured as a failing automated test first and turned green with the implementation fix in the same work item; deterministic exceptions MUST be documented in publish artifacts.
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
- For each entry in `Deferred Proposals`, present a triage table and wait for the user to confirm an outcome per proposal before acting: **file-issue** (create a GitHub issue and record the URL), **reject** (record rationale in `pr_context.md` and close in `AGENTS.backlog.md`), or **park** (record in `AGENTS.backlog.md` with a mandatory trigger: `after: <slug>`, `on-scope: <tag>` from the Scope Registry, or `triage: next-session`). No proposal may be silently omitted — every proposal receives an explicit recorded outcome.
- Pull requests must follow repository templates and include equivalent sections for deterministic review context.
- Canonical skill for this phase: `blueprint-sdd-step07-pr-packager`.

## Specialized Agent Collaboration (When Used)
- Partition ownership by bounded context and dependency direction, not by arbitrary files.
- Backend/API contributors (for example FastAPI stacks) should preserve `domain -> application -> infrastructure -> presentation` flow and explicit contract boundaries.
- Frontend contributors (for example Vue stacks) should preserve feature boundaries, typed API contracts, state/event flow clarity, and testability.
- Always preserve deterministic handoffs: each task must map to SDD artifacts, validation evidence, and a clear owner.

## Assistant Interoperability
- SDD artifacts (`specs/**`, `.spec-kit/**`) and Make targets are the canonical, tool-agnostic execution contract for any code assistant.
- Assistants MUST default to SDD-enabled execution unless the user explicitly opts out in the current request.
- Bundled Codex skills under `.agents/skills/**` are accelerators, not alternative governance; they must resolve to the same lifecycle/order/validation contract.
- For assistants that do not support Codex skill loading (for example Claude Code), use the corresponding `SKILL.md` files as plain-text runbooks and still execute canonical repository commands.
- When specialized subagents are used, assign each one to an isolated worktree and bounded-context ownership slice to prevent write collisions.
- The work-item spec must explicitly declare the selected stack profile and agent execution model before implementation.
- Skill runbooks (`.agents/skills/*/SKILL.md`) are governed by this file. Any update to
  cross-cutting guardrails, lifecycle policy, or sign-off rules in `AGENTS.md` MUST be
  reflected in the `## Governance Context` section of the relevant skill runbooks. Conversely,
  when a `SKILL.md` introduces new operator-facing guidance, verify that it aligns with the
  canonical policy here and add an explicit section to `AGENTS.md` if needed.

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
- Unit and integration tests MUST use mocked or stubbed external dependencies. Real
  network calls, database connections, or external services are not acceptable in unit
  tests and require explicit justification in integration tests.
- Target line coverage ≥ 70% for all non-trivial code paths.
- Business-critical features (declared as acceptance criteria in `spec.md`) MUST have
  100% automated test coverage before the DoD is signed off.
- The full default CI pipeline (excluding execute-mode infra and e2e lanes) MUST
  complete in under 15 minutes. Flag any addition that pushes past this budget before
  merging.
- E2E tests are reserved for the smallest possible set of business-critical user
  journeys that cannot be validated by component or contract tests. Never add an E2E
  test where a Pact contract or component test provides equivalent confidence.

## Contract Testing Standards
- Consumer-Driven Contract Testing (Pact) is the standard for verifying API integration
  correctness across service boundaries. Direct E2E tests across service boundaries are
  strictly discouraged.
- The consumer side (frontend / client service) generates Pact contracts from unit-level
  interaction tests against the Pact Mock Server. Generated `.json` pact files are the
  contract artefacts checked into source control.
- The provider side (backend service) verifies published contracts in isolated tests
  (`backend-test-contracts` lane) without requiring a live frontend or full integration
  environment.
- During frontend development, use the Pact Stub Server to simulate provider responses
  instead of pointing tests at a live backend service.
- OpenAPI specs and event/message contracts that define new or changed service interfaces
  MUST be drafted in the Specify phase before implementation code is written. Record the
  contract file path in `spec.md` under Contract Impacts.

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
  - `docs/blueprint/**` is canonical in source mode; bootstrap template sync MUST include ONLY the consumer-facing allowlisted subset defined by blueprint docs-sync contract.
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
