# Specification

## Spec Readiness Gate (Blocking)
<!-- SPEC_PRODUCT_READY=true: intake gate — Product sign-off only; unlocks agent ADR drafting.
     SPEC_READY=true: implementation gate — all sign-offs required; unlocks coding. -->
- SPEC_READY: true
- SPEC_PRODUCT_READY: true
- Open questions count: 0
- Unresolved alternatives count: 0
- Unresolved TODO markers count: 0
- Pending assumptions count: 0
- Open clarification markers count: 0
- Product sign-off: approved
- Architecture sign-off: approved
- Security sign-off: approved
- Operations sign-off: approved
- Missing input blocker token: none
- ADR path: docs/blueprint/architecture/decisions/ADR-issue-352-sdd-step03-step05-drift-loop.md
- ADR status: approved
- SPEC_READY_EXCEPTION: none
- authorized-by: none

## Applicable Guardrail Controls (Normative)
- Applicable control IDs: SDD-C-002, SDD-C-004, SDD-C-005, SDD-C-006, SDD-C-008, SDD-C-012, SDD-C-019, SDD-C-020, SDD-C-023
- Control exception rationale: none

## Implementation Stack Profile (Normative)
- Backend stack profile: python_plus_fastapi_pydantic_v2
- Frontend stack profile: vue_router_pinia_onyx
- Test automation profile: pytest_vitest_playwright_pact
- Agent execution model: specialized-subagents-isolated-worktrees
- Managed service preference: stackit-managed-first
- Managed service exception rationale: none
- Runtime profile: local-first-docker-desktop-kubernetes
- Local Kubernetes context policy: docker-desktop-preferred
- Local provisioning stack: crossplane-plus-helm
- Runtime identity baseline: eso-plus-argocd-plus-keycloak
- Local-first exception rationale: none

## Objective
- Business outcome: Close the structural loop between SDD step03 (spec authoring) and step05 (implementation) so spec-to-implementation drift in named values, types, defaults, and rendered UI is caught by automated gates rather than surfacing only at manual browser testing.
- Success metric: After this work item ships, a new full-SDD feature work item MUST NOT reach a merged state in which (a) a spec-enumerated value is duplicated as inline literals across more than one source file, OR (b) a field declared with `EXACTLY ONE OF: a | b | c` carries a plain primitive type in implementation code, OR (c) a critical-path user-facing flow has zero automated rendered-output assertions. (a) and (b) are enforced by the step05 SKILL.md implementation checklist (human gate); (c) is enforced by the same checklist plus the mandatory Vitest Browser Mode / Playwright coverage requirement (FR-008). The only new machine-automated check added by this work item is FR-002: `make quality-sdd-check` rejects any work item with `SPEC_READY: true` that lacks a `spec-complete` C7 event, which is the prerequisite gate that makes (a)/(b)/(c) auditable.

## Normative Requirements

### Functional Requirements (Normative)

- FR-001 — Step03 promoted to mandatory gate. AGENTS.md `§ Mandatory Workflow` MUST classify `blueprint-sdd-step03-spec-complete` as a mandatory gate (not an "accelerator") for every work item whose `SPEC_READY_EXCEPTION` is one of `{none, bug-fix, refactor, chore, authorized-deviation}`. Skipping step03 for these tracks MUST be a documented governance violation.

- FR-002 — Machine-enforced step03 detection via C7 audit trail. `make quality-sdd-check` MUST reject a work item that is staged for implementation (i.e., `SPEC_READY: true`) when `artifacts/c7/<work-item-slug>.jsonl` does NOT contain at least one event with `phase: "spec-complete"` for the work item's ticket id. The check MUST produce a deterministic error message naming the work-item slug and the missing phase.

- FR-003 — Exempt tracks. `make quality-sdd-check` MUST NOT enforce the FR-002 check when EXACTLY ONE OF the following holds: (a) `SPEC_READY_EXCEPTION: upgrade` (pipeline-driven, no human sign-off model); (b) no `specs/` directory exists for the work item (chore-with-no-specs passive-pass case). The `c7-emission-opted-out` event written by the opt-out audit (see ADR-issue-347) MUST NOT satisfy FR-002 — only a true `spec-complete` event counts.

- FR-004 — Step03 AC authoring requires explicit assertion descriptions. `.agents/skills/blueprint-sdd-step03-spec-complete/SKILL.md` MUST require that every AC in `spec.md` names not only the test ID covering it but also the specific assertion the test MUST verify, in the form: `AC-NNN [description] — verified by T-N, which MUST assert <exact condition>.`. ACs whose body matches the regex pattern `verified by T-\d+(,| which) (covers|verifies|tests) <[^>]+>$` (label-only) MUST be REJECTED at the step03 spec-complete gate.

- FR-005 — Spec-value regression test mandate. `.agents/skills/blueprint-sdd-step05-implement/SKILL.md` Guardrails section MUST require that, for every FR or AC naming exact enumerated values, field defaults, required option sets, or specific behavioural postconditions, at least one test MUST exist that would fail if any named value were absent, wrong, or reordered. Coverage MUST include enumerated option sets, field defaults, behavioural postconditions, and required/forbidden fields.

- FR-006 — Union-type mandate for spec-enumerated fields. `.agents/skills/blueprint-sdd-step05-implement/SKILL.md` MUST require that any field whose allowed values are named in spec.md as `EXACTLY ONE OF: ...` uses a stack-native union/enum type in implementation code (TypeScript `'a' | 'b' | 'c'`, Pydantic `Literal["a","b","c"]`, Kotlin sealed class or enum, Go `const` enum group). A plain primitive type (`string`, `str`, `String`) for such a field MUST be a checklist failure.

- FR-007 — Single source of truth for enum constants. `.agents/skills/blueprint-sdd-step05-implement/SKILL.md` MUST require spec-enumerated value sets to be defined as a named constant in one canonical location per stack (TypeScript `as const` array or object, Python module-level tuple/Literal, Kotlin companion-object set, Go `const` block). All template option arrays, composable/store defaults, validation logic, and test fixtures MUST import and reference the constant rather than repeating values inline. Inline literal repetition MUST be a checklist failure.

- FR-008 — Mandatory automated rendered-output coverage for critical user journeys. `.agents/skills/blueprint-sdd-step05-implement/SKILL.md` MUST require that every feature introducing or modifying a user-facing flow (form, wizard, multi-step interaction) has at least one automated test that (a) exercises the critical path in a real browser against the running application or component, AND (b) asserts what the user sees at each step (field labels, option values, rendered state) — not just what the API receives. The test MUST be part of the automated quality gate.

- FR-009 — Vitest Browser Mode satisfies FR-008 by default; Playwright required only on escalation. A Vitest Browser Mode component test (existing Guardrail #14) MUST satisfy FR-008 when its assertions enumerate every rendered spec-enumerated value reachable through the critical path. When the critical path crosses route boundaries OR depends on auth/session state OR spans more than one mounted root component, an additional Playwright cross-page E2E test MUST be added.

- FR-010 — Stack-agnostic application of FR-005..FR-009. The new guardrails MUST apply to every `Implementation Stack Profile` declared in `spec.md`. `.agents/skills/blueprint-sdd-step05-implement/SKILL.md` MUST publish a per-profile examples table (TS, Python, Kotlin, Go) showing the canonical union-type and SSOT-constant idiom for each declared backend/frontend profile.

- FR-011 — Forward-only application. The new gates MUST apply only to work items whose spec-scaffold timestamp is on or after the merge date of this work item. Existing in-flight or merged work items MUST NOT be retroactively blocked.

- FR-012 — Shift-left AC authoring at step01 + scaffold templates. `.agents/skills/blueprint-sdd-step01-intake/SKILL.md` Discover-phase guidance MUST require ACs to be authored in the canonical form `AC-NNN [description] — verified by T-N, which MUST assert <exact condition>.` from the first draft. Both scaffold templates (`.spec-kit/templates/blueprint/spec.md` and `.spec-kit/templates/consumer/spec.md`) MUST seed the AC placeholders in the canonical form so the example itself teaches the pattern. The intent is to author ACs correctly at step01 rather than recover them at the step03 rejection gate.

- FR-013 — Machine-enforce AC format in `check_sdd_assets.py`. For work items with `SPEC_READY: true` and slug date prefix ≥ `2026-06-01`, `make quality-sdd-check` MUST scan each line of `spec.md` matching `^-\s+AC-\d+\b` (AC bullet lines) outside fenced code blocks and reject any such line that does NOT contain the literal phrase `MUST assert`. The error message MUST name the spec.md path, line number, and the offending AC text. This implements the machine-enforcement layer of FR-004 (reverses ADR D-7).

- FR-014 — Shift-left deferred-proposal documentation to step01. `.agents/skills/blueprint-sdd-step01-intake/SKILL.md` Discover phase MUST include a step requiring the author to document conscious scope exclusions in a `## Potential Deferred Proposals` section of `spec.md` from the first draft. Both scaffold templates (`.spec-kit/templates/blueprint/spec.md` and `.spec-kit/templates/consumer/spec.md`) MUST seed this section with a canonical placeholder. `.agents/skills/blueprint-sdd-step07-pr-packager/SKILL.md` triage guidance MUST distinguish pre-planned exclusions (documented at step01) from newly-discovered proposals (discovered during implementation), so step07 closes out both buckets.

### Non-Functional Requirements (Normative)

- NFR-SEC-001 — N/A — governance change with no runtime authn/authz/secret-handling impact. Rationale: changes are scoped to AGENTS.md text, SKILL.md runbooks, and `scripts/bin/quality/check_sdd_assets.py` validation logic; no new secrets, capabilities, or external interfaces are introduced.

- NFR-OBS-001 — The FR-002 check failure path MUST emit a deterministic METRIC line on stdout in the format `[METRIC] name=sdd_step03_missing_spec_complete value=1 work_item=<slug>` so that CI job logs provide an audit trail consistent with the existing `sdd_exception_gate_total` metric (AGENTS.md § Audit metric).

- NFR-REL-001 — A C7 helper failure (sink unwritable, disk full, malformed input) MUST NOT block FR-002 evaluation. When the JSONL file does not exist or is unparseable, the gate MUST report a deterministic error pointing to the JSONL path rather than crashing. Rollback is by reverting this work item's commits — no migration artefact is written that would persist outside the spec directory.

- NFR-OPS-001 — `make quality-sdd-check` MUST exit non-zero with a single composite error message when FR-002 is violated, naming the work-item slug, the missing phase, and the expected JSONL path. The fix path MUST be discoverable from the message text alone (no additional log inspection required).

- NFR-A11Y-001 — N/A — governance change with no UI surface.

## Normative Option Decision
- Option A: Bundle all six gaps into a single work item with one spec, one ADR, one PR (closed-loop framing per the issue body).
- Option B: Split into six sequential work items (one per gap) under an epic.
- Selected option: OPTION_A
- Rationale: The issue explicitly frames the six changes as one closed loop where removing any one leaves a bypass or blind spot. Splitting would (a) leave intermediate merged states where the loop is open, (b) require six rounds of step01–step07 overhead for changes that together touch ~5 files, and (c) contradict the user's stated decomposition preference for light slicing inside one work item rather than many tickets (memory: `feedback_decomposition_preference`).

## Contract Changes (Normative)
- Config/Env contract: No new environment variables. The existing `BLUEPRINT_SDD_C7_EMIT=0` opt-out is preserved; when set, FR-002 enforcement MUST defer to the existing opt-out audit semantics (the `c7-emission-opted-out` event does NOT satisfy FR-002 — opt-out work items fall under the FR-003 exemption only when they also match an exempt track).
- API contract: none
- OpenAPI / Pact contract path: none
- Event contract: No new C7 phase value — FR-002 consumes the existing `spec-complete` phase already emitted by step03 (verified in `scripts/lib/sdd/c7_emit.py` `_PHASES` enum).
- Make/CLI contract: `make quality-sdd-check` MUST emit the FR-002 enforcement result and the NFR-OBS-001 metric line. No new public Make targets are added.
- Docs contract: AGENTS.md `§ Mandatory Workflow` MUST be updated to reflect FR-001. `.agents/skills/blueprint-sdd-step01-intake/SKILL.md` MUST be updated per FR-012 (Discover-phase canonical AC authoring guidance) and FR-014 (scope-exclusions step + `## Potential Deferred Proposals` section requirement). `.agents/skills/blueprint-sdd-step03-spec-complete/SKILL.md` and `.agents/skills/blueprint-sdd-step05-implement/SKILL.md` MUST be updated per FR-004..FR-010. `.agents/skills/blueprint-sdd-step07-pr-packager/SKILL.md` MUST be updated per FR-014 (two-bucket triage). Both scaffold templates (`.spec-kit/templates/blueprint/spec.md` and `.spec-kit/templates/consumer/spec.md`) MUST have their `AC-001` placeholder replaced with the canonical form per FR-012 AND seed a `## Potential Deferred Proposals` section per FR-014. The README of each affected skill MUST cross-reference this ADR.

## Blueprint Upstream Defect Escalation (Normative)
- Upstream issue URL: none
- Temporary workaround path: none
- Replacement trigger: none
- Workaround review date: none

## Normative Acceptance Criteria

- AC-001 [Step03 gate — happy path] — verified by T-101, which MUST assert that `make quality-sdd-check` exits 0 for a fixture work item whose `spec.md` has `SPEC_READY: true` AND whose `artifacts/c7/<slug>.jsonl` contains at least one event with `phase: "spec-complete"` and matching `ticket_id`.

- AC-002 [Step03 gate — missing spec-complete event] — verified by T-102, which MUST assert that `make quality-sdd-check` exits non-zero AND emits the substring `sdd_step03_missing_spec_complete` AND the exact work-item slug in stderr when the JSONL file exists but contains no `spec-complete` event for the ticket.

- AC-003 [Exempt track — upgrade] — verified by T-103, which MUST assert that `make quality-sdd-check` exits 0 for a fixture work item whose `spec.md` declares `SPEC_READY_EXCEPTION: upgrade` AND whose JSONL contains no `spec-complete` event.

- AC-004 [Exempt track — chore-no-specs] — verified by T-104, which MUST assert that `make quality-sdd-check` exits 0 when no `specs/` subdirectory exists for the work item, even when no JSONL file is present.

- AC-005 [Opt-out event does NOT satisfy gate] — verified by T-105, which MUST assert that `make quality-sdd-check` exits non-zero when the JSONL file contains EXACTLY ONE `c7-emission-opted-out` event and zero `spec-complete` events for a non-exempt work item.

- AC-006 [Step03 SKILL.md AC authoring rule] — verified by T-201, which MUST assert that the string `verified by T-` AND the substring `which MUST assert` appear in the AC authoring section of `.agents/skills/blueprint-sdd-step03-spec-complete/SKILL.md` AND that the file contains an explicit rejection rule for label-only ACs.

- AC-007 [Step05 SKILL.md guardrails for FR-005..FR-008] — verified by T-202, which MUST assert that `.agents/skills/blueprint-sdd-step05-implement/SKILL.md` Guardrails section contains four new numbered guardrails covering (a) spec-value regression tests, (b) union types for spec-enumerated fields, (c) single source of truth for enum constants, (d) automated rendered-output coverage for critical user journeys.

- AC-008 [Stack-agnostic per-profile examples table for FR-010] — verified by T-203, which MUST assert that the implement SKILL.md contains a per-profile examples table with at least one row each for TypeScript (Vue/Nuxt), Python (FastAPI), Kotlin (Ktor), and Go (Gin) showing the union-type idiom and the SSOT-constant idiom.

- AC-009 [FR-009 Vitest Browser Mode escalation rule] — verified by T-204, which MUST assert that the implement SKILL.md text declares (a) Vitest Browser Mode component test satisfies FR-008 when assertions enumerate all rendered spec-enumerated values, AND (b) Playwright cross-page E2E is required when the critical path crosses route boundaries OR depends on auth/session state OR spans more than one mounted root.

- AC-010 [AGENTS.md mandatory-gate text for FR-001] — verified by T-205, which MUST assert that AGENTS.md `§ Mandatory Workflow` contains the literal phrase `mandatory gate` referring to `blueprint-sdd-step03-spec-complete` AND lists the exempt tracks `upgrade` and `chore-with-no-specs`.

- AC-011 [Shift-left AC authoring at step01 + scaffold templates for FR-012] — verified by T-206, which MUST assert that (a) `.agents/skills/blueprint-sdd-step01-intake/SKILL.md` contains the canonical AC form substring `verified by T-` AND `which MUST assert` in its Discover-phase authoring guidance, AND (b) both `.spec-kit/templates/blueprint/spec.md` and `.spec-kit/templates/consumer/spec.md` seed the `AC-001` placeholder in the canonical form (containing the substrings `verified by T-` and `which MUST assert`) rather than the legacy `AC-001 MUST be objectively testable.` placeholder.

- AC-012 [Machine AC format gate — FR-013] — verified by T-106, which MUST assert that (a) `make quality-sdd-check` exits 0 for a fixture `spec.md` containing only ACs with `MUST assert`; (b) exits non-zero naming the offending line when `spec.md` contains `- AC-001 covers authentication` (label-only, no `MUST assert`); (c) an AC inside a fenced code block lacking `MUST assert` is skipped and produces no violation; (d) a work item with slug date prefix < `2026-06-01` is exempt from the check even when its ACs are label-only.

- AC-013 [Proposals shift-left at step01 + scaffold + step07 — FR-014] — verified by T-207, which MUST assert that (a) `.agents/skills/blueprint-sdd-step01-intake/SKILL.md` contains guidance requiring scope exclusions in a `Potential Deferred Proposals` section from the first draft; (b) both `.spec-kit/templates/blueprint/spec.md` and `.spec-kit/templates/consumer/spec.md` seed a `## Potential Deferred Proposals` placeholder section; (c) `.agents/skills/blueprint-sdd-step07-pr-packager/SKILL.md` triage guidance explicitly names both buckets: pre-planned exclusions and newly-discovered proposals.

## Informative Notes (Non-Normative)
- Context: Six structural gaps identified in issue #352 collectively allow spec-to-implementation drift to survive automated gates and surface only at manual browser testing. The fix is a closed loop: shift-left AC authoring at step01 + scaffold templates (FR-012) → step03 rejection gate for label-only ACs (FR-004) → machine-enforced step03 presence check (FR-002) → spec-value regression tests (FR-005) → union types (FR-006) → SSOT constants (FR-007) → mandatory rendered-output coverage (FR-008).
- Tradeoffs: FR-001 raises the floor for non-feature tracks (bug-fix/refactor/chore now require step03), trading marginal authoring overhead against closing the manual-sign-off loophole. FR-009 reuses Vitest Browser Mode where possible to avoid forcing Playwright on every feature.
- Clarifications: none open.

## Explicit Exclusions
- Retroactive remediation: existing in-flight or merged work items are NOT re-validated against the new gates (per FR-011). The new gates apply only to work items whose spec-scaffold timestamp is on or after this work item's merge date.
- Generated-consumer changes: `blueprint/contract.yaml` is NOT modified. Generated consumer repos receive the new SKILL.md text via the standard skill-runbook propagation path (no contract field changes, no new template-rendered files).
- Upgrade-track step03 enforcement: `SPEC_READY_EXCEPTION: upgrade` work items are exempt from FR-002 per FR-003. The blueprint-upgrade pipeline is pipeline-driven and does not invoke step03; forcing the gate would block automated upgrade runs.
- E2E framework selection across non-Vue stacks: this work item does NOT mandate a specific E2E framework for Kotlin or Go frontends (none exist in the blueprint stack today). Playwright is named explicitly only as the escalation path for the existing `vue_router_pinia_onyx` profile.
