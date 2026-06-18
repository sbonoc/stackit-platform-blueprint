# Traceability Matrix

## Requirement-to-Delivery Mapping

| Requirement ID | Control IDs | WCAG SC | Design Element | Implementation Path(s) | Test Evidence | Documentation Evidence | Operational Evidence |
|---|---|---|---|---|---|---|---|
| FR-001 | SDD-C-005, SDD-C-006 | N/A | `architecture.md` § Bounded Contexts and Responsibilities; ADR-issue-361 § Decision (5-child table) | GitHub issues `#361.1`, `#361.2`, `#361.3`, `#361.4`, `#361.5` (filed per T-001) | T-001 manual evidence (GitHub issue links recorded in `pr_context.md`) | `specs/2026-06-18-issue-361-orchestrator-service/spec.md` § FR-001 | parent `#361` Integration AC tick log |
| FR-002 | SDD-C-005 | N/A | `architecture.md` § Domain layer (DispatchMatrix); ADR-issue-361 § Decision | `#361.1` source paths (deferred to child intake) | `#361.1` unit + contract tests (AC-001) | `docs/blueprint/autonomous-factory/design-contracts.md` § C3 (source-of-truth) | runbook entry deferred to `#361.3` `orchestrator.md` |
| FR-003 | SDD-C-005 | N/A | `architecture.md` § Domain layer (ConvergenceEngine); ADR-issue-361 § Decision; ADR-issue-364 § 4 / § 5 | `#361.1` source paths | `#361.1` unit tests (AC-002) | ADR-issue-364 § 4 / § 5 | N/A |
| FR-004 | SDD-C-005 | N/A | `architecture.md` § Domain layer (SchemaValidator); ADR-issue-361 § Decision | `#361.1` source paths | `#361.1` unit + integration tests (AC-003) | `docs/blueprint/architecture/decisions/ADR-issue-337-c7-emission-mechanism.md` § Skill output contract | log fields `decision_summary: schema-validation-failed` (NFR-OBS-001) |
| FR-005 | SDD-C-009, SDD-C-010 | N/A | `architecture.md` § Application layer (C7Emitter); ADR-issue-361 § Decision | `#361.2` source paths | `#361.2` unit + contract tests (AC-004) | `docs/blueprint/autonomous-factory/design-contracts.md` § C7 sealed schema | C7 events on durable bus carry deterministic `event_id` |
| FR-006 | SDD-C-010 | N/A | `architecture.md` § Domain layer (TicketTokenAccumulator + ConvergenceEngine merger_overhead) | `#361.2` source paths | `#361.2` unit tests (AC-004 panels d–g) | ADR-issue-368 § extension-field table | `outcome_details.token_usage` per panel-dispatched event |
| FR-007 | SDD-C-009 | N/A | `architecture.md` § Application layer (ReviewerRotationPicker) | `#361.2` source paths | `#361.2` unit + integration tests (AC-006) | `docs/blueprint/architecture/decisions/ADR-issue-337-reviewer-model-heterogeneity.md` | C7 `phase: agent-pr-review` events carry heterogeneous `outcome_details.routing_keys[]` |
| FR-008 | SDD-C-013 | N/A | `architecture.md` § Infrastructure adapters (RabbitMqTriggerSubscriber, OpenHandsAgentServerClient) | `#361.3` source paths | `#361.3` integration tests (AC-005) | `docs/blueprint/autonomous-factory/orchestrator.md` (authored in `#361.3`) | trigger-accepted message ack discipline in the work loop logs |
| FR-009 | SDD-C-009 | N/A | `architecture.md` § Infrastructure adapters (EsoSecretVolumeReader); ADR-issue-361 § Decision | `#361.4` source paths (Helm chart values + ESO `ExternalSecret`) | `#361.4` integration tests (AC-007 part b/c) | Helm chart `values.yaml` schema | mounted volume paths in the pod spec |
| FR-010 | SDD-C-013 | N/A | `architecture.md` § Context D — Deployment surface | `scripts/templates/infra/orchestrator/` (authored in `#361.4`) | `#361.4` Helm template + kind-cluster integration tests (AC-007) | `docs/blueprint/autonomous-factory/design-contracts.md` § C8 (new row authored in `#361.4`) | Helm release status |
| FR-011 | SDD-C-009 | N/A | `architecture.md` § Non-Functional Architecture Notes (Security) | `#361.4` `NetworkPolicy` manifest | `#361.4` integration tests (AC-007 part c) | Helm chart `templates/networkpolicy.yaml` | denied egress probe evidence |
| FR-012 | SDD-C-005, SDD-C-006 | N/A | `architecture.md` § Domain layer (PredicateRegistry) + § Context E (ux-ui-designer + matrix wiring) | `#361.1` (predicate-registry mechanism) + `#361.5` (PERSONA.md + C3 matrix wiring + `#369` closure) | `#361.1` unit tests + cross-child integration test (AC-009) | `.agents/personas/ux-ui-designer/PERSONA.md` (authored in `#361.5`); `docs/blueprint/autonomous-factory/design-contracts.md` § C3 updated rows (in `#361.5`) | C7 `expert_verdicts[]` rows include or omit `ux-ui-designer` per predicate |
| FR-013 | SDD-C-016 | N/A | ADR-issue-361 § Decision; Contract C4 | parent `#361` GitHub issue body updated at T-002 | parent Integration AC manual ticking by human bounded-context reviewer | `docs/blueprint/autonomous-factory/design-contracts.md` § C4 | parent close audit log |
| NFR-SEC-001 | SDD-C-009 | N/A | `architecture.md` § Non-Functional Architecture Notes (Security) | `#361.4` Helm chart `securityContext` + ESO wiring | `#361.4` integration tests (AC-007 part b) | Helm chart `templates/deployment.yaml` securityContext block | pod spec audit |
| NFR-OBS-001 | SDD-C-010 | N/A | `architecture.md` § Non-Functional Architecture Notes (Observability) | `#361.1` + `#361.2` + `#361.3` log helpers + `#361.2` metric registrations | per-child unit tests for log field presence | `docs/blueprint/autonomous-factory/orchestrator.md` § Observability | structured JSON logs + Prometheus `/metrics` scrape evidence |
| NFR-REL-001 | SDD-C-011 | N/A | `architecture.md` § Non-Functional Architecture Notes (Reliability and rollback) | `#361.2` `TicketTokenAccumulator.rebuild_from_bus`; `#361.4` Helm `strategy.rollingUpdate` | `#361.2` unit tests for rebuild path; `#361.4` Helm rollback smoke | Helm chart `strategy.rollingUpdate` config | rolling-update logs |
| NFR-OPS-001 | SDD-C-013 | N/A | `architecture.md` § Non-Functional Architecture Notes (Monitoring/alerting) | `#361.4` Helm `livenessProbe` / `readinessProbe`; `#361.3` `orchestrator.md` runbook entries | `#361.4` integration tests for probe endpoints | `docs/blueprint/autonomous-factory/orchestrator.md` § Runbook | probe success rate in metrics |
| NFR-A11Y-001 | SDD-C-019 | N/A | spec § NFR-A11Y-001 ("N/A — headless orchestrator service with no UI surface") | N/A | T-A01 declaration | spec § NFR-A11Y-001 | N/A |
| AC-001 | SDD-C-012 | N/A | `architecture.md` § Domain layer (DispatchMatrix) | `#361.1` source paths | `#361.1` unit test `T-101` | spec § AC-001 | startup log on matrix-load |
| AC-002 | SDD-C-012 | N/A | `architecture.md` § Domain layer (ConvergenceEngine) | `#361.1` source paths | `#361.1` unit test `T-102` | spec § AC-002 | convergence outcome counter (NFR-OBS-001) |
| AC-003 | SDD-C-012 | N/A | `architecture.md` § Domain layer (SchemaValidator) | `#361.1` source paths | `#361.1` unit + integration test `T-103` | spec § AC-003 | schema-validation failure counter |
| AC-004 | SDD-C-012 | N/A | `architecture.md` § Application layer (C7Emitter) | `#361.2` source paths | `#361.2` unit + contract test `T-104` | spec § AC-004 | C7 event on durable bus |
| AC-005 | SDD-C-012, SDD-C-016 | N/A | ADR-issue-361 § Decision (parent integration AC) | `#361.3` cross-child integration test `T-201` | `T-201` integration suite | spec § AC-005 | C7 phase-event count per work item |
| AC-006 | SDD-C-012, SDD-C-016 | N/A | `architecture.md` § Application layer (ReviewerRotationPicker) | `#361.3` cross-child integration test `T-202` | `T-202` integration suite | spec § AC-006 | `routing_keys[]` heterogeneity audit |
| AC-007 | SDD-C-012, SDD-C-016 | N/A | `architecture.md` § Context D | `#361.4` cross-child integration test `T-203` | `T-203` Helm + kind-cluster suite | spec § AC-007 | Helm release + NetworkPolicy probe |
| AC-008 | SDD-C-012, SDD-C-016 | N/A | `architecture.md` § Application layer + § Infrastructure adapters | `#361.3` cross-child integration test `T-204` | `T-204` integration suite | spec § AC-008 | reject-counter increment vs FR-008 rerun cap |
| AC-009 | SDD-C-012, SDD-C-016 | N/A | `architecture.md` § Domain layer (PredicateRegistry) + § Context E | `#361.5` cross-child integration test `T-205` | `T-205` integration suite | spec § AC-009 | `expert_verdicts[]` audit per predicate |

## Graph Linkage
- Graph file: `graph.json`
- Every `FR-###`, `NFR-*-###`, and `AC-###` listed in this file MUST have a corresponding node in `graph.json`.
- Node IDs referenced:
  - FR-001, FR-002, FR-003, FR-004, FR-005, FR-006, FR-007, FR-008, FR-009, FR-010, FR-011, FR-012, FR-013
  - NFR-SEC-001, NFR-OBS-001, NFR-REL-001, NFR-OPS-001, NFR-A11Y-001
  - AC-001, AC-002, AC-003, AC-004, AC-005, AC-006, AC-007, AC-008, AC-009

## Validation Summary
- Required bundles executed: `make quality-sdd-check`, `make quality-hardening-review`, `make docs-build`, `make docs-smoke`
- Result summary: <run at Step 7 pre-publish>
- Documentation validation:
  - `make docs-build`
  - `make docs-smoke`

## Evidence Manifest
- Manifest file: `evidence_manifest.json`
- Context export: `context_pack.md`
- PR context export: `pr_context.md`
- Hardening review export: `hardening_review.md`

## Open Risks and Follow-Ups
- Follow-up 1: `#361.3` filing waits on `#335` + `#336` spec-complete (Q-1 resolution). Track via parent issue body checkbox.
- Follow-up 2: `ux-ui-designer` expert raises standing roster to 9 vs ADR-issue-364 ceiling of 8. Architecture sign-off is the human approval surface; FR-012 predicate is the conditioning safety property.
- Follow-up 3: Embedding-based finding dedup (ADR-issue-364 § 11) and per-expert prompt-cache discipline (ADR-issue-368) remain as parked backlog entries on `on-scope: factory` trigger.
