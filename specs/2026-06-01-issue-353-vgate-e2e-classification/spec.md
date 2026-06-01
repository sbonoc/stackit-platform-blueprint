# Specification

## Spec Readiness Gate (Blocking)
<!-- SPEC_PRODUCT_READY=true: intake gate — Product sign-off only; unlocks agent ADR drafting.
     SPEC_READY=true: implementation gate — all sign-offs required; unlocks coding. -->
- SPEC_READY: false
- SPEC_PRODUCT_READY: false
- Open questions count: 3
- Unresolved alternatives count: 3
- Unresolved TODO markers count: 0
- Pending assumptions count: 0
- Open clarification markers count: 3
- Product sign-off: pending
- Architecture sign-off: pending
- Security sign-off: pending
- Operations sign-off: pending
- Missing input blocker token: none
- ADR path: docs/blueprint/architecture/decisions/ADR-issue-353-vgate-e2e-classification.md
- ADR status: proposed
- SPEC_READY_EXCEPTION: none
- authorized-by: none

## Applicable Guardrail Controls (Normative)
- Applicable control IDs: SDD-C-003, SDD-C-004, SDD-C-005, SDD-C-006, SDD-C-008, SDD-C-009, SDD-C-010, SDD-C-011, SDD-C-012, SDD-C-016, SDD-C-017, SDD-C-019, SDD-C-020, SDD-C-021, SDD-C-024
- Control exception rationale: SDD-C-001 not applicable (no BLOCKED_MISSING_INPUTS lifecycle — open questions are design choices, not missing business inputs). SDD-C-002 not applicable (this work item IS a gate; the control applies by following it, not by citing it). SDD-C-007 not applicable (no bounded-context or DDD concerns — tooling-only change). SDD-C-013 not applicable (no managed service provisioned). SDD-C-014 not applicable (Python scripting change; no K8s/Crossplane/ESO components). SDD-C-015 not applicable (no app delivery workflow scope). SDD-C-018 not applicable (not a consumer upstream-defect workaround). SDD-C-022 not applicable (no HTTP routes or API endpoints). SDD-C-023 not applicable (no filter or payload-transform logic).

## Implementation Stack Profile (Normative)
- Backend stack profile: python_scripting_plus_bash
- Frontend stack profile: none
- Test automation profile: pytest
- Agent execution model: single-agent
- Managed service preference: explicit-consumer-exception
- Managed service exception rationale: Tooling-only Python script change; no managed service is provisioned or consumed by this work item.
- Runtime profile: local-first-docker-desktop-kubernetes
- Local Kubernetes context policy: docker-desktop-preferred
- Local provisioning stack: crossplane-plus-helm
- Runtime identity baseline: eso-plus-argocd-plus-keycloak
- Local-first exception rationale: This change adds Python quality-gate tooling with no K8s, Crossplane, or runtime identity components. The local-first profile is declared for compliance; none of its runtime components are exercised by this work item.
- Has user-facing flow: false
- E2E gate classification: N/A
- E2E automation target: none

## Objective
- Business outcome: Consumer teams can no longer silently classify a user-facing feature's E2E gate as permanently `manual` and pass every automated quality check. Any work item scoped to a user-facing flow must carry an `automated` or time-bounded `manual-with-target` E2E gate classification; the quality gate enforces this machine-check before the PR can be marked ready.
- Success metric: `make quality-sdd-check` fails with a clear error when a post-gate-date spec declares `has-user-facing-flow: true` with a playwright-capable test profile and `E2E gate classification: manual`; it passes for `automated` and for valid `manual-with-target` with a present `E2E automation target` date.

## Normative Requirements

### Functional Requirements (Normative)

- FR-001 The Implementation Stack Profile in `spec.md` MUST be extended with three new fields: `has-user-facing-flow` (values: `true` | `false`), `E2E gate classification` (values: `automated` | `manual-with-target` | `manual`), and `E2E automation target` (ISO 8601 date string or `none`).
- FR-002 `check_sdd_assets.py` MUST implement a `_check_vgate_classification` function that, for each work item spec, applies the V-gate classification rule: when `has-user-facing-flow: true` AND the test automation profile string contains `playwright`, the `E2E gate classification` MUST NOT be `manual`.
- FR-003 When `E2E gate classification: manual-with-target`, `check_sdd_assets.py` MUST verify that `E2E automation target` is present and matches the pattern `\d{4}-\d{2}-\d{2}`; absence or malformation MUST produce a gate violation.
- FR-004 `_check_vgate_classification` MUST apply a forward-only guard keyed on `_VGATE_GATE_SINCE` (the ISO 8601 merge date of this work item's PR): work items whose slug date predates `_VGATE_GATE_SINCE` MUST be skipped entirely and produce no violation.
- FR-005 `_check_vgate_classification` MUST be wired into `_validate_work_item_specs` so that `make quality-sdd-check` invokes the check automatically for every work item in the catalog.
- FR-006 The blueprint spec template (`.spec-kit/templates/blueprint/spec.md`) and the consumer spec template (`.spec-kit/templates/consumer/spec.md`) MUST be updated to seed `has-user-facing-flow`, `E2E gate classification`, and `E2E automation target` fields in the Implementation Stack Profile section; the consumer init template mirror MUST be synced via `sync_consumer_init_sdd_assets.py`.
- FR-007 `AGENTS.md` MUST be updated to add a mandatory Playwright E2E artifact rule in the testing and quality section: when `has-user-facing-flow: true` and the test automation profile contains `playwright`, at least one Playwright test covering the critical-path user journey MUST be a required implementation artifact for the work item.
- FR-008 On any V-gate classification violation, `check_sdd_assets.py` MUST emit the metric `sdd_vgate_manual_e2e_violation=<count>` to stderr, consistent with the metric-emission pattern established in issue #352.

### Non-Functional Requirements (Normative)

- NFR-SEC-001 The `E2E automation target` date field MUST be validated as a syntactically correct ISO 8601 date string (`YYYY-MM-DD`); a value that is absent or does not match the pattern when `E2E gate classification: manual-with-target` MUST cause a gate violation. The check MUST NOT make network calls or access external services.
- NFR-OBS-001 All V-gate violations MUST be reported to stderr (not stdout); the violation message MUST identify the work item slug, the violating field, the current value, and the expected value to allow immediate correction without additional diagnosis.
- NFR-REL-001 `_check_vgate_classification` MUST be idempotent: re-running the check on the same spec MUST produce the same violation set regardless of run order or prior invocations.
- NFR-OPS-001 The check MUST NOT raise an unhandled exception for any well-formed spec.md; missing fields that trigger the rule MUST be reported as violations, not as Python exceptions.
- NFR-A11Y-001 N/A — this work item adds no UI; no WCAG scope applies.

## Normative Option Decision

> **[NEEDS CLARIFICATION: Q-1 — Explicit `has-user-facing-flow` flag or heuristic keyword scanning of the FR list for user-facing flow detection?]**
>
> **Options:**
> - **A) Explicit flag** — Author sets `has-user-facing-flow: true` in the spec. Deterministic, machine-checkable, requires conscious opt-in. (agent recommendation)
> - **B) Heuristic keyword scan** — Checker scans FR text for terms like "form", "wizard", "multi-step". No new field needed. Risk: high false-positive/negative rate; hard to unit-test comprehensively.
>
> **Agent recommendation:** Option A because explicit flags are deterministic and follow the same pattern already used for `SPEC_READY_EXCEPTION`. Heuristics produce unpredictable gate behavior.

> **[NEEDS CLARIFICATION: Q-2 — V-gate rule scope: any profile string containing "playwright", or only the exact string "pytest_vitest_playwright_pact"?]**
>
> **Options:**
> - **A) Contains "playwright"** — future-proof; covers custom profiles. (agent recommendation)
> - **B) Exact match "pytest_vitest_playwright_pact"** — narrowly scoped; lower risk of unintended trigger.
>
> **Agent recommendation:** Option A (substring match) because the check intent is "Playwright is available" — that intent is carried by any profile string naming playwright, not only the canonical one.

> **[NEEDS CLARIFICATION: Q-3 — Date validation depth: verify `E2E automation target` is a future date, or only that it is present and correctly formatted?]**
>
> **Options:**
> - **A) Present + correct format only** — simple; past-date enforcement belongs in step07 triage. (agent recommendation)
> - **B) Must be a future date** — stronger enforcement; but a check run after the target date always fails even if the team resolved it, creating spurious gate failures.
>
> **Agent recommendation:** Option A. Past-date escalation is a governance/review concern, not a hard machine gate.

- Option A (Q-1): Explicit `has-user-facing-flow` flag in spec.md Implementation Stack Profile.
- Option B (Q-1): Heuristic keyword scan of FR list.
- Selected option: [NEEDS CLARIFICATION: Q-1 — see above]
- Rationale: [NEEDS CLARIFICATION: pending Q-1 selection]

## Contract Changes (Normative)
- Config/Env contract: none
- API contract: none
- OpenAPI / Pact contract path: none
- Event contract: none
- Make/CLI contract: No new make targets. `make quality-sdd-check` behavior extended — now also runs `_check_vgate_classification` for every work item in the catalog.
- Docs contract: `AGENTS.md` testing section MUST be updated (FR-007). Blueprint and consumer spec templates MUST be updated (FR-006). Consumer init template mirror MUST be synced via `sync_consumer_init_sdd_assets.py` after consumer template update.

## Blueprint Upstream Defect Escalation (Normative)
- Upstream issue URL: none
- Temporary workaround path: none
- Replacement trigger: none
- Workaround review date: none

## Normative Acceptance Criteria

- AC-001 [V-gate check rejects manual classification for user-facing flow with playwright profile] — verified by T-101, which MUST assert that `_check_vgate_classification` returns at least one violation when the spec has `has-user-facing-flow: true`, test automation profile `pytest_vitest_playwright_pact`, and `E2E gate classification: manual`.
- AC-002 [V-gate check passes for automated classification] — verified by T-102, which MUST assert that `_check_vgate_classification` returns zero violations when the spec has `has-user-facing-flow: true`, test automation profile `pytest_vitest_playwright_pact`, and `E2E gate classification: automated`.
- AC-003 [V-gate check passes for manual-with-target with valid automation target] — verified by T-103, which MUST assert that `_check_vgate_classification` returns zero violations when the spec has `has-user-facing-flow: true`, `E2E gate classification: manual-with-target`, and `E2E automation target: 2026-12-31`.
- AC-004 [V-gate check rejects manual-with-target with absent automation target] — verified by T-104, which MUST assert that `_check_vgate_classification` returns at least one violation when `E2E gate classification: manual-with-target` and `E2E automation target` is `none` or absent.
- AC-005 [V-gate check rejects manual-with-target with malformed automation target] — verified by T-105, which MUST assert that `_check_vgate_classification` returns at least one violation when `E2E automation target` is present but does not match `\d{4}-\d{2}-\d{2}`.
- AC-006 [Pre-gate slugs are exempt from the V-gate check] — verified by T-106, which MUST assert that `_check_vgate_classification` returns zero violations for a spec with `has-user-facing-flow: true` and `E2E gate classification: manual` when the work item slug date predates `_VGATE_GATE_SINCE`.
- AC-007 [Non-playwright profiles are exempt from the V-gate check] — verified by T-107, which MUST assert that `_check_vgate_classification` returns zero violations when test automation profile does not contain the substring `playwright`, regardless of `has-user-facing-flow` value.
- AC-008 [has-user-facing-flow: false is exempt] — verified by T-108, which MUST assert that `_check_vgate_classification` returns zero violations when `has-user-facing-flow: false`, regardless of `E2E gate classification`.
- AC-009 [Metric is emitted to stderr on violation] — verified by T-109, which MUST assert that `sdd_vgate_manual_e2e_violation` appears in captured stderr output when a violation is detected by `_validate_work_item_specs`.
- AC-010 [Blueprint spec template seeds all three new fields] — verified by T-110, which MUST assert that `.spec-kit/templates/blueprint/spec.md` contains `has-user-facing-flow`, `E2E gate classification`, and `E2E automation target` fields in the Implementation Stack Profile section.
- AC-011 [Consumer spec template seeds all three new fields] — verified by T-111, which MUST assert that `.spec-kit/templates/consumer/spec.md` contains all three new fields in the Implementation Stack Profile section.
- AC-012 [AGENTS.md contains mandatory Playwright E2E artifact rule] — verified by T-112, which MUST assert that `AGENTS.md` contains the phrase `has-user-facing-flow` in the testing and quality section.

## Informative Notes (Non-Normative)
- Context: "V-gate" is used informally in issue #353 to denote the E2E verification gate for a user-facing feature. No such named concept previously existed in the blueprint codebase. This work item introduces the concept as three spec fields and one quality-gate check in `check_sdd_assets.py`, following the same machine-enforcement pattern established by `_check_ac_format` and `_check_step03_complete_event` (issue #352).
- Tradeoffs: An explicit `has-user-facing-flow` flag requires author discipline but is deterministic and straightforward to unit-test. Heuristic detection from FR text would require no new field but would produce unpredictable gate behavior on edge-case FR phrasings and would be difficult to cover comprehensively with tests.
- Clarifications:
  - [NEEDS CLARIFICATION: Q-1 — Explicit flag vs heuristic detection. See Normative Option Decision section.]
  - [NEEDS CLARIFICATION: Q-2 — Profile scope: contains "playwright" vs exact string. See Normative Option Decision section.]
  - [NEEDS CLARIFICATION: Q-3 — Date validation depth: format-only vs future-date. See Normative Option Decision section.]

## Explicit Exclusions
- Retroactive enforcement on pre-gate work items: existing specs predating `_VGATE_GATE_SINCE` are grandfathered; no backfill is required.
- Playwright test content validation: this work item does not validate the content or quality of Playwright test files — only that the spec's E2E gate classification field value is correct.
- Playwright test existence check: the check does not verify that a Playwright test file exists on disk — it enforces only the classification field in spec.md.
- Consumer repo retroactive audit: consumer repos already carrying specs with `vitest_playwright_pact` profile are not retroactively broken; the check applies only to new work items whose slug date is on or after `_VGATE_GATE_SINCE`.

## Potential Deferred Proposals
- `automation-target` future-date enforcement: validate that `E2E automation target` is not in the past; deferred because a past date after the target was missed is a governance/escalation concern (step07 triage), not a hard gate failure that blocks ongoing local development.
- Playwright test existence check: machine-verify that at least one `*.spec.ts` or similar file exists when `has-user-facing-flow: true`; deferred because file-existence heuristics require knowing the naming convention and risk false positives for repos that have not yet created tests in the same work item.
- Cross-repo V-gate classification audit report: generate a report listing all specs with their V-gate classification status; deferred — belongs in a dedicated observability or reporting work item.
