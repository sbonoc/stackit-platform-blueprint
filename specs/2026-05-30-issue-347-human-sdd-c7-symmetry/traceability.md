# Traceability Matrix

## Requirement-to-Delivery Mapping

| Requirement ID | Control IDs | WCAG SC | Design Element | Implementation Path(s) | Test Evidence | Documentation Evidence | Operational Evidence |
|---|---|---|---|---|---|---|---|
| FR-001 | SDD-C-003, SDD-C-004, SDD-C-019 | N/A | architecture.md § Bounded Contexts — Context C; ADR § Decision (third sealed emitter) | docs/blueprint/autonomous-factory/design-contracts.md § Contract C7 § Emission mechanism | tests/blueprint/test_design_contracts_schema.py (Slice 1 red→green) | docs/blueprint/architecture/decisions/ADR-issue-347-human-sdd-c7-symmetry.md | none |
| FR-002 | SDD-C-003, SDD-C-004, SDD-C-009 | N/A | architecture.md § Bounded Contexts — Context A (helper sole writer); ADR § Decision (skill-as-tool pattern) | scripts/lib/sdd/c7_emit.py; scripts/bin/sdd/c7_emit.py; .agents/skills/blueprint-sdd-step*/SKILL.md (seven addenda) | tests/sdd/test_c7_emit_unit.py | docs/blueprint/governance/sdd_execution_guide.md (new § C7 Emission for Local SDD Sessions) | helper invocation logs (stderr on failure) |
| FR-003 | SDD-C-003, SDD-C-004 | N/A | architecture.md § High-Level Component Design — Infrastructure adapters (JsonlSinkAdapter) | scripts/lib/sdd/c7_emit.py (JsonlSinkAdapter) | tests/sdd/test_c7_emit_jsonl_round_trip.py | docs/blueprint/governance/sdd_execution_guide.md (sink path documented) | artifacts/c7/<slug>.jsonl committed to branch |
| FR-004 | SDD-C-003, SDD-C-004 | N/A | architecture.md § High-Level Component Design — Domain layer (EventIdDerivation) | scripts/lib/sdd/c7_emit.py (event_id derivation function) | tests/sdd/test_c7_emit_unit.py (byte-for-byte parity with orchestrator hash) | ADR § Decision (four-input variant) + design-contracts.md § Contract C7 | none |
| FR-005 | SDD-C-003, SDD-C-004 | N/A | architecture.md § High-Level Component Design — Application layer (EnvVarModelResolver) | scripts/lib/sdd/c7_emit.py (EnvVarModelResolver + persona-as-skill-basename logic) | tests/sdd/test_c7_emit_unit.py (priority chain) | ADR § Decision (sentinel rules) + design-contracts.md § Contract C7 (persona + model description extensions) | none |
| FR-006 | SDD-C-003, SDD-C-004, SDD-C-010 | N/A | architecture.md § Bounded Contexts — Context C; ADR § Decision (execution_mode discriminator) | scripts/lib/sdd/c7_emit.py (envelope construction); orchestrator + webhook handler emit paths add execution_mode | tests/sdd/test_c7_emit_contract.py (execution_mode preserved on round-trip) | design-contracts.md § Contract C7 (extension-field vocabulary) | Grafana dashboard panel facet |
| FR-007 | SDD-C-003, SDD-C-004, SDD-C-009 | N/A | architecture.md § High-Level Component Design — Application layer (OptOutAuditUseCase) | scripts/lib/sdd/c7_emit.py (OptOutAuditUseCase); blueprint/contract.yaml § spec.spec_driven_development_contract.c7_emission | tests/sdd/test_c7_emit_opt_out.py | docs/blueprint/governance/sdd_execution_guide.md (opt-out behavior); ADR § Decision (default-on with sealed opt-out) | c7-emission-opted-out audit event surfaced on Grafana |
| FR-008 | SDD-C-003, SDD-C-004, SDD-C-009, SDD-C-010 | N/A | architecture.md § Bounded Contexts — Context B (#336 ingest extension); ADR § Decision (webhook handler ingests at PR-event boundaries) | #336 webhook handler — three new event-type handlers + GitHub contents API fetch + dedupe + republish | tests/webhook_handler/test_pr_event_c7_ingest.py | design-contracts.md § Contract C7 § Emission mechanism + ADR § Decision | bus consumer logs |
| FR-009 | SDD-C-003, SDD-C-004, SDD-C-012 | N/A | architecture.md § Bounded Contexts — Context B (dedupe semantics) | #336 webhook handler (dedupe-by-event_id logic) | tests/webhook_handler/test_pr_event_c7_ingest.py (assert zero new emissions on repeat synchronize) | design-contracts.md § Contract C7 § Emission idempotency (existing rule) | bus consumer dedupe metrics |
| FR-010 | SDD-C-003, SDD-C-004, SDD-C-011, SDD-C-019 | N/A | architecture.md § Bounded Contexts — Context C (contract surface ownership) | docs/blueprint/autonomous-factory/design-contracts.md + scripts/templates/blueprint/bootstrap/docs/blueprint/autonomous-factory/design-contracts.md (bootstrap mirror) | reviewer checklist (sealed three-emitter rule + execution_mode + four-input event_id documented); make docs-build | docs/blueprint/autonomous-factory/design-contracts.md (canonical) | none |
| FR-011 | SDD-C-003, SDD-C-004 | N/A | architecture.md § Bounded Contexts — Context C (ADR ownership) | docs/blueprint/architecture/decisions/ADR-issue-347-human-sdd-c7-symmetry.md | reviewer checklist (Status advanced proposed → accepted on merge; four locked decisions D-1..D-4 recorded verbatim) | docs/blueprint/architecture/decisions/ADR-issue-347-human-sdd-c7-symmetry.md | none |
| FR-012 | SDD-C-003, SDD-C-004 | N/A | architecture.md § Bounded Contexts — Context A (helper-and-skill ownership) | .agents/skills/blueprint-sdd-stepXX-*/SKILL.md (all seven runbooks); scripts/templates/consumer/init/.agents/skills/blueprint-sdd-stepXX-*/SKILL.md.tmpl (consumer mirrors) | scripts/bin/quality/check_sdd_assets.py (uniform-addendum byte-identical-modulo-phase-enum check) | each skill runbook contains the addendum | check_sdd_assets.py CI gate |
| FR-013 | SDD-C-003, SDD-C-004 | N/A | architecture.md § Risks and Tradeoffs (Risk 4) | .gitattributes (linguist-generated + diff=none rule) | manual verification on this PR (AC-006) | .gitattributes | none |
| FR-014 | SDD-C-003, SDD-C-004 | N/A | architecture.md § Problem Statement § Scope boundaries (PRs opened after merge only) | none — explicit exclusion; no backfill code | reviewer checklist | spec.md § Explicit Exclusions | none |
| NFR-SEC-001 | SDD-C-009, SDD-C-019 | N/A | architecture.md § Non-Functional Architecture Notes — Security; ADR § Decision (skill-as-tool preserves the sealed-emitter anti-LLM-hallucination property) | scripts/lib/sdd/c7_emit.py is the SOLE writer; skill runbook addendum forbids LLM-side JSONL writes | code review (helper is the only `O_APPEND` writer to `artifacts/c7/`); reviewer checklist | ADR § Decision Drivers + § Decision | none |
| NFR-SEC-002 | SDD-C-009 | N/A | architecture.md § Non-Functional Architecture Notes — Security (no new credential surface); ADR § Decision Drivers | #336 webhook handler (uses existing GitHub App installation token) | code review (no new credential read paths) | ADR § Consequences (no new credential surface) | none |
| NFR-OBS-001 | SDD-C-010 | N/A | architecture.md § Non-Functional Architecture Notes — Observability | Grafana dashboard panel update (Blueprint instance) | manual rehearsal screenshot in pr_context.md (AC-005) | docs/blueprint/autonomous-factory/instrumentation-plan.md (execution_mode facet documented) | Grafana dashboard live |
| NFR-OBS-002 | SDD-C-010 | N/A | architecture.md § Non-Functional Architecture Notes — Observability; ADR § Decision (FR-008 unknown-model exemption) | FR-008 predicate update (existing in #333 — adds exemption branch) | pytest extension in FR-008 predicate's test suite | ADR § Decision + ADR-issue-337-reviewer-model-heterogeneity.md amendment | Grafana surfaces inconclusive count separately |
| NFR-REL-001 | SDD-C-010, SDD-C-012 | N/A | architecture.md § Non-Functional Architecture Notes — Reliability and rollback | scripts/lib/sdd/c7_emit.py (failure path: log + return success) | tests/sdd/test_c7_emit_unit.py (failure path coverage) | docs/blueprint/governance/sdd_execution_guide.md (helper-failure non-blocking) | helper stderr logs |
| NFR-OPS-001 | SDD-C-010, SDD-C-012 | N/A | architecture.md § Non-Functional Architecture Notes — Reliability and rollback (rebase/squash idempotency) | scripts/lib/sdd/c7_emit.py (idempotent append) + #336 dedupe | tests/webhook_handler/test_pr_event_c7_ingest.py (dedupe on duplicate lines) | design-contracts.md § Contract C7 § Emission idempotency | bus consumer dedupe metrics |
| NFR-A11Y-001 | N/A | N/A | N/A — no UI surface | N/A | N/A | spec.md § NFR-A11Y-001 ("N/A — this work item adds no UI surface") | N/A |
| AC-001 | SDD-C-012 | N/A | spec.md § AC-001 (>= 7 events in full lifecycle) | manual rehearsal on a stub work item; pytest integration test fixture | tests/webhook_handler/test_pr_event_c7_ingest.py + manual rehearsal log | pr_context.md (validation evidence) | none |
| AC-002 | SDD-C-012 | N/A | spec.md § AC-002 (schema validation + emitter + execution_mode) | scripts/lib/sdd/c7_emit.py (envelope construction); jsonschema validation in #336 ingest | tests/sdd/test_c7_emit_contract.py | design-contracts.md § Contract C7 (schema) | bus consumer audit |
| AC-003 | SDD-C-012 | N/A | spec.md § AC-003 (dedupe on repeat synchronize) | #336 webhook handler (dedupe-by-event_id) | tests/webhook_handler/test_pr_event_c7_ingest.py | design-contracts.md § Contract C7 § Emission idempotency | bus consumer dedupe metrics |
| AC-004 | SDD-C-012 | N/A | spec.md § AC-004 (opt-out audit event semantics) | scripts/lib/sdd/c7_emit.py (OptOutAuditUseCase) | tests/sdd/test_c7_emit_opt_out.py + #336 integration test | docs/blueprint/governance/sdd_execution_guide.md (opt-out behavior) | Grafana c7-emission-opted-out panel |
| AC-005 | SDD-C-010, SDD-C-012 | N/A | spec.md § AC-005 (Grafana panel facet) | Grafana dashboard panel update | manual rehearsal screenshot attached to pr_context.md | docs/blueprint/autonomous-factory/instrumentation-plan.md (execution_mode facet) | Grafana dashboard live |
| AC-006 | SDD-C-012 | N/A | spec.md § AC-006 (`.gitattributes` diff=none rule hides JSONL) | .gitattributes | manual verification on this PR (screenshot in pr_context.md) | .gitattributes | none |
| AC-007 | SDD-C-012, SDD-C-017 | N/A | spec.md § AC-007 (all quality bundles green) | make quality-sdd-check; make docs-build; make docs-smoke; pytest helper suite | CI output (commit hash + bundle results captured in pr_context.md) | pr_context.md § Validation Evidence | CI green |

## Graph Linkage
- Graph file: `graph.json`
- Every `FR-###`, `NFR-*-###`, and `AC-###` listed in this file MUST have a corresponding node in `graph.json`.
- Node IDs referenced:
  - FR-001, FR-002, FR-003, FR-004, FR-005, FR-006, FR-007, FR-008, FR-009, FR-010, FR-011, FR-012, FR-013, FR-014
  - NFR-SEC-001, NFR-SEC-002
  - NFR-OBS-001, NFR-OBS-002
  - NFR-REL-001, NFR-OPS-001, NFR-A11Y-001
  - AC-001, AC-002, AC-003, AC-004, AC-005, AC-006, AC-007

## Validation Summary
- Required bundles executed: pending implementation (Steps 05–07 will populate)
- Result summary: pending
- Documentation validation:
  - `make docs-build`
  - `make docs-smoke`

## Evidence Manifest
- Manifest file: `evidence_manifest.json`
- Context export: `context_pack.md`
- PR context export: `pr_context.md`
- Hardening review export: `hardening_review.md`

## Open Risks and Follow-Ups
- Follow-up 1: Cross-repo aggregation of consumer-repo C7 events — eligible once `artifacts/c7/*.jsonl` is a stable contract in blueprint repo. Owner: TBD post-merge. Trigger: first consumer adopter requests metrics-dashboard symmetry.
- Follow-up 2: `blueprint-sdd-traceability-keeper` emission (pending Q-6 resolution). If included, requires a new `phase` enum entry — separate #339 amendment cycle.
- Follow-up 3: Consumer-ops skills (`blueprint-consumer-ops`, `blueprint-consumer-upgrade`) emission — different audit surface; out-of-scope here.
- Follow-up 4: Self-bootstrap emission for this work item #347 (pending Q-3 resolution; default excluded).
