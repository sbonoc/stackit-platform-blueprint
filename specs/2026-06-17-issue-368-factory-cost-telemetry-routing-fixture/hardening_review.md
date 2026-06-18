# Hardening Review

## Repository-Wide Findings Fixed

- Finding 1: No pre-existing repository-wide findings were identified or fixed — scope is a docs-layer contract amendment (design-contracts § C7 + ADR) plus a T-201 test suite; no existing code paths were modified. Pre-existing working-tree failures (`make/blueprint.generated.mk` KMS targets, `test_tooling_contracts`, `test_optional_runtime_contract_validation`) are unrelated to this branch, pre-date it, and are not introduced or worsened by this PR.

## Observability and Diagnostics Changes

- **New C7 extension fields** (`outcome_details.token_usage`, `outcome_details.merger_overhead`, `outcome_details.ticket_token_summary`): standardized in design-contracts § C7. These fields make per-ticket token cost and merger dedup overhead queryable from C7 events without additional instrumentation. The implementation (Slices 2–4) lands in #361.
- **`outcome_details.routing_keys` scope widened**: now emitted on all panel-dispatched phases (not only `agent-pr-review`). Enables per-phase model-assignment auditability across the full SDD lifecycle. No new log or metric surface in this blueprint repo.
- **`audit-cost` CLI sub-command** (Slice 3, #361): exits non-zero when the step08 `ticket_token_summary` exceeds the declared ceiling, enabling CI alerting without a dashboard. Implementation in #361.
- No Grafana dashboards, no new alert rules, no new trace spans in this blueprint repo.

## Architecture and Code Quality Compliance

- **SOLID / Clean Architecture / DDD**: this PR delivers only contract documentation (design-contracts.md amendment + ADR) and a document-content test (`test_design_contracts_c7_extension_fields_issue368.py`). No domain, application, or infrastructure code is added in this repo. Clean Architecture layering is not applicable to a documentation-only change.
- **Test pyramid**: 97.89% unit / 1.61% integration / 0.50% e2e — all within bounds. The 22 new assertions are classified as unit tests (document-content grep assertions; no I/O beyond a single file read). `make quality-docs-check-changed` passes.
- **Documentation / diagram / CI / skill consistency**:
  - `docs/blueprint/autonomous-factory/design-contracts.md` § C7 amended; bootstrap template mirror auto-synced via `sync_blueprint_template_docs.py` (updated=1 at implement step; updated=0 at document-sync confirmation). Blueprint-template-drift hook in `make quality-hooks-run` strict phase: pass.
  - `docs/blueprint/architecture/decisions/ADR-issue-368-factory-cost-telemetry-routing-fixture.md` committed and approved; `ADR status: approved` recorded in `spec.md`.
  - Architecture diagrams in `architecture.md` (flowchart TD + sequenceDiagram) accurately reflect the implemented design: JSONL read-back for step08 roll-up, sentinel -1 for missing usage, `c7_emit.py audit-cost` as the sole audit surface.
  - Skill runbooks reference design-contracts § C7 by pointer; no runbook edits required — the widened `routing_keys` scope is documented at the source.
- **Spec-value regression (FR-005/FR-008 guardrails)**: T-201 test suite asserts all three new field row names by exact string (`outcome_details.token_usage`, `outcome_details.merger_overhead`, `outcome_details.ticket_token_summary`), all required sub-field names (`input_tokens`, `output_tokens`, `findings_before_dedup`, `findings_after_dedup`, `severity_escalation_events`, `total_input_tokens`, `total_output_tokens`, `total_expert_step_instantiations`), and the removal of the old `phase: agent-pr-review` scope restriction. All 22 assertions green.

## Accessibility Gate (Normative — non-UI reviewers mark non-applicable items N/A)

- [x] SC 4.1.2 (Name, Role, Value): N/A — no user-facing flow; `has-user-facing-flow: false`
- [x] SC 2.1.1 (Keyboard): N/A — no user-facing flow
- [x] SC 2.4.7 (Focus Visible): N/A — no user-facing flow
- [x] SC 1.4.1 (Use of Color): N/A — no user-facing flow
- [x] SC 3.3.1 (Error Identification): N/A — no user-facing flow
- [x] axe-core WCAG 2.1 AA scan evidence: N/A — no user-facing flow; `NFR-A11Y-001: N/A` declared in spec.md

## Proposals Only (Not Implemented)

- Proposal 1: Embedding-based router implementation — Parked (`after: issue-368`). The routing fixture (Slice 4, #361) is the evidence-gathering mechanism; the embedding-match router ships only when T-104 failure rate ≥ 20%. Not in scope here.
- Proposal 2: Per-expert prompt-cache efficiency — Parked (`on-scope: factory`). Prompt-cache discipline for Opus-tier experts could reduce cost after first-run telemetry establishes baseline. Not in scope here; see ADR-issue-364 § 11.
- Proposal 3: Cost telemetry consumer dashboard — Parked (`after: issue-350`). Downstream of C7 ingest (#350); no consumer need yet.
