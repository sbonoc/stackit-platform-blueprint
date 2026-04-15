# Spec-Driven Development (SDD) Operating Model

This blueprint follows an explicit SDD lifecycle for non-trivial work.

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
- Control catalog source: `.spec-kit/control-catalog.yaml`
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
- `graph.yaml`
- `evidence_manifest.json`
- `context_pack.md`
- `pr_context.md`
- `hardening_review.md`
- Finalized ADR document (using `.spec-kit/templates/<track>/adr.md`)

Optional for complex work:
- `research.md`
- `data-model.md`
- `contracts/`
- `quickstart.md`

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

- `graph.yaml` is the machine-readable dependency map for requirement/acceptance nodes.
- `traceability.md` MUST map the same requirement/acceptance IDs declared in `graph.yaml`.
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

Use this mapping when Codex skills are available:
- `Discover` + initial decomposition: `blueprint-sdd-intake-decompose`
- Clarification/readiness gate: `blueprint-sdd-clarification-gate`
- Slice planning and ownership: `blueprint-sdd-plan-slicer`
- Coverage and drift control: `blueprint-sdd-traceability-keeper`
- `Document` phase completion: `blueprint-sdd-document-sync`
- `Publish` phase packaging: `blueprint-sdd-pr-packager`

These skills accelerate execution but do not replace lifecycle gates or validation commands.

## Multi-Agent Compatibility

The SDD contract is tool-agnostic. Any assistant must follow:
- `AGENTS.md` governance
- `.spec-kit/**` templates
- canonical Make/validation commands

For details (including non-Codex assistants such as Claude Code), see:
- [Assistant Compatibility](assistant_compatibility.md)

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
