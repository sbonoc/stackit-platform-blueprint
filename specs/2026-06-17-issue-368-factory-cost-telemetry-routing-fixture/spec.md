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
- ADR path: docs/blueprint/architecture/decisions/ADR-issue-368-factory-cost-telemetry-routing-fixture.md
- ADR status: approved
- SPEC_READY_EXCEPTION: none
- authorized-by: none

## Applicable Guardrail Controls (Normative)
- Applicable control IDs: SDD-C-001, SDD-C-002, SDD-C-003, SDD-C-004, SDD-C-005, SDD-C-006, SDD-C-007, SDD-C-008, SDD-C-009, SDD-C-010, SDD-C-011, SDD-C-012, SDD-C-013, SDD-C-014, SDD-C-015, SDD-C-016, SDD-C-017, SDD-C-018, SDD-C-019, SDD-C-020, SDD-C-021
- Control exception rationale: none

## Implementation Stack Profile (Normative)
- Backend stack profile: python_plus_fastapi_pydantic_v2
- Frontend stack profile: none
- Test automation profile: pytest_vitest_playwright_pact
- Agent execution model: specialized-subagents-isolated-worktrees
- Managed service preference: stackit-managed-first
- Managed service exception rationale: none
- Runtime profile: local-first-docker-desktop-kubernetes
- Local Kubernetes context policy: docker-desktop-preferred
- Local provisioning stack: crossplane-plus-helm
- Runtime identity baseline: eso-plus-argocd-plus-keycloak
- Local-first exception rationale: none
- Has user-facing flow: false
- E2E gate classification: N/A

## Objective
- Business outcome: First autonomous factory runs produce actionable cost telemetry and a routing-quality signal instead of forcing redesign mid-flight — enabling evidence-based decisions on panel sizing and the substring-vs-embedding routing algorithm.
- Success metric: (1) Per-ticket token/cost roll-up queryable from a single C7 step08 close-out event; (2) ≥ 25 routing fixture rows all pass under the production bigram algorithm on a clean run; (3) cost-ceiling audit predicate triggers on a synthetic over-budget event in test.

## Normative Requirements

### Functional Requirements (Normative)

- FR-001 The orchestrator (#361) MUST emit, on every panel-dispatched C7 event, the extension field `outcome_details.token_usage` containing per-expert token counts — keyed by `expert_slug` — with sub-fields `input_tokens` (integer ≥ 0) and `output_tokens` (integer ≥ 0) for each dispatched expert.
- FR-002 The orchestrator (#361) MUST emit, on every panel-dispatched C7 event, the extension field `outcome_details.merger_overhead` containing: `findings_before_dedup` (integer ≥ 0), `findings_after_dedup` (integer ≥ 0), and `severity_escalation_events` (integer ≥ 0).
- FR-003 The orchestrator (#361) MUST emit, on the step08 close-out C7 event, the extension field `outcome_details.ticket_token_summary` containing: `total_input_tokens` (integer ≥ 0), `total_output_tokens` (integer ≥ 0), and `total_expert_step_instantiations` (integer ≥ 0) rolled up across all panel-dispatched phase events for the same `ticket_id`.
- FR-004 #361's spec MUST declare a per-ticket budget expressed as a cost ceiling (P95 $X USD) and a separate token ceiling (P95 N input tokens), with an audit predicate in `c7_emit.py` or a dedicated audit hook that emits `outcome: rejected` with `rejection_reason: cost-ceiling-exceeded` when the step08 `ticket_token_summary` exceeds the stated ceiling.
- FR-005 The `outcome_details.routing_keys` extension field (already standardized in design-contracts § C7) MUST be populated on ALL panel-dispatched C7 events (not only `phase: agent-pr-review`), so that per-phase model-assignment is auditable across the full SDD lifecycle.
- FR-006 A test module `tests/blueprint/orchestrator/test_step02_routing_fixture.py` MUST be committed under #361's test tree containing ≥ 25 hand-curated `(question_text, expected_expert_set)` pairs covering the recurring step02 question shapes: auth-flow shape, data-flow choices, observability surface decisions, performance vs. cost trade-offs, and rollback design.
- FR-007 The routing fixture MUST execute the production routing algorithm (bigram-overlap per ADR-issue-364 § 4.2) against each `question_text` input and assert the returned expert set equals `expected_expert_set`.
- FR-008 The routing fixture MUST be structured so that a single threshold check — `fraction_failing = failing_rows / total_rows >= 0.20` — constitutes the unblock trigger for upgrading to embedding-match routing (ADR-issue-364 § 4.2 follow-up). The fixture module MUST expose a `EMBEDDING_UPGRADE_THRESHOLD = 0.20` constant and document the trigger meaning in a module-level docstring.

### Non-Functional Requirements (Normative)

- NFR-SEC-001 Token-count and cost data MUST NOT include prompt content or any personally identifiable information. Only integer counters, routing keys, and slug identifiers SHALL appear in C7 extension fields.
- NFR-OBS-001 The `ticket_token_summary` roll-up MUST be emittable from a single C7 event query by `ticket_id` and `phase: agent-pr-review` without joining across phase events. All per-expert token counts per phase MUST be queryable via the phase events alone.
- NFR-REL-001 If token-count metadata is unavailable for a dispatched expert (LiteLLM API returns no usage block), the orchestrator MUST record `input_tokens: -1, output_tokens: -1` for that expert and MUST NOT fail the phase emission. The `ticket_token_summary` computation MUST treat `-1` values as `0` for aggregation (conservative undercount, not a hard failure).
- NFR-OPS-001 The cost-ceiling audit predicate MUST be runnable as a standalone CLI invocation (`uv run python3 scripts/bin/sdd/c7_emit.py audit-cost --ticket <id>`) that exits non-zero when the ceiling is exceeded, enabling CI integration without a full orchestrator stack.
- NFR-A11Y-001 N/A — no user-facing flow.

## Normative Option Decision
- Option A: Inline per-expert token counts directly on each C7 event's `outcome_details` as a sibling map (keyed by `expert_slug`), plus a roll-up on step08.
- Option B: Emit one C7 event per expert invocation (not per phase), with token counts on individual events; derive roll-ups at query time.
- Selected option: OPTION_A
- Rationale: Option B multiplies C7 event volume by ~36× per ticket, breaking the sealed three-emitter rule's phase-boundary anchor (one event per skill execution). Option A preserves the sealed contract, keeps dashboards queryable without joins, and matches the existing `outcome_details.expert_verdicts[]` extension pattern already ratified in design-contracts § C7.

## Contract Changes (Normative)
- Config/Env contract: none
- API contract: none
- OpenAPI / Pact contract path: none
- Event contract: design-contracts § C7 extension-field vocabulary gains three new standardized rows: `outcome_details.token_usage` (all panel-dispatched events), `outcome_details.merger_overhead` (all panel-dispatched events), `outcome_details.ticket_token_summary` (step08 close-out events). The existing `outcome_details.routing_keys` scope is widened from `phase: agent-pr-review` only to all panel-dispatched phases. These are additive extension fields — pre-existing subscribers MUST NOT reject events that include them; new subscribers MUST NOT reject events that omit them.
- Make/CLI contract: `uv run python3 scripts/bin/sdd/c7_emit.py audit-cost --ticket <id>` — new CLI sub-command.
- Docs contract: design-contracts § C7 extension-field table updated; ADR-issue-368 drafted.

## Blueprint Upstream Defect Escalation (Normative)
- Upstream issue URL: none
- Temporary workaround path: none
- Replacement trigger: none
- Workaround review date: none

## Normative Acceptance Criteria

- AC-001 [Token-usage extension on all panel events] — verified by T-101, which MUST assert that a simulated panel-dispatched C7 event produced by the orchestrator test harness contains `outcome_details.token_usage` with one entry per dispatched expert slug, each having `input_tokens >= 0` and `output_tokens >= 0` (or `= -1` for the unavailable-usage case), and that the event passes C7 schema validation.
- AC-002 [Merger-overhead extension on all panel events] — verified by T-101, which MUST assert that the same simulated event carries `outcome_details.merger_overhead` with `findings_before_dedup >= findings_after_dedup >= 0` and `severity_escalation_events >= 0`.
- AC-003 [Step08 ticket roll-up] — verified by T-102, which MUST assert that after injecting synthetic per-phase token-usage events for a test ticket_id, the step08 roll-up `ticket_token_summary.total_input_tokens` equals the arithmetic sum of all per-expert input_tokens across all phases (excluding -1 sentinel values) for that ticket_id.
- AC-004 [Cost-ceiling audit predicate] — verified by T-103, which MUST assert that `c7_emit.py audit-cost --ticket <synthetic-id>` exits with code 1 and emits `rejection_reason: cost-ceiling-exceeded` when injected with a `ticket_token_summary` that exceeds the declared ceiling, and exits with code 0 for a synthetic in-budget ticket.
- AC-005 [routing_keys on all panel events] — verified by T-101, which MUST assert that panel-dispatched events at phases other than `agent-pr-review` also carry `outcome_details.routing_keys` as a non-empty list of LiteLLM routing-key strings.
- AC-006 [Routing fixture ≥ 25 rows, all pass] — verified by T-104, which MUST assert that `uv run python3 -m pytest tests/blueprint/orchestrator/test_step02_routing_fixture.py` exits with code 0, collects ≥ 25 parametrized test rows, and reports zero failures on a clean HEAD of #361's implementation branch.
- AC-007 [Embedding-upgrade threshold constant] — verified by T-104, which MUST assert that `test_step02_routing_fixture.EMBEDDING_UPGRADE_THRESHOLD == 0.20` and that the module docstring contains the substring `embedding-match` so the trigger meaning is discoverable.
- AC-008 [design-contracts § C7 table updated] — verified by T-201, which MUST assert that `docs/blueprint/autonomous-factory/design-contracts.md` contains the three new extension-field rows (`outcome_details.token_usage`, `outcome_details.merger_overhead`, `outcome_details.ticket_token_summary`) after the existing `outcome_details.routing_keys` row, and that the `outcome_details.routing_keys` row description no longer restricts scope to `phase: agent-pr-review` only.

## Informative Notes (Non-Normative)
- Context: Issue #368 is a direct post-#364 follow-up; the two operational risks (token-budget reality, step02 routing quality) were explicitly held out of #364's scope because they require runtime telemetry from #361 before designing against real data. This work lands those gaps before the first autonomous run. All deliverables are scoped to #361's implementation workspace.
- Tradeoffs: The per-ticket roll-up on step08 (FR-003) requires the orchestrator to retain a running accumulator across all prior phase events for the same ticket_id. The alternative (query-time join) was rejected per NFR-OBS-001 (single-event queryability). The accumulator is bounded per-ticket and cleared on completion.
- Clarifications:
  - Budget ceiling decision (Q-1, resolved PR #371 comment by sbonoc, 2026-06-17): Option A selected — ship placeholder ceilings ($5 USD / 500K input tokens) in #361's spec so the audit predicate executes from day one and produces a visible signal on first run. The ceiling is a named Python constant in `c7_emit.py`; calibration to measured actuals after the first 3 autonomous runs is a one-liner chore commit, not a schema or ADR change. FR-004 and plan.md Slice 3 are updated to reflect this decision.

## Explicit Exclusions
- Embedding-based router implementation: only the evidence-gathering fixture is in scope; the embedding-match router itself is a follow-up unblocked by fixture failure rates.
- Per-expert prompt-cache discipline: tracked separately in ADR-issue-364 § 11 Future Work.
- Cost telemetry UI or dashboard: this work only standardizes the C7 extension fields; dashboard authoring is a separate consumer concern.
- UX/UI expert persona (#369): blocked on #361 conditional dispatch gate; explicitly out of scope.

## Potential Deferred Proposals
- Embedding-based router (ADR-issue-364 § 4.2): deferred — this work produces the fixture that triggers the upgrade decision; implementation follows only if ≥ 20% of fixture rows fail under bigram routing.
- Per-expert prompt-cache efficiency (ADR-issue-364 § 11): deferred — prompt-cache discipline for Opus-tier experts could meaningfully reduce cost; surfaces after first telemetry run establishes baseline.
- Cost telemetry consumer dashboard: deferred — downstream of C7 ingest (#350); no consumer has requested a dashboard UI yet.
