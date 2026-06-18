# PR Context

## Summary
- Work item: 2026-06-17-issue-368-factory-cost-telemetry-routing-fixture
- Objective: Land two operational gaps identified during #364 PR review before the first autonomous factory run: (1) standardize three new additive C7 extension fields (`outcome_details.token_usage`, `outcome_details.merger_overhead`, `outcome_details.ticket_token_summary`) so per-ticket token cost is queryable from a single step08 event without joins; widen `outcome_details.routing_keys` scope to all panel-dispatched phases; and (2) specify and document the step02 routing-quality fixture (`test_step02_routing_fixture.py`) that serves as the canonical signal for the bigram-vs-embedding routing algorithm decision.
- Scope boundaries: The blueprint-repo deliverable is the design-contracts § C7 amendment + ADR (Slice 1). Slices 2–4 (orchestrator token accumulation, `audit-cost` CLI sub-command, routing fixture) land in #361's implementation workspace and reference this spec.

## Requirement Coverage

| Requirement | Design element | Implementation path | Test evidence |
|---|---|---|---|
| FR-001 | `outcome_details.token_usage` C7 extension field | `docs/blueprint/autonomous-factory/design-contracts.md` § C7 (new row) | `test_design_contracts_c7_extension_fields_issue368.py::C7TokenUsageExtensionFieldTests` (5 assertions) |
| FR-002 | `outcome_details.merger_overhead` C7 extension field | `docs/blueprint/autonomous-factory/design-contracts.md` § C7 (new row) | `test_design_contracts_c7_extension_fields_issue368.py::C7MergerOverheadExtensionFieldTests` (5 assertions) |
| FR-003 | `outcome_details.ticket_token_summary` on step08 | `docs/blueprint/autonomous-factory/design-contracts.md` § C7 (new row) | `test_design_contracts_c7_extension_fields_issue368.py::C7TicketTokenSummaryExtensionFieldTests` (6 assertions) |
| FR-004 | `audit-cost` CLI sub-command; `COST_CEILING_USD = 5`, `TOKEN_CEILING_INPUT = 500_000` | `c7_emit.py audit-cost` (Slice 3, #361 workspace) | T-103 in #361 |
| FR-005 | `outcome_details.routing_keys` scope widened | `docs/blueprint/autonomous-factory/design-contracts.md` § C7 (routing_keys row updated) | `test_design_contracts_c7_extension_fields_issue368.py::C7RoutingKeysScopeWideningTests` (3 assertions) |
| FR-006 | Routing fixture ≥ 25 rows | `test_step02_routing_fixture.py` (Slice 4, #361 workspace) | T-104 in #361 |
| FR-007 | Fixture executes production bigram router | `test_step02_routing_fixture.py` imports production router | T-104 in #361 |
| FR-008 | `EMBEDDING_UPGRADE_THRESHOLD = 0.20` + docstring | `test_step02_routing_fixture.py` (Slice 4, #361 workspace) | T-104 in #361 |
| NFR-SEC-001 | Integer-only extension fields, no PII | design-contracts § C7 row descriptions; code review in #361 | T-101 field-content assertions in #361 |
| NFR-OBS-001 | `ticket_token_summary` queryable without joins | JSONL read-back at step08 emit; single-event roll-up | T-102 in #361 |
| NFR-REL-001 | Sentinel -1 on missing LiteLLM usage | design-contracts § C7 token_usage row; orchestrator (Slice 2, #361) | T-101 sentinel path in #361 |
| NFR-OPS-001 | `audit-cost` CLI exits non-zero on breach | `c7_emit.py audit-cost` (Slice 3, #361 workspace) | T-103 in #361 |
| AC-001 | token_usage + merger_overhead + routing_keys schema-valid | Slice 1 (this PR) + Slice 2 (#361) | T-101 in #361; T-201 (this PR — 22 assertions green) |
| AC-002 | merger_overhead present on panel events | Slice 1 + Slice 2 | T-101 in #361 |
| AC-003 | Step08 roll-up arithmetic correct | Slice 2, JSONL read-back | T-102 in #361 |
| AC-004 | audit-cost CLI exit codes correct | Slice 3 | T-103 in #361 |
| AC-005 | routing_keys on all panel phases | Slice 1 (scope widened in this PR) + Slice 2 (#361) | T-101 in #361; T-201 (this PR) |
| AC-006 | Routing fixture ≥ 25 rows, all pass | Slice 4 (#361) | T-104 in #361 |
| AC-007 | EMBEDDING_UPGRADE_THRESHOLD == 0.20 + docstring | Slice 4 (#361) | T-104 in #361 |
| AC-008 | design-contracts § C7 table updated | Slice 1 — `docs/blueprint/autonomous-factory/design-contracts.md` | T-201 (22 assertions, all green) |

- Contract surfaces changed:
  - `docs/blueprint/autonomous-factory/design-contracts.md` § C7 extension-field vocabulary: 4 rows amended/added (`routing_keys` scope widened; `token_usage`, `merger_overhead`, `ticket_token_summary` added)
  - `scripts/templates/blueprint/bootstrap/docs/blueprint/autonomous-factory/design-contracts.md` — auto-synced mirror
  - `docs/blueprint/architecture/decisions/ADR-issue-368-factory-cost-telemetry-routing-fixture.md` — new ADR (approved)
  - `scripts/lib/quality/test_pyramid_contract.json` — T-201 test classified as unit

## Key Reviewer Files

- Primary files to review first:
  - `docs/blueprint/autonomous-factory/design-contracts.md` § C7 (lines ~309–320) — the normative extension-field table; four rows changed/added; this is the contract definition that all orchestrator and subscriber implementations build against
  - `docs/blueprint/architecture/decisions/ADR-issue-368-factory-cost-telemetry-routing-fixture.md` — decision rationale for Deliverable A (inline extension fields vs. per-expert event fan-out) and Deliverable B (fixture as canonical evidence for embedding-upgrade decision)
  - `tests/blueprint/test_design_contracts_c7_extension_fields_issue368.py` — T-201 test suite (22 assertions); the spec-value regression tests per FR-005/FR-008 guardrail for enumerated field names and scope descriptions

- High-risk files:
  - `docs/blueprint/autonomous-factory/design-contracts.md` § C7 `routing_keys` row — the scope change (agent-pr-review only → all panel-dispatched phases) must preserve the FR-008 reviewer-heterogeneity audit predicate semantics; reviewer should confirm the amended row still reads correctly for the step08-specific audit use case
  - `scripts/templates/blueprint/bootstrap/docs/blueprint/autonomous-factory/design-contracts.md` — must remain byte-identical to the source via auto-sync; any manual edit here would break the blueprint-template-drift check

## Validation Evidence

```
# T-201 test suite — 22 assertions, all pass
$ uv run python3 -m pytest tests/blueprint/test_design_contracts_c7_extension_fields_issue368.py -q
22 passed in 0.04s

# quality-sdd-check — pass
$ make quality-sdd-check
[quality-sdd-check] validated SDD assets, readiness gates, and language policy

# quality-docs-check-changed — pass
$ make quality-docs-check-changed
[test-pyramid] ratios unit=97.89% (min>60.00%) integration=1.61% (max<=30.00%) e2e=0.50% (max<=10.00%)
[test-pyramid] OK

# docs-build — pass
$ make docs-build
[SUCCESS] Generated static files in "build".

# docs-smoke — pass
$ make docs-smoke
[METRIC] name=script_duration_seconds value=0 script=docs_smoke status=success

# bootstrap template sync — clean (updated=0)
$ uv run python3 scripts/lib/docs/sync_blueprint_template_docs.py
summary: quality-docs-sync-blueprint-template (created=0 updated=0 removed=0 skipped=17)

# quality-hooks-run strict phase — all checks passed
$ make quality-hooks-run
[INFO] quality hooks strict gate completed
[METRIC] name=quality_hooks_keep_going_total value=1 status=success phase=strict failed_checks=0
```

- Artifact references: `specs/2026-06-17-issue-368-factory-cost-telemetry-routing-fixture/traceability.md`, `artifacts/c7/2026-06-17-issue-368-factory-cost-telemetry-routing-fixture.jsonl`

## Risk and Rollback

- Main risks: all changes are additive C7 extension fields (`additionalProperties: true`); no schema migration required. (1) routing_keys scope widening — pre-#368 orchestrators won't populate the field on non-agent-pr-review events; subscribers MUST NOT reject events that omit it. (2) New rows token_usage/merger_overhead/ticket_token_summary — pre-existing subscribers tolerate inclusion; post-#368 subscribers tolerate omission. (3) Template drift — `sync_blueprint_template_docs.py` auto-sync + blueprint-template-drift hook guard.
- Rollback strategy: `git revert <merge-commit-sha>` removes the three new rows and restores the routing_keys scope restriction; no downstream schema migration. Follow with `uv run python3 scripts/lib/docs/sync_blueprint_template_docs.py` to sync the revert to the bootstrap mirror. No database migration, no feature flag, no infra change.

## Deferred Proposals

1. **Embedding-based router implementation** — Parked. Trigger: `after: issue-368`. The routing fixture (Slice 4, #361) produces the evidence; implementation follows only when ≥ 20% of fixture rows fail under bigram routing. No issue filed — the fixture's `EMBEDDING_UPGRADE_THRESHOLD` assertion is the living trigger.

2. **Per-expert prompt-cache efficiency** — Parked. Trigger: `on-scope: factory`. Prompt-cache discipline for Opus-tier experts could materially reduce cost; surfaces on the next factory-scope work item after first-run telemetry establishes the cost baseline. See ADR-issue-364 § 11 Future Work.

3. **Cost telemetry consumer dashboard** — Parked. Trigger: `after: issue-350`. Downstream of C7 ingest (#350); no consumer has requested a dashboard UI yet.
