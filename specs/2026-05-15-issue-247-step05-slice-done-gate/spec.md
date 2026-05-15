# Specification

## Spec Readiness Gate (Blocking)
<!-- SPEC_PRODUCT_READY=true: intake gate — Product sign-off only; unlocks agent ADR drafting.
     SPEC_READY=true: implementation gate — all sign-offs required; unlocks coding. -->
- SPEC_READY: false
- SPEC_PRODUCT_READY: false
- Open questions count: 0
- Unresolved alternatives count: 0
- Unresolved TODO markers count: 0
- Pending assumptions count: 0
- Open clarification markers count: 0
- Product sign-off: pending
- Architecture sign-off: pending
- Security sign-off: pending
- Operations sign-off: pending
- Missing input blocker token: none
- ADR path: docs/blueprint/architecture/decisions/ADR-issue-247-step05-slice-done-gate.md
- ADR status: proposed
- SPEC_READY_EXCEPTION: none
- authorized-by: none

## Applicable Guardrail Controls (Normative)
- Applicable control IDs: SDD-C-001, SDD-C-002, SDD-C-003, SDD-C-004, SDD-C-005, SDD-C-006, SDD-C-011, SDD-C-012, SDD-C-016, SDD-C-017, SDD-C-019, SDD-C-020, SDD-C-021
- Control exception rationale: SDD-C-007 not applicable — docs-only change; no code architecture boundaries crossed. SDD-C-008 not applicable — no automated test suite; docs changes have no test pyramid. SDD-C-009 not applicable — no authn/authz or secret-handling paths. SDD-C-010 not applicable — no metrics/traces owned by this change. SDD-C-013 not applicable — tooling only; no STACKIT managed service. SDD-C-014 not applicable — no runtime changes; tooling only. SDD-C-015 not applicable — no app delivery workflow impact. SDD-C-018 not applicable — no blueprint-managed defect workaround. SDD-C-022 not applicable — no HTTP routes. SDD-C-023 not applicable — no filter/transform logic. SDD-C-024 not applicable — docs-only; no pre-PR smoke failures possible.

## Implementation Stack Profile (Normative)
- Backend stack profile: none
- Frontend stack profile: none
- Test automation profile: none
- Agent execution model: single-agent
- Managed service preference: explicit-consumer-exception
- Managed service exception rationale: governance tooling only; no STACKIT managed service involved
- Runtime profile: local-first-docker-desktop-kubernetes
- Local Kubernetes context policy: docker-desktop-preferred
- Local provisioning stack: crossplane-plus-helm
- Runtime identity baseline: custom-approved-exception
- Local-first exception rationale: no runtime changes; governance tooling only

## Objective
- Business outcome: Close four structural gaps in the `blueprint-sdd-step05-implement` skill's per-slice definition of done that allowed a spec-compliant, green-test implementation to ship with six missing API response fields visible and wrong in the browser. The gaps permitted: (1) new response schema fields that serialize as null with no integration test gate; (2) Vue rendering branches that are never exercised by any component test; (3) Pact consumer interactions written without verifying the same-repo provider in the same slice; and (4) the local smoke test being treated as optional. This work item adds three new guardrails and promotes the smoke gate to a mandatory, numbered workflow step, closing all four gaps without altering any existing guardrail.
- Success metric: (1) SKILL.md contains Guardrails #13, #14, and #15. (2) The "After All Slices Complete" table has distinct REQUIRED rows for HTTP scope and HTTP+UI rendering scope. (3) A numbered main workflow step "3. Local smoke gate" exists in SKILL.md. (4) `references/implement_checklist.md` exists on disk (contract compliance gap resolved) and accurately summarizes the new gates from SKILL.md. (5) AGENTS.md § Cross-Cutting Guardrails, § Testing and Quality Ratios, § Contract Testing Standards, and § Minimum Validation Bundles each contain the additions defined in FR-007 through FR-010. (6) `make quality-hooks-run` passes clean.

## Normative Requirements

### Functional Requirements (Normative)
- FR-001 `.agents/skills/blueprint-sdd-step05-implement/SKILL.md` MUST include a new Guardrail #13 stating: for any HTTP-scope slice that adds or modifies fields on a response schema, a backend integration test MUST assert that ALL fields declared in the response contract are present and non-null/non-empty in the HTTP response for a fixture with real (non-empty) data. Asserting only that the handler returns 200 or that the response is not empty MUST NOT satisfy this gate. This assertion MUST be implemented using FastAPI `TestClient` (no live cluster, no port-forward) — it is a pyramid-level integration test, not a smoke test. The local smoke gate (`make test-smoke-all-local`) is a separate, coarser reachability gate and MUST NOT be used as a substitute for this field-coverage assertion.
- FR-002 `.agents/skills/blueprint-sdd-step05-implement/SKILL.md` MUST include a new Guardrail #14 stating: for any Vue SFC rendering change (new component, modified template, or touched conditional branch), before marking the slice done the implementer MUST enumerate which Vitest Browser Mode component test covers each rendering branch touched — including fallback, degraded, and error paths. A slice MUST NOT be declared done if any rendering branch that was added or modified is absent from the component test suite.
- FR-003 `.agents/skills/blueprint-sdd-step05-implement/SKILL.md` MUST include a new Guardrail #15 stating: for any HTTP-scope slice that adds or modifies fields on an API response contract (TypeScript type, Pydantic schema, or OpenAPI spec): (a) a Pact consumer interaction asserting the new/modified field shape MUST be written in the same slice; (b) when the provider lives in the same repository, provider verification MUST pass in the same slice; (c) when the provider lives in a separate repository, the generated pact file MUST be committed and the slice-done report MUST explicitly record "Pact provider verification: deferred to provider repo <name>". A slice that extends an API contract without a Pact consumer interaction MUST NOT be declared done.
- FR-004 The "After All Slices Complete — Minimum validation bundle" table in SKILL.md MUST replace the single HTTP row with two distinct rows: one for "HTTP route / filter / query scope" marking `make test-smoke-all-local` as REQUIRED and non-optional, and one for "HTTP route + UI rendering scope" requiring both `make test-smoke-all-local` AND Vitest Browser Mode component test suite green — both marked REQUIRED.
- FR-005 The local smoke gate content MUST be promoted from the "Special cases" section in SKILL.md to a numbered unconditional main workflow step titled "3. Local smoke gate (HTTP and UI-rendering scope)", with an explicit statement that this step is REQUIRED and non-optional for HTTP and UI-rendering scope and that a PR MUST NOT be opened until it passes.
- FR-006 `.agents/skills/blueprint-sdd-step05-implement/references/implement_checklist.md` MUST exist on disk. It is listed as a `required_file` in `blueprint/contract.yaml` but is currently absent. Its content MUST summarize the per-slice gates introduced by Guardrails #13, #14, and #15 and the promoted smoke gate in concise checklist format. SKILL.md is the normative source; the checklist is a derived artifact and MUST remain consistent with SKILL.md. The checklist MUST NOT introduce requirements beyond what SKILL.md specifies.
- FR-007 AGENTS.md § Cross-Cutting Guardrails MUST be updated to add a field-coverage gate requirement: for any HTTP-scope change that adds or modifies fields on a response schema, a backend integration test using FastAPI `TestClient` (no live cluster, no port-forward) MUST assert that ALL declared response contract fields are non-null/non-empty against a fixture with real (non-empty) data. This extends the existing "Positive-path filter/payload-transform test coverage" bullet in that section and provides the canonical normative home for Guardrail #13.
- FR-008 AGENTS.md § Testing and Quality Ratios MUST be updated to add: for any Vue SFC rendering change, unit and component tests MUST cover every rendering branch touched — including fallback, degraded, and error paths — before the slice is declared done. This creates the canonical normative home for Guardrail #14, which the audit confirmed does not currently exist anywhere in AGENTS.md.
- FR-009 AGENTS.md § Contract Testing Standards MUST be updated to add: when both consumer (frontend) and provider (backend) live in the same repository, Pact provider verification MUST run in the same implementation slice as the consumer interaction test. Writing only the consumer interaction without verifying the same-repo provider in the same slice MUST NOT be treated as a complete Pact contract gate. This provides the canonical normative home for the same-repo timing requirement in Guardrail #15.
- FR-010 AGENTS.md § Minimum Validation Bundles MUST be updated to add two HTTP-scope entries: (a) "HTTP route / filter / query scope: `make test-smoke-all-local`" and (b) "HTTP route + UI rendering scope: `make test-smoke-all-local` AND Vitest Browser Mode component test suite green." These entries resolve the drift between § Cross-Cutting Guardrails (which already requires `test-smoke-all-local` for HTTP scope) and the Minimum Validation Bundles table (which currently has no HTTP-scope row).

### Non-Functional Requirements (Normative)
- NFR-MAINT-001 New Guardrails #13, #14, and #15 MUST follow the existing numbered format in SKILL.md and MUST use MUST / MUST NOT normative language. No existing guardrails (1–12) SHALL be removed or altered. All additions MUST be additive.
- NFR-COMPAT-001 All changes MUST be additive. Existing slices that already have backend integration tests covering all contract fields, Pact consumer interactions, provider verification results, and component test branch coverage MUST continue to satisfy the updated gate with no rework.
- NFR-A11Y-001 N/A — no UI or frontend changes.

## Normative Option Decision
- Option A: Edit SKILL.md with three new guardrails and promote the smoke test to a numbered main workflow step; create `references/implement_checklist.md`. Verification through the SDD spec review process and `make quality-hooks-run`. No automated content scanner added.
- Option B: Additionally add an automated quality check that verifies SKILL.md contains the required guardrail patterns and the smoke gate step, providing automated regression protection if the guardrails are accidentally removed.
- Selected option: OPTION_A
- Rationale: The skill runbook is human-authored governance prose, not a machine-verifiable interface contract. An automated guardrail-text scanner would couple the check to prose phrasing, requiring updates on any reword, and provides limited incremental value over the spec-to-code review gap already enforced by SDD review. Option B is parked as a future proposal (on-scope: skills).

## Contract Changes (Normative)
- Config/Env contract: none
- API contract: none
- OpenAPI / Pact contract path: none
- Event contract: none
- Make/CLI contract: none
- Docs contract: `AGENTS.md` gains four additions: field-coverage gate in § Cross-Cutting Guardrails; per-SFC rendering-branch coverage rule in § Testing and Quality Ratios; same-repo Pact provider timing requirement in § Contract Testing Standards; two HTTP-scope rows in § Minimum Validation Bundles. `.agents/skills/blueprint-sdd-step05-implement/SKILL.md` gains Guardrails #13, #14, #15 and a numbered "3. Local smoke gate" workflow step; minimum validation bundle table gains two explicit required rows; "Special cases" HTTP section is promoted to the main workflow. `.agents/skills/blueprint-sdd-step05-implement/references/implement_checklist.md` is created as a derived summary artifact (listed in `blueprint/contract.yaml` required_files but absent on disk); content is driven by the SKILL.md changes, not independently specified.

## Blueprint Upstream Defect Escalation (Normative)
- Upstream issue URL: none
- Temporary workaround path: none
- Replacement trigger: none
- Workaround review date: none

## Normative Acceptance Criteria
- AC-001 SKILL.md Guardrail #13 exists and requires: a backend integration test asserting ALL response contract fields are present and non-null/non-empty in the HTTP response for a fixture with real (non-empty) data; asserting only a 200 response or non-empty body MUST NOT satisfy the gate.
- AC-002 SKILL.md Guardrail #14 exists and requires: for any Vue SFC rendering change, the implementer MUST enumerate which Vitest Browser Mode component test covers each rendering branch touched (including fallback, degraded, and error paths); a slice MUST NOT be declared done if any touched branch is absent from the component test suite.
- AC-003 SKILL.md Guardrail #15 exists and requires: (a) a Pact consumer interaction for any HTTP-scope slice modifying a response contract; (b) same-repo provider verification in the same slice; (c) cross-repo deferral recorded explicitly in the slice-done report. A slice that extends an API contract without a Pact interaction MUST NOT be declared done.
- AC-004 The "After All Slices Complete — Minimum validation bundle" table in SKILL.md contains at least two HTTP-scope rows: one for "HTTP route / filter / query scope" and one for "HTTP route + UI rendering scope", both explicitly marked as REQUIRED and non-optional.
- AC-005 A numbered main workflow step "3. Local smoke gate (HTTP and UI-rendering scope)" exists in SKILL.md before the "After All Slices Complete" section, clearly stating the gate is REQUIRED and that a PR MUST NOT be opened until it passes.
- AC-006 `.agents/skills/blueprint-sdd-step05-implement/references/implement_checklist.md` exists on disk (contract compliance gap resolved). Its content is a concise checklist summary of the per-slice gates from Guardrails #13, #14, #15 and the smoke gate step; it introduces no requirements beyond SKILL.md.
- AC-007 `make quality-hooks-run` passes clean after all changes are applied.
- AC-008 AGENTS.md § Cross-Cutting Guardrails contains a requirement that, for HTTP-scope schema changes, ALL response contract fields MUST be asserted non-null/non-empty in a FastAPI `TestClient` integration test against a real-data fixture.
- AC-009 AGENTS.md § Testing and Quality Ratios contains a requirement that Vue SFC rendering changes MUST have component tests covering every rendering branch touched — including fallback, degraded, and error paths.
- AC-010 AGENTS.md § Contract Testing Standards contains a requirement that same-repo Pact provider verification MUST run in the same implementation slice as the consumer interaction test.
- AC-011 AGENTS.md § Minimum Validation Bundles contains two HTTP-scope entries: one for "HTTP route / filter / query scope" and one for "HTTP route + UI rendering scope".

## Informative Notes (Non-Normative)
- Context: The delivery gap was confirmed through a real incident: a spec-compliant, fully green-test implementation shipped with six missing catalog fields (summary, assetType, industryTags, complianceTags, sovereigntyTags, createdAt) that were visible and wrong in the browser but caught by no automated gate. The root cause analysis identified four structural gaps in the skill's per-slice definition of done — all of which would have been covered by Guardrails #13–#15 and the promoted smoke gate.
- Tradeoffs: Adding Guardrails #13–#15 raises the bar for HTTP and UI-rendering scope slices. Slices that previously passed by asserting only a 200 response and green unit tests now require additional evidence (field coverage assertion, component test branch enumeration, Pact consumer+provider). This is intentional; the previous bar was insufficient.
- Clarifications: The cross-repo Pact deferral protocol (Guardrail #15c) does not block the slice but requires an explicit acknowledgment in the slice-done report. This is by design — the consumer's Pact interaction is the artifact; provider verification gates belong to the provider team.

## Explicit Exclusions
- Option B (automated SKILL.md content scanner) is explicitly out of scope.
- Changes to other SDD step skill runbooks (step-01 through step-07) are out of scope; only step-05 is affected.
- No changes to `blueprint/contract.yaml` or any Make targets.
- No changes to existing guardrails 1–12 in SKILL.md.
- AGENTS.md changes are limited to the four additions defined in FR-007 through FR-010; no other sections of AGENTS.md are in scope.
