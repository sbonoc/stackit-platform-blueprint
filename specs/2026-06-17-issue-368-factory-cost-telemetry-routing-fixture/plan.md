# Implementation Plan

## Implementation Start Gate
- Implementation tasks MUST remain unchecked until `SPEC_READY=true`.
- If required inputs are missing, add `BLOCKED_MISSING_INPUTS` in `spec.md` and keep the gate closed.

## Constitution Gates (Pre-Implementation)
- Simplicity gate:
  - Token-usage accumulation is a running dict keyed by `expert_slug`; no new service or database.
  - The `audit-cost` sub-command reads existing JSONL files; no new storage.
- Anti-abstraction gate:
  - Extend the existing merger return value (dict) with `merger_overhead` keys — no new class.
  - The routing fixture imports the production bigram-router function directly; no mock.
- Integration-first testing gate:
  - T-101 (unit: token-usage + merger-overhead on simulated panel event) written red before orchestrator code changes.
  - T-104 (routing fixture) written against the production router function; the fixture itself IS the test.
- Positive-path filter/transform test gate:
  - FR-007 routing fixture: each row asserts a non-empty `expected_expert_set` for a valid question; at least 5 rows MUST assert multi-expert dispatch (positive-path for multi-match per ADR-issue-364 § 4.2 step 7).
- Finding-to-test translation gate:
  - If a routing fixture row fails under bigram routing, that failure IS the reproducible finding; the fixture itself is the deterministic check. No additional translation needed — the fixture constitutes T-104.

## Delivery Slices

1. Slice 1 — Design-contracts § C7 amendment (red: AC-008 test checking table rows present → green: add rows to design-contracts.md + widen routing_keys scope)
   - Amend `docs/blueprint/autonomous-factory/design-contracts.md` § C7 extension-field vocabulary:
     - Add row `outcome_details.token_usage` after `outcome_details.routing_keys`.
     - Add row `outcome_details.merger_overhead` after `outcome_details.token_usage`.
     - Add row `outcome_details.ticket_token_summary` after `outcome_details.merger_overhead`.
     - Update `outcome_details.routing_keys` description: remove "`phase: agent-pr-review` only" restriction; replace with "all panel-dispatched phases with ≥ 2 experts".
   - ADR-issue-368 is already committed and approved on this branch (status: approved); no draft work required in #361.
   - Blueprint-repo deliverable: this slice is complete when design-contracts.md carries the three rows and T-201 grep passes on this branch.

2. Slice 2 — Orchestrator token-usage accumulation and C7 emission (red: T-101 asserts extension fields present → green: orchestrator merger emits them)
   - Extend merger return value to include `merger_overhead` dict.
   - Accumulate per-expert token counts from LiteLLM `usage` block (sentinel -1 on missing).
   - Add `outcome_details.token_usage`, `outcome_details.merger_overhead`, `outcome_details.routing_keys` (all panels) to C7 envelope construction.
   - At step08 emit time: read all prior phase events for the same `ticket_id` from `artifacts/c7/<slug>.jsonl`; sum per-expert `input_tokens` and `output_tokens` across all `outcome_details.token_usage` entries (treating -1 as 0); count total expert-step instantiations; emit as `outcome_details.ticket_token_summary`. Do NOT use an in-memory accumulator — JSONL read-back ensures reproducibility on retry.

3. Slice 3 — `audit-cost` CLI sub-command (red: T-103 asserts CLI exits non-zero on over-budget → green: implement sub-command)
   - Add `audit-cost` sub-command to `scripts/bin/sdd/c7_emit.py`.
   - Sub-command reads C7 JSONL for `ticket_id`, finds step08 `ticket_token_summary`, compares against ceiling constant.
   - Exits 1 + emits `rejection_reason: cost-ceiling-exceeded` when exceeded; exits 0 otherwise.
   - Pin cost ceiling constant (placeholder: $5 USD / 500K input tokens) with a comment marking it for calibration post-first-run.

4. Slice 4 — Step02 routing fixture (T-104: write ≥ 25 parametrized rows + EMBEDDING_UPGRADE_THRESHOLD constant)
   - Write `tests/blueprint/orchestrator/test_step02_routing_fixture.py` under #361's test tree.
   - Curate ≥ 25 `(question_text, expected_expert_set)` pairs across 5 question-shape categories:
     - Auth-flow shape (≥ 5 rows): questions about OAuth flows, token scopes, session handling — expect `security-paranoid`, `data-privacy`.
     - Data-flow choices (≥ 5 rows): questions about pipeline fan-out, schema evolution, retention — expect `data-privacy`, `boundary-hawk`.
     - Observability decisions (≥ 4 rows): questions about span attributes, alert thresholds — expect `operability-sre`.
     - Performance vs. cost (≥ 5 rows): questions about hot paths, N+1, retry budgets, token cost — expect `performance-cost-aware`.
     - Rollback design (≥ 6 rows): questions about migration reversibility, blue-green, feature flags — expect `operability-sre`, `boundary-hawk`.
   - Expose `EMBEDDING_UPGRADE_THRESHOLD = 0.20` and module docstring.
   - Assert `fraction_failing < EMBEDDING_UPGRADE_THRESHOLD` as a summary assertion so a regression is immediately visible.

## Change Strategy
- Migration/rollout sequence: Slice 1 (docs) → Slice 2 (orchestrator) → Slice 3 (CLI) → Slice 4 (fixture). Each slice is independently committable; downstream slices do not block upstream consumers.
- Workspace boundary: Slice 1 (design-contracts.md + ADR) lands in this blueprint repo on this branch. Slices 2–4 land in #361's implementation workspace; the implementation PR for #361 references this spec.
- Backward compatibility policy: all C7 extension fields are additive (`additionalProperties: true`); pre-#368 subscribers MUST tolerate events that include the new fields; post-#368 subscribers MUST tolerate events that omit them.
- Rollback plan: revert design-contracts amendment (one table-section deletion); revert orchestrator merger changes (remove accumulation dict and emission key); delete `audit-cost` sub-command; delete routing fixture file. No schema migration required.

## Validation Strategy (Shift-Left)
- Unit checks: T-101 (token-usage + merger-overhead on simulated panel event, including sentinel -1 path); T-102 (step08 roll-up arithmetic); T-103 (audit-cost CLI exit codes).
- Contract checks: T-201 (grep design-contracts.md for three new extension-field rows and corrected routing_keys scope).
- Integration checks: T-104 (routing fixture against production router — this IS an integration test, not a mock).
- E2E checks: N/A — no user-facing flow.

## App Onboarding Contract (Normative)
- Required minimum make targets:
  - `apps-bootstrap`
  - `apps-smoke`
  - `backend-test-unit`
  - `backend-test-integration`
  - `backend-test-contracts`
  - `backend-test-e2e`
  - `touchpoints-test-unit`
  - `touchpoints-test-integration`
  - `touchpoints-test-contracts`
  - `touchpoints-test-e2e`
  - `test-unit-all`
  - `test-integration-all`
  - `test-contracts-all`
  - `test-e2e-all-local`
  - `infra-port-forward-start`
  - `infra-port-forward-stop`
  - `infra-port-forward-cleanup`
- App onboarding impact: no-impact
- Notes: this work item adds test files and a CLI sub-command under #361; it does not add or change make targets in this blueprint repo.

## Documentation Plan (Document Phase)
- Blueprint docs updates: design-contracts § C7 extension-field table (Slice 1); ADR-issue-368 (proposed → accepted after sign-off).
- Consumer docs updates: none — extension fields are additive; consumer ingest subscribers need no change.
- Mermaid diagrams updated: architecture.md diagrams in this spec; ADR-issue-368 will include the same flowchart + sequence diagrams.
- Docs validation commands:
  - `make docs-build`
  - `make docs-smoke`

## Publish Preparation
- PR context file: `pr_context.md`
- Hardening review file: `hardening_review.md`
- Local smoke gate (HTTP route/filter changes): not applicable — no HTTP route changes.
- Publish checklist:
  - Requirement/contract coverage: FR-001–FR-008, NFR-*, AC-001–AC-008 all traced in traceability.md.
  - Key reviewer files: design-contracts.md § C7 amendment; ADR-issue-368; test_step02_routing_fixture.py.
  - Validation evidence: T-101–T-104 pass; T-201 grep pass; `make quality-sdd-check` pass.
  - Rollback notes: additive-only; revert is three file deletions + one doc edit.

## Operational Readiness
- Logging/metrics/traces: `audit-cost` sub-command writes to stdout; CI captures exit code. No new persistent log surface in this repo.
- Alerts/ownership: cost-ceiling breach surfaces as CI failure in #361's pipeline; no new alerting system required.
- Runbook updates: none required for this blueprint repo; #361's operational runbook should note the `audit-cost` CLI.

## Risks and Mitigations
- Risk 1 — Placeholder ceiling fires on first real run → mitigation: ceiling is a named Python constant with a calibration comment; updating after first run is a one-liner chore commit in #361 (no schema change, no ADR amendment required).
- Risk 2 — LiteLLM API changes `usage` block field names → mitigation: sentinel -1 path (NFR-REL-001) ensures emission never fails; the undercount signal is visible in the telemetry.
- Risk 3 — Routing fixture rows encode wrong expected_expert_set → mitigation: each row is hand-curated against the production PERSONA.md trigger phrases; a fixture PR review by the author of #364 (sbonoc) catches mismatches before merge.
