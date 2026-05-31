# Architecture

## Context
- Work item: 2026-05-31-issue-352-sdd-step03-step05-drift-loop
- Owner: platform-team (single maintainer per `feedback_solo_operator_topology`)
- Date: 2026-05-31

## Stack and Execution Model
- Backend stack profile: python_plus_fastapi_pydantic_v2
- Frontend stack profile: vue_router_pinia_onyx
- Test automation profile: pytest_vitest_playwright_pact
- Agent execution model: specialized-subagents-isolated-worktrees

## Problem Statement
- What needs to change and why: Six structural gaps between step03 (spec authoring) and step05 (implementation) let spec-to-implementation drift survive every automated gate. The fix is a single closed loop covering all six gaps in one work item; removing any one leaves a bypass or blind spot per the issue body.
- Scope boundaries: AGENTS.md `§ Mandatory Workflow`, `.agents/skills/blueprint-sdd-step03-spec-complete/SKILL.md`, `.agents/skills/blueprint-sdd-step05-implement/SKILL.md`, `scripts/bin/quality/check_sdd_assets.py`, and accompanying pytest fixtures + tests. ADR addition.
- Out of scope: `blueprint/contract.yaml` (no contract field changes); generated-consumer files (skill runbook propagation only); retroactive remediation of existing work items.

## Bounded Contexts and Responsibilities
- **SDD Governance (AGENTS.md)** — owns the policy text declaring step03 as a mandatory gate and listing exempt tracks. Source of truth for the rule.
- **SDD Validation (`scripts/bin/quality/check_sdd_assets.py`)** — owns the FR-002 machine enforcement: reads `artifacts/c7/<slug>.jsonl`, asserts a `spec-complete` event exists, honours FR-003 exemptions. Source of truth for enforcement behaviour.
- **Step03 Skill Runbook** — owns the AC-authoring requirement (FR-004) and surfaces the rejection rule for label-only ACs at spec-complete time.
- **Step05 Skill Runbook** — owns guardrails FR-005..FR-010 and the per-profile examples table.
- **C7 Emission Library (`scripts/lib/sdd/c7_emit.py`)** — UNCHANGED by this work item. The `spec-complete` phase already exists in the `_PHASES` enum (verified during intake). FR-002 reads the existing event; no new emission path is added.

## High-Level Component Design
- **Domain layer** (governance text):
  - AGENTS.md `§ Mandatory Workflow` — add mandatory-gate clause + exempt-track list.
  - SKILL.md runbook updates — text-only changes to authoring rules and guardrails.
- **Application layer** (validation logic):
  - `check_sdd_assets.py` — new `_check_step03_complete_event(work_item_dir, spec_data)` function called from the existing implementation-ready validator path. Reads `artifacts/c7/<slug>.jsonl`, parses each line as JSON, filters by `phase == "spec-complete"` AND `ticket_id == <ticket>`. Honours FR-003 exemption gates before performing any I/O.
- **Infrastructure adapters**: none — file I/O via stdlib only; JSON validation via stdlib `json` (no Pydantic dependency added to the check script).
- **Presentation/API/workflow boundaries**: `make quality-sdd-check` is the single CLI surface. Error message format follows the existing `SPEC_READY_EXCEPTION` audit-metric pattern.

## Integration and Dependency Edges
- Upstream dependencies:
  - C7 JSONL sink format (ADR-issue-347-human-sdd-c7-symmetry): the JSONL file format is treated as a stable interface. `check_sdd_assets.py` consumes `phase`, `ticket_id`, `event_id` fields. The sink is committed to the work-item branch and travels with the PR (no network fetch required).
  - C7 phase enum (`scripts/lib/sdd/c7_emit.py` `_PHASES`): the value `"spec-complete"` is treated as a sealed enum member; if it ever changes, FR-002 enforcement breaks. Cross-reference comment added in the check script.
- Downstream dependencies:
  - Existing SDD work items in flight: FR-011 grandfathers them — the new check runs only on work items whose spec-scaffold timestamp is on or after merge.
  - Generated consumer repos: receive the new SKILL.md text via standard skill propagation; consumer-side `make quality-sdd-check` inherits the FR-002 enforcement when the blueprint is upgraded.
- Data/API/event contracts touched: none (only `make quality-sdd-check` output format gains the NFR-OBS-001 metric line — additive).

## Non-Functional Architecture Notes
- Security: no new attack surface; FR-002 reads a file already in the work tree and writes nothing.
- Observability: NFR-OBS-001 metric line (`[METRIC] name=sdd_step03_missing_spec_complete value=1 work_item=<slug>`) follows the existing `sdd_exception_gate_total` pattern so CI log scrapers need no new parsers.
- Reliability and rollback: rollback is a clean revert of this work item's commits. No persistent state migration. NFR-REL-001 ensures a malformed JSONL produces a clear error rather than a crash.
- Monitoring/alerting: no alerting wiring — failure mode is a `make quality-sdd-check` non-zero exit at PR-CI time, surfaced to the contributor via the existing CI status check.

## Risks and Tradeoffs
- Risk 1 — Contributors with legitimate local-only SDD work who run `BLUEPRINT_SDD_C7_EMIT=0` will hit the gate when they try to merge.
  Mitigation: FR-003 keeps the exempt tracks unchanged; opt-out users on full-SDD must run step03 to record `spec-complete` (or set the appropriate `SPEC_READY_EXCEPTION` value). Documented in the failure message.
- Risk 2 — FR-006/FR-007 union-type and SSOT mandates are stack-agnostic but the existing per-stack idioms differ. Mis-application across stacks could produce noise.
  Mitigation: FR-010 mandates a per-profile examples table in the SKILL.md so contributors copy from canonical idioms instead of re-deriving them.
- Tradeoff — FR-001 raises the bar for bug-fix/refactor/chore-with-specs (they must now run step03 to record a `spec-complete` event). Cost: one extra skill invocation per non-feature work item. Benefit: closes the loophole where a contributor manually edits sign-off fields without running step03, defeating the gate intent.
- Tradeoff — FR-009 (Vitest Browser Mode satisfies FR-008) keeps the cost low for single-component rendering changes; the Playwright escalation rule only triggers for true multi-route flows. Accepted to avoid pushing past the `e2e ≤ 10%` pyramid ratio (AGENTS.md § Testing and Quality Ratios) for small features.

## ADR Reference
- Path: `docs/blueprint/architecture/decisions/ADR-issue-352-sdd-step03-step05-drift-loop.md` — Status: proposed
