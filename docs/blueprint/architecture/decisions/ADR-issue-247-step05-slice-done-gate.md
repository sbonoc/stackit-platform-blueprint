# ADR — step-05-implement: Deterministic Slice-Done Gate for HTTP+UI-Rendering Scope

- Status: proposed
- Work item: 2026-05-15-issue-247-step05-slice-done-gate
- Closes: #247
- Date: 2026-05-15
- ADR technical decision sign-off: pending

## Context

### Confirmed delivery gap

A spec-compliant, fully green-test implementation shipped with six missing catalog response fields (summary, assetType, industryTags, complianceTags, sovereigntyTags, createdAt). All were visible and wrong in the browser. No automated gate caught the regression. Root-cause analysis identified four structural gaps in the `blueprint-sdd-step05-implement` skill's per-slice definition of done.

### Gap 1 — API response field coverage

Guardrail #5 requires positive-path assertions for filter and payload-transform changes, but does not require that every field declared in a response contract is asserted as non-null/non-empty in a backend integration test. A schema can be extended, all existing tests can pass, and new fields can silently serialize as null or be omitted entirely.

### Gap 2 — Vue rendering branch coverage

`AGENTS.md` has a binding rule ("unit + component test per SFC before the PR is done") but the skill does not operationalize this at the per-slice boundary. There is no checklist item requiring the implementer to enumerate which Vitest Browser Mode component test covers each rendering branch touched, including fallback, degraded, and error paths.

### Gap 3 — Pact same-repo provider verification

Pact is documented under "Stack-specific test isolation" as an approach, but it is not a mandatory per-slice artifact for HTTP-scope slices that add or modify response fields. Crucially, the skill makes no distinction between same-repo and cross-repo provider scenarios. When both consumer (Vue) and provider (FastAPI) live in the same repository, writing only the consumer interaction leaves the contract loop open.

### Gap 4 — Smoke gate is a "special case", not a hard gate

The local smoke test is listed under "Special cases" rather than as a numbered, unconditional main workflow step. This makes it visually optional and structurally subordinate to the main flow.

## Decision

Add three new guardrails to `.agents/skills/blueprint-sdd-step05-implement/SKILL.md` and promote the smoke gate to a numbered unconditional main workflow step. All changes are additive — no existing guardrail (1–12) is altered.

### Guardrail #13 — API response field coverage

For any HTTP-scope slice that adds or modifies fields on a response schema, a backend integration test MUST assert that ALL fields declared in the response contract are present and non-null/non-empty in the HTTP response for a fixture with real (non-empty) data. Asserting only a 200 response or a non-empty body MUST NOT satisfy this gate.

**Rationale**: The delivery gap demonstrated that schema extension without field-level assertion is a production-visible failure mode. The assertion must use a fixture with real data to detect null serialization; an empty/minimal fixture can make all fields appear correctly null.

### Guardrail #14 — Vue component test per rendering branch

For any Vue SFC rendering change, before marking the slice done the implementer MUST enumerate which Vitest Browser Mode component test covers each rendering branch touched — including fallback, degraded, and error paths. A slice MUST NOT be declared done if any added or modified rendering branch is absent from the component test suite.

**Rationale**: This operationalizes the existing `AGENTS.md` binding rule at the per-slice level. The rule existed but was not enforced at the slice boundary; enumeration makes the gap visible before it reaches review.

### Guardrail #15 — Pact consumer + provider (same-slice, same-repo)

For any HTTP-scope slice that adds or modifies fields on an API response contract: (a) a Pact consumer interaction asserting the new/modified field shape MUST be written in the same slice; (b) when the provider lives in the same repository, provider verification MUST pass in the same slice; (c) when the provider lives in a separate repository, the generated pact file MUST be committed and the slice-done report MUST explicitly record "Pact provider verification: deferred to provider repo <name>". A slice that extends an API contract without a Pact consumer interaction MUST NOT be declared done.

**Rationale**: Writing only the consumer interaction without verifying the same-repo provider leaves the contract loop open — the interaction documents what the frontend expects but does not confirm the backend delivers it. The cross-repo deferral path acknowledges the practical constraint while requiring an explicit acknowledgment in the slice-done report.

### Smoke gate promotion

The "HTTP route / query scope" block is moved from "Special cases" to a numbered main workflow step "3. Local smoke gate (HTTP and UI-rendering scope)". The minimum validation bundle table is updated with two distinct REQUIRED rows for HTTP scope and HTTP+UI rendering scope.

**Rationale**: A "special case" is visually optional. For HTTP and UI-rendering scope, the smoke test is the only gate that exercises the full rendering path end-to-end with real serialized data. It must be a hard, numbered step.

### references/implement_checklist.md

Create `.agents/skills/blueprint-sdd-step05-implement/references/implement_checklist.md` with four per-slice checklist items corresponding to the four gaps. The file is already listed as a `required_file` in `blueprint/contract.yaml`; this ADR resolves the on-disk gap.

## Option not taken — Option B: automated SKILL.md content scanner

An automated quality check that verifies SKILL.md contains the required guardrail patterns and the smoke gate step would provide automated regression protection if the guardrails are accidentally removed.

**Rejected for this work item**: The skill runbook is human-authored governance prose, not a machine-verifiable interface contract. An automated guardrail-text scanner couples the check to prose phrasing, requiring updates on any reword, and provides limited incremental value over the spec-to-code review gap already enforced by SDD review. Option B is parked as a backlog proposal (on-scope: skills) for a future iteration.

## Consequences

- New slices implementing HTTP or UI-rendering scope must provide: a backend integration test asserting all response contract fields (Guardrail #13), an enumeration of Vitest component tests per rendering branch (Guardrail #14), and a Pact consumer interaction with same-repo provider verification or explicit cross-repo deferral (Guardrail #15).
- The smoke gate is now a numbered unconditional step — not a special case. PRs for HTTP or UI-rendering scope MUST NOT be opened until it passes.
- No existing guardrails (1–12) are altered. Slices that already satisfy the new gates require no rework.
- The on-disk gap for `references/implement_checklist.md` is resolved. Consumer repos receive the file on next blueprint upgrade.
