# Spec-Driven Development (SDD) Operating Model

This blueprint follows an explicit SDD lifecycle for non-trivial work.

For a step-by-step execution walkthrough — what command starts each step,
what artifacts are produced, when commits and PRs are created, and what checks
run — see the [SDD Execution Guide](sdd_execution_guide.md).

## Lifecycle

1. `Discover`
2. `High-Level Architecture`
3. `Specify`
4. `Plan`
5. `Implement`
6. `Verify`
7. `Document`
8. `Operate`
9. `Publish`

Implementation should not start before the first four phases are materially captured.

SDD is mandatory by default for assistant-executed work. A lightweight or non-SDD path is valid only when the user explicitly opts out in the current request.

When starting a new work item, use `make spec-scaffold SPEC_SLUG=<work-item-slug>`; it creates and checks out a dedicated non-default branch by default. Explicit opt-out requires `SPEC_NO_BRANCH=true`.

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

## Readiness Gate (Mandatory)

`Implement` is blocked until `spec.md` records:

- `SPEC_READY=true`
- `Open questions count: 0`
- `Unresolved alternatives count: 0`
- `Unresolved TODO markers count: 0`
- `Pending assumptions count: 0`
- Approved sign-offs for `Product`, `Architecture`, `Security`, and `Operations`
- `ADR path` and approved `ADR status`

If required inputs are missing, add `BLOCKED_MISSING_INPUTS` and keep `SPEC_READY=false`.
Code assistants must not fill missing requirements with assumptions in spec artifacts.
Use `[NEEDS CLARIFICATION: ...]` markers for unresolved inputs and keep `Open clarification markers count` at `0` before `SPEC_READY=true`.

## Canonical Artifacts

- Policy mapping: `.spec-kit/policy-mapping.md`
- Control catalog source: `.spec-kit/control-catalog.json`
- Control catalog rendered view: `.spec-kit/control-catalog.md`
- Template packs:
  - `.spec-kit/templates/blueprint/`
  - `.spec-kit/templates/consumer/`
- Work-item workspace: `specs/<YYYY-MM-DD>-<work-item-slug>/`
- ADR repositories:
  - `docs/blueprint/architecture/decisions/`
  - `docs/platform/architecture/decisions/`

Each work item should include:
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
- Finalized ADR document (using `.spec-kit/templates/<track>/adr.md`)

Non-feature change types (bug fix, upgrade, refactor, chore) MUST NOT be forced through
the full 10-artifact cycle. Use the Lightweight SDD Bypass Track: set `SPEC_READY_EXCEPTION`
and `authorized-by` in `spec.md` to reduce the required artifact set to `{spec.md, pr_context.md}`.
See `AGENTS.md §Lightweight SDD Bypass Track` for activation, tiered minimum traceability, and rollback.

Optional for complex work:
- `research.md`
- `data-model.md`
- `contracts/`
- `quickstart.md`

## Acceptance Criteria Authoring Rule

Every AC in `spec.md` MUST follow the canonical form from the first draft:

```
AC-NNN [<describe what is verified>] — verified by T-N, which MUST assert <exact condition that must hold>.
```

The assertion description MUST name a concrete, objectively verifiable condition. Label-only entries
that use a verb without a postcondition (`covers`, `verifies`, `tests`) are rejected by the
`blueprint-sdd-step03-spec-complete` gate. In addition, `make quality-sdd-check` runs a machine
check (`_check_ac_format` in `check_sdd_assets.py`) that flags any `^- AC-\d+` line in `spec.md`
(outside fenced code blocks) that does not contain `MUST assert` — for work items with slug date
≥ 2026-06-01. Scaffold templates seed ACs in this form; do not replace them with label-only stubs.

## Control and Stack Requirements in `spec.md`

Each work-item `spec.md` must define:
- `Applicable Guardrail Controls` section with `SDD-C-###` IDs.
- `Implementation Stack Profile` section with:
  - backend stack profile
  - frontend stack profile
  - test automation profile
  - agent execution model
  - managed-service decision fields
  - local-first runtime baseline fields

## Guardrails to Capture in Specs

- Security and privacy
- Observability (logs/metrics/traces)
- Monitoring and alerting ownership
- Reliability, resilience, and rollback strategy
- Operability and diagnostics
- Architecture quality (SOLID, Clean Architecture/Clean Code, DDD adapted to stack)
- Shift-left test automation and test-pyramid adherence
- Positive-path filter/payload-transform coverage (matching fixture/request value returns record and output fields are preserved; empty-result-only assertions are insufficient)
- API response field-coverage gate (HTTP-scope slices adding/modifying response schema fields): backend integration test using FastAPI `TestClient` MUST assert ALL declared response contract fields are non-null/non-empty against a real-data fixture; asserting only a 200 response or non-empty body is insufficient
- Spec-value regression tests: when a spec enumerates allowed values (status codes, enum variants, config keys), at least one unit test MUST assert against the literal spec values — not a superset or pattern match
- Union types for spec-enumerated fields: spec-enumerated fields MUST be typed as union/literal types, not bare `str`/`string`/`any`, in every language the implementation uses (TypeScript `'a' | 'b'`, Python `Literal["a","b"]`, Kotlin `enum class`, Go typed `const` block)
- Single source of truth for enum constants: enum values MUST be defined in exactly one place (e.g. `as const` array, module-level tuple, companion object) and imported everywhere else — no inline string literals duplicating spec values
- Vue SFC rendering-branch coverage: for any Vue SFC change, Vitest Browser Mode component tests MUST cover every rendering branch touched — including fallback, degraded, and error paths — before the slice is done
- Critical user journey rendered-output coverage: Vitest Browser Mode satisfies the rendered-output gate by default; Playwright is required only when the critical path crosses route boundaries, auth/session state, or multiple mounted roots
- V-gate E2E classification: every work item spec MUST declare `Has user-facing flow` (true/false) and `E2E gate classification` (automated | manual | N/A) in the Implementation Stack Profile. When `has-user-facing-flow: true` and the test automation profile contains `playwright`, `E2E gate classification` MUST be `automated`; any other value is a gate violation caught by `make quality-sdd-check`. Step01 intake pre-sets `has-user-facing-flow` from issue signals (shift-left); the author overrides to `false` with justification only if the inference is wrong. Step07 triage escalation: unresolved V-gate violations block PR merge and are escalated to the platform team.
- Pact consumer + same-repo provider timing: for HTTP-scope slices modifying API contracts, a Pact consumer interaction MUST be written in the same slice; same-repo provider verification MUST run in the same slice; cross-repo deferral MUST be explicitly recorded in the slice-done report
- Local smoke gate for HTTP route/filter scope: `make test-smoke-all-local` is a mandatory numbered main workflow step (Step 3) — not optional — and a PR MUST NOT be opened until it passes; `pr_context.md` evidence required
- Reproducible-finding translation gate (pre-PR smoke/deterministic-check failures become failing automated tests first, then green with the fix in the same work item; deterministic exceptions are documented)
- Managed-service-first runtime posture (`stackit-*` profiles default to managed STACKIT services; exceptions require explicit approved rationale)
- Local-first runtime baseline for local execution (`docker-desktop` context policy + Crossplane/Helm provisioning + ESO/Argo/Keycloak runtime identity), with explicit approved exception rationale when deviating
- App onboarding minimum Make-target contract, including canonical port-forward wrappers

## Managed-Service Decision Contract

- Record managed-service posture in `spec.md` `Implementation Stack Profile`:
  - `Managed service preference: stackit-managed-first` (default)
  - `Managed service exception rationale: none` (default)
- If `Managed service preference` is `explicit-consumer-exception`, include:
  - explicit rationale and affected capabilities
  - approved ADR entry
  - decision-log record in `AGENTS.decisions.md`
- No implementation starts from an exception path without explicit approval evidence.

## Local-First Runtime Contract

- Record local-first posture in `spec.md` `Implementation Stack Profile`:
  - `Runtime profile: local-first-docker-desktop-kubernetes`
  - `Local Kubernetes context policy: docker-desktop-preferred`
  - `Local provisioning stack: crossplane-plus-helm`
  - `Runtime identity baseline: eso-plus-argocd-plus-keycloak`
  - `Local-first exception rationale: none`
- If runtime profile deviates, include explicit approved exception rationale in `spec.md`, ADR, and `AGENTS.decisions.md`.

## App Onboarding Contract

- `plan.md` MUST include an `App Onboarding Contract` section.
- `tasks.md` MUST include an `App Onboarding Minimum Targets` section.
- Minimum required targets:
  - `apps-bootstrap`
  - `apps-smoke`
  - backend/touchpoints lane targets
  - aggregate test targets
  - `infra-port-forward-start`
  - `infra-port-forward-stop`
  - `infra-port-forward-cleanup`

## Graph and Evidence Contract

- `graph.json` is the machine-readable dependency map for requirement/acceptance nodes.
- `traceability.md` MUST map the same requirement/acceptance IDs declared in `graph.json`.
- `evidence_manifest.json` stores deterministic file checksum evidence for the work item.
- `context_pack.md` is the normalized execution handoff summary for implementation/review/operations.
- Canonical helper targets:
  - `make spec-impact`
  - `make spec-evidence-manifest`
  - `make spec-context-pack`
  - `make spec-pr-context`

## Hardening Review Contract

- Before publish/review, complete a repository-wide hardening review and store it in `hardening_review.md`.
- Required sections:
  - `Repository-Wide Findings Fixed`
  - `Observability and Diagnostics Changes`
  - `Architecture and Code Quality Compliance`
  - `Proposals Only (Not Implemented)`
- Canonical command:
  - `make quality-hardening-review`

## Publish Contract

- `Publish` creates deterministic PR-review context, not just code diff publication.
- `pr_context.md` must include:
  - `Summary`
  - `Requirement Coverage`
  - `Key Reviewer Files`
  - `Validation Evidence`
  - `Risk and Rollback`
  - `Deferred Proposals`
- PR templates must contain equivalent headings so code-review agents can focus on contract-critical context.

## Blueprint Defect Escalation Contract (Consumer Track)

- If a consumer discovers a blueprint-managed defect, escalate upstream using blueprint issue templates.
- Keep temporary consumer workaround lifecycle explicit in spec/docs until upstream fix is adopted:
  - `Upstream issue URL`
  - `Temporary workaround path`
  - `Replacement trigger`
  - `Workaround review date`

## Lifecycle Skill Mapping (Deterministic Agent Workflow)

Each skill covers one or more execution steps from the
[SDD Execution Guide](sdd_execution_guide.md):

| Skill | Steps | Actor |
|---|---|---|
| `blueprint-sdd-step01-intake` | 0 (auto-scaffold) + 1–2 (Discover → Plan, Draft PR) | Any stakeholder |
| `blueprint-sdd-step02-resolve-questions` | 0 (auto-scaffold, safety) + 3 (open question resolution loop) | Any stakeholder |
| `blueprint-sdd-step03-spec-complete` | 4 (Architecture/Security/Ops sign-offs, SPEC_READY) — **mandatory gate** enforced by `make quality-sdd-check` for `{none, bug-fix, refactor, chore, authorized-deviation}` tracks; exempt for `upgrade` and `chore-with-no-specs` | Software Engineer · CTO / Architect |
| `blueprint-sdd-step04-plan-slicer` | 5 (plan refinement, optional) | Software Engineer |
| `blueprint-sdd-step05-implement` | 6 (TDD implementation slices) | Software Engineer |
| `blueprint-sdd-step06-document-sync` | 7 (Document + Operate) | Software Engineer |
| `blueprint-sdd-step07-pr-packager` | 8–9 (Publish, mark PR ready) | Software Engineer |
| `blueprint-sdd-traceability-keeper` | Cross-cutting (coverage and drift control) | Software Engineer |

Skills retired: `blueprint-sdd-intake-decompose`, `blueprint-sdd-po-spec`,
`blueprint-sdd-clarification-gate` — their responsibilities are covered by
`step01-intake` and `step02-resolve-questions`.

These skills accelerate execution but do not replace lifecycle gates or validation commands.

## Multi-Agent Compatibility

The SDD contract is tool-agnostic. Any assistant must follow:
- `AGENTS.md` governance
- `.spec-kit/**` templates
- canonical Make/validation commands

For details (including non-Codex assistants such as Claude Code), see:
- [Assistant Compatibility](assistant_compatibility.md)
- [SDD Execution Guide](sdd_execution_guide.md) — step-by-step execution walkthrough with commands, git operations, and checks

## Normative Language Rules

- Normative behavior sections use deterministic keywords: `MUST`, `MUST NOT`, `SHALL`, `EXACTLY ONE OF`.
- Ambiguous terms are forbidden in normative sections:
  - `should`
  - `may`
  - `could`
  - `might`
  - `either`
  - `and/or`
  - `as needed`
  - `approximately`
  - `etc.`
- Informative sections can explain context and tradeoffs, but do not define implementation behavior.

## Document and Operate Expectations

- `Document` phase updates blueprint and consumer docs, including Mermaid diagrams where impacted.
- Required docs validation commands:
  - `make docs-build`
  - `make docs-smoke`
- `Operate` captures diagnostics ownership, monitoring/alerting, and rollback/runbook readiness.

## Specialized Contributor Pattern

When splitting implementation across backend/frontend specialists, assign ownership by bounded context and interface contract, use isolated worktrees, and map each slice into the same traceability matrix.
