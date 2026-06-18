# Implementation Plan

## Implementation Start Gate
- Implementation tasks MUST remain unchecked until `SPEC_READY=true`.
- If required inputs are missing, add `BLOCKED_MISSING_INPUTS` in `spec.md` and keep the gate closed.

## Constitution Gates (Pre-Implementation)
- Simplicity gate:
  - Initial implementation ships single-replica orchestrator with naive string-equality finding dedup; horizontal scaling and embedding-based dedup are explicitly deferred.
  - Convergence engine ships only the three modes documented in ADR-issue-364 § 4 / § 5; no speculative future modes.
- Anti-abstraction gate:
  - Use stdlib `hashlib.sha256` directly for `event_id` derivation; no wrapper crypto layer.
  - Use `jsonschema` library directly for validation; do not introduce a custom abstraction layer over draft-07.
  - Use `pika` (or `aio-pika`) directly for AMQP; do not wrap in a generic "bus client" abstraction.
- Integration-first testing gate:
  - Contract test against `docs/blueprint/autonomous-factory/design-contracts.md` § C3 markdown shape (the matrix loader's source of truth).
  - Contract test against the C7 sealed eleven-field schema in § C7 (the emitter's output shape).
  - Integration tests use a kind-cluster fixture for `#361.4` Helm install + NetworkPolicy probe.
- Positive-path filter/transform test gate:
  - N/A — no HTTP route or filter/payload-transform logic in this work item.
- Finding-to-test translation gate:
  - Any reproducible pre-PR finding from manual checks (e.g., dispatch matrix loader rejects a fixture that should pass) MUST be translated into a failing automated test first.
  - The implementation fix MUST turn that test green in the same work item.

## Delivery Slices

**Step04 plan-slicer skip rationale (2026-06-18).** The `blueprint-sdd-step04-plan-slicer` skill was deliberately SKIPPED for this work item, per the skill's own runbook permission: "Skip this step for straightforward work items where `plan.md` from Step 1 is already clear and actionable." Three reasons:
1. This parent coordination spec's actual implementation surface is small — 2 idempotent bash scripts + 1 pytest + the spec artifact set. No runtime orchestrator code lands here; all of that lives in the 5 children.
2. The meaningful slicing already happened at parent intake — FR-001 and ADR § Decision table decompose `#361` into 5 children along layer/feature/governance-docs boundaries. Re-slicing the parent's own tiny implementation into more granular slices would be ceremony without information gain.
3. Each child runs its own SDD lifecycle including its own step04 plan-slicer pass against its own scope; that is where dependency-ordered execution sequencing belongs.
A `phase: plan-slicer` C7 audit event is emitted with `outcome: success` so the audit trail shows this step was considered and deliberately skipped, not forgotten.

The 5 child work items (`#361.1` … `#361.5`) each carry their own delivery slices in their own `spec.md` + `plan.md`. The parent slice plan below sequences the **parent coordination work** that lands in THIS work item only:

1. Slice 1 (this work item) — author the parent coordination spec (this document set), file the 5 child GitHub issues (Q-1 resolution applies — `#361.1` + `#361.2` + `#361.4` + `#361.5` filed at parent merge; `#361.3` filed after `#335` + `#336` reach spec-complete), open the parent Draft PR, attach the Integration AC checkboxes to the parent issue body.
2. Slice 2 (deferred to each child) — each child runs its own SDD lifecycle (intake → spec-complete → plan-slicer → implement → document-sync → pr-packager → agent-pr-review) per `AGENTS.md`.

## Change Strategy
- Migration/rollout sequence:
  1. Merge parent coordination PR (`#361`) — no runtime code; just spec, ADR, child issue refs.
  2. Children `#361.1` + `#361.2` + `#361.4` + `#361.5` run in parallel; merge order is `#361.1` first (pure core including predicate-registry mechanism), then `#361.2` (depends on core), then `#361.4` (depends on both for the Helm chart's runtime image) and `#361.5` (depends on `#361.1` for the predicate-registry mechanism that its C3 matrix rows reference).
  3. `#361.3` waits on `#335` + `#336` spec-complete; merges last.
  4. Parent `#361` closes only when all 5 children merge AND every Integration AC checkbox is ticked by a human bounded-context reviewer per Contract C4.
- Backward compatibility policy: The orchestrator is a new service with no prior surface; backward compatibility applies only to the additive C7 extension fields (subscribers MUST tolerate events that omit them, per § C7).
- Rollback plan: Per-child Helm rollback for `#361.4`; per-child PR revert for `#361.1` / `#361.2` / `#361.3`. The parent coordination spec itself is content-only — revert the commit.

## Validation Strategy (Shift-Left)
- Unit checks (per child):
  - `#361.1`: pure-Python unit tests for `DispatchMatrix.load`, `ConvergenceEngine.merge` (per mode), `SchemaValidator.validate`, `PredicateRegistry.evaluate`.
  - `#361.2`: unit tests for `event_id` derivation, `model_family(s)` normalization, `ReviewerRotationPicker.pick`, `TicketTokenAccumulator` add/summary/rebuild paths.
  - `#361.3`: unit tests for the OpenHands client request/response shapes against a stub HTTP server; subscriber ack/nack discipline against an in-process AMQP stub.
  - `#361.4`: Helm chart template tests (`helm template ... | kubectl --dry-run=server`); NetworkPolicy schema validation; PERSONA.md content validation per the existing `#360` PERSONA.md content checks.
- Contract checks:
  - C7 envelope shape validated against the JSON Schema embedded in `docs/blueprint/autonomous-factory/design-contracts.md` § C7.
  - Dispatch matrix shape validated against the table structure in § C3.
- Integration checks:
  - Cross-child integration tests (AC-005 .. AC-009) live in the deepest-merging child (`#361.3` or `#361.4`) and exercise the full work loop against in-process stubs for `#335` + `#336`.
- E2E checks:
  - N/A — no UI / no Playwright. Operator observability is via Grafana under `#350`.

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
- Notes: this work item is platform/factory infrastructure (orchestrator service), not an app-delivery workload. Child `#361.4` adds `infra-helm-orchestrator-*` targets under the existing `infra-helm-*` family but does not change the app-onboarding minimum-targets contract.

## Documentation Plan (Document Phase)
- Blueprint docs updates:
  - `docs/blueprint/autonomous-factory/design-contracts.md` § Contract C8 — adds the orchestrator Helm chart row (authored in `#361.4`).
  - `docs/blueprint/autonomous-factory/orchestrator.md` (new file, authored in `#361.3`) — work loop, dispatch matrix loader, convergence engine, schema validator, C7 emitter, reviewer-rotation picker, conditional-dispatch predicate registry, operator runbook entries.
  - `AGENTS.backlog.md` — mark `#369` incorporated when `#361.4` merges.
- Consumer docs updates:
  - Consumer-side orchestrator deployment overlay docs land in `#361.4` alongside the Helm chart.
- Mermaid diagrams updated:
  - `sequenceDiagram` for dispatch flow (in ADR + `orchestrator.md`).
  - `classDiagram` for module structure (in ADR + `orchestrator.md`).
- Docs validation commands:
  - `make docs-build`
  - `make docs-smoke`

## Publish Preparation
- PR context file:
  - `pr_context.md`
- Hardening review file:
  - `hardening_review.md`
- Local smoke gate (HTTP route/filter changes):
  - N/A — the orchestrator publishes no HTTP route handlers. Internal `/healthz` / `/readyz` / `/metrics` routes are operator-only and do not carry user-facing query/filter logic.
- Publish checklist:
  - include requirement/contract coverage (FR-001 .. FR-013, NFR-SEC-001 / NFR-OBS-001 / NFR-REL-001 / NFR-OPS-001 / NFR-A11Y-001, AC-001 .. AC-009)
  - include key reviewer files (this spec, ADR-issue-361, architecture.md, traceability.md)
  - include validation evidence + rollback notes

## Operational Readiness
- Logging/metrics/traces: NFR-OBS-001 — structured JSON stdout logs with `ticket_id`, `phase`, `rerun_round`, `event_id`, `decision_summary`; Prometheus `/metrics` counters for dispatched skills, schema validation failures, C7 emissions by phase, panel convergence outcomes by mode.
- Alerts/ownership: oncall ownership is `@sbonoc/factory-operations`; alert routes wired in `#361.4` Helm chart values (alert manager wiring deferred to consumer overlay).
- Runbook updates: NFR-OPS-001 — runbook entries for (a) draining the trigger queue, (b) reading C7 events from the durable bus, (c) looking up the most recent `phase: implement` event for reviewer-rotation debugging.

## Risks and Mitigations
- Risk 1 -> mitigation: `#335` / `#336` server-contract drift between intake and `#361.3` start. Mitigation: Q-1 sequences `#361.3` filing after `#335` + `#336` spec-complete; parent integration AC (AC-005) is the cross-child gate that catches drift.
- Risk 2 -> mitigation: `ux-ui-designer` expert raises the standing roster to 9 against the ADR-issue-364 ceiling of 8. Mitigation: FR-012 conditional-dispatch predicate gates the expert; architecture sign-off is the human approval surface for the ceiling exception.
- Risk 3 -> mitigation: At-least-once trigger delivery duplicates dispatches. Mitigation: deterministic `event_id = sha256(ticket_id|phase|rerun_round|emitter)` collapses duplicates at the bus; tested in AC-004.
- Risk 4 -> mitigation: Schema-validation false positives during early skill iteration. Mitigation: validation failure surfaces through the `#336` reject-rerun cap (AC-008); the reject signal is a fast-feedback loop into skill authoring.
