# Traceability Matrix

## Requirement-to-Delivery Mapping

| Requirement ID | Control IDs | WCAG SC | Design Element | Implementation Path(s) | Test Evidence | Documentation Evidence | Operational Evidence |
|---|---|---|---|---|---|---|---|
| FR-001 | SDD-C-005 | N/A | `outcome_details.token_usage` C7 extension field | orchestrator merger + C7 envelope construction (Slice 2, T-004) | T-101 | design-contracts § C7 table row | C7 JSONL per-phase |
| FR-002 | SDD-C-005 | N/A | `outcome_details.merger_overhead` C7 extension field | orchestrator merger return value (Slice 2, T-003, T-005) | T-101 | design-contracts § C7 table row | C7 JSONL per-phase |
| FR-003 | SDD-C-005 | N/A | `outcome_details.ticket_token_summary` on step08 | orchestrator per-ticket accumulator (Slice 2, T-007) | T-102 | design-contracts § C7 table row | C7 JSONL step08 |
| FR-004 | SDD-C-010 | N/A | Cost-ceiling audit predicate + ceiling constant | `c7_emit.py audit-cost` sub-command (Slice 3, T-008, T-009) | T-103 | ADR-issue-368 § ceiling-decision | CI exit code |
| FR-005 | SDD-C-005 | N/A | `outcome_details.routing_keys` widened to all panel phases | orchestrator C7 envelope construction (Slice 2, T-006) | T-101 | design-contracts § C7 routing_keys row update | C7 JSONL per-phase |
| FR-006 | SDD-C-012 | N/A | `test_step02_routing_fixture.py` ≥ 25 rows | Slice 4 (T-010) | T-104 | ADR-issue-368 § routing-fixture | — |
| FR-007 | SDD-C-012 | N/A | Routing fixture calls production bigram algorithm | `test_step02_routing_fixture.py` imports production router (T-010) | T-104 | ADR-issue-368 § routing-fixture | — |
| FR-008 | SDD-C-012 | N/A | `EMBEDDING_UPGRADE_THRESHOLD = 0.20` + module docstring | Slice 4 (T-011, T-012) | T-104 | ADR-issue-368 § embedding-upgrade-trigger | — |
| NFR-SEC-001 | SDD-C-009 | N/A | Extension fields carry only integer counters + routing keys | orchestrator C7 envelope construction; code review | T-101 (field content assertions) | ADR-issue-368 § security | C7 JSONL field audit |
| NFR-OBS-001 | SDD-C-010 | N/A | `ticket_token_summary` on step08 queryable without joins | orchestrator accumulator design (T-007) | T-102 | design-contracts § C7 table row | C7 JSONL step08 query |
| NFR-REL-001 | SDD-C-006 | N/A | Sentinel -1 on missing LiteLLM usage | orchestrator token accumulation (T-004) | T-101 (sentinel path) | ADR-issue-368 § reliability | — |
| NFR-OPS-001 | SDD-C-010 | N/A | `audit-cost` CLI exit code | `c7_emit.py audit-cost` (T-008, T-009) | T-103 | ADR-issue-368 § ops | CI pipeline |
| AC-001 | SDD-C-012 | N/A | Token-usage extension on panel events | T-001, T-004 | T-101 | design-contracts § C7 | C7 JSONL |
| AC-002 | SDD-C-012 | N/A | Merger-overhead extension on panel events | T-001, T-003, T-005 | T-101 | design-contracts § C7 | C7 JSONL |
| AC-003 | SDD-C-012 | N/A | Step08 ticket roll-up arithmetic | T-007 | T-102 | design-contracts § C7 | C7 JSONL |
| AC-004 | SDD-C-012 | N/A | Cost-ceiling audit CLI exits 1 on breach | T-008, T-009 | T-103 | ADR-issue-368 | CI |
| AC-005 | SDD-C-012 | N/A | routing_keys on all panel phases | T-006 | T-101 | design-contracts § C7 | C7 JSONL |
| AC-006 | SDD-C-012 | N/A | Routing fixture ≥ 25 rows all pass | T-010 | T-104 | ADR-issue-368 | — |
| AC-007 | SDD-C-012 | N/A | EMBEDDING_UPGRADE_THRESHOLD == 0.20 + docstring | T-011, T-012 | T-104 | ADR-issue-368 | — |
| AC-008 | SDD-C-012 | N/A | design-contracts.md § C7 table updated | T-001 | T-201 | design-contracts.md diff | — |

## Graph Linkage
- Graph file: `graph.json`
- Every `FR-###`, `NFR-*-###`, and `AC-###` listed in this file MUST have a corresponding node in `graph.json`.
- Node IDs referenced:
  - FR-001, FR-002, FR-003, FR-004, FR-005, FR-006, FR-007, FR-008
  - NFR-SEC-001, NFR-OBS-001, NFR-REL-001, NFR-OPS-001
  - AC-001, AC-002, AC-003, AC-004, AC-005, AC-006, AC-007, AC-008

## Validation Summary
- Required bundles executed: (to be completed at implementation phase)
- Result summary: (to be completed at implementation phase)
- Documentation validation:
  - `make docs-build`
  - `make docs-smoke`

## Evidence Manifest
- Manifest file: `evidence_manifest.json`
- Context export: `context_pack.md`
- PR context export: `pr_context.md`
- Hardening review export: `hardening_review.md`

## Open Risks and Follow-Ups
- Follow-up 1: Calibrate per-ticket budget ceiling constant in #361 after first 3 autonomous runs produce measured actuals (chore-track, no ADR amendment required).
- Follow-up 2: If routing fixture failure rate ≥ 20% under bigram algorithm, escalate to embedding-match routing implementation (ADR-issue-364 § 4.2 follow-up, tracked by fixture EMBEDDING_UPGRADE_THRESHOLD assertion).
