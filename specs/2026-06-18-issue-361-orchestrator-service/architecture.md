# Architecture

## Context
- Work item: `#361` Orchestrator service (Child B of `#333`, Phase 1 of Epic `#332`)
- Owner: `@sbonoc/factory-architecture` (intake author), bounded-context team `@sbonoc/factory-context-factory`
- Date: 2026-06-18

## Stack and Execution Model
- Backend stack profile: `python_plus_fastapi_pydantic_v2` (FastAPI surface is internal-only — `/healthz`, `/readyz`, `/metrics`; no public HTTP API)
- Frontend stack profile: `none`
- Test automation profile: `pytest_vitest_playwright_pact` (only `pytest` is exercised by this work item)
- Agent execution model: `specialized-subagents-isolated-worktrees`

## Problem Statement
- What needs to change and why: The autonomous factory currently has personas, skills, and the C7 lifecycle event schema authored (`#360`, `#337`, `#339`, `#347`, `#364`, `#368`), but no service that **dispatches** them. Without an orchestrator, the factory cannot turn an `agent-ready`-labeled GitHub issue into a sequence of skill executions, cannot validate skill outputs against the YAML jsonschema in `## Required Output Schema` blocks, cannot run the FR-008 reviewer-rotation picker, and cannot emit the eleven-field C7 phase-boundary events with the additive `expert_verdicts[]` / `routing_keys` / `token_usage` / `merger_overhead` extensions. This work item authors that service.
- Scope boundaries: The orchestrator is a persistent Python `Deployment` on the SKE control-plane node pool factory namespace. Its surfaces are: (a) RabbitMQ subscriber against `#336`'s trigger queue, (b) OpenHands Agent Server HTTP client against `#335`'s API, (c) durable-bus publisher emitting C7 events, (d) Prometheus `/metrics` scrape endpoint, (e) Kubernetes liveness/readiness probes. All five surfaces are owned by this work item across its 5-child decomposition.
- Out of scope: The OpenHands Agent Server itself (per #335, self-hosted in the SKE factory namespace — in-cluster Helm chart deployed via ArgoCD, sibling pattern to Keycloak — NOT a STACKIT-managed service), the LiteLLM gateway (per #335, external pre-existing service — the only true managed-external dependency), the RabbitMQ trigger queue topology + webhook handler, consumer-side C7 ingest + Grafana dashboards. Workspace pods are ephemeral and spawned by the in-cluster OpenHands Agent Server itself; the orchestrator does NOT spawn pods directly.

## Bounded Contexts and Responsibilities
5 children decompose along two canonical axes per the ADR-issue-337-light-decomposition-policy "Multi-axis exception for manually-authored parent coordination specs" (amended 2026-06-19): 4 under `architectural-layer` (runtime), 1 under `bounded-context: expert-panel` (governance/persona contract). Every child carries EXACTLY ONE canonical boundary type — the exception allows the parent to span two axes but forbids any single child from carrying a hybrid label.

- Context A — **Dispatch core** (child `#361.1`, `architectural-layer: domain/application`): pure-Python, no I/O. Loads the SDD-step × expert dispatch matrix from `docs/blueprint/autonomous-factory/design-contracts.md` § Contract C3; implements the three convergence modes from `ADR-issue-364-expert-persona-model.md` § 4 / § 5; validates skill outputs against the `## Required Output Schema` jsonschema; evaluates conditional-dispatch predicates (FR-012 mechanism layer).
- Context B — **Emission + bus integration** (child `#361.2`, `architectural-layer: infrastructure — emission and bus integration`): C7 event envelope construction with the deterministic `event_id`; durable-bus publisher (RabbitMQ AMQP); reviewer-rotation picker that queries the bus for the most recent `phase: implement` event on a given `ticket_id` and applies the `model_family(s)` normalization from § C7.
- Context C — **External-runtime clients** (child `#361.3`, `architectural-layer: infrastructure — external-runtime clients and service entrypoint`): RabbitMQ trigger subscriber consuming `#336`'s work queue; OpenHands Agent Server HTTP client per `#335`'s API (the OpenHands Agent Server is self-hosted in the SKE factory namespace per #335 — in-cluster Helm chart deployed via ArgoCD, sibling pattern to Keycloak; the orchestrator reaches it via in-cluster Kubernetes service DNS, NOT a public/managed-service endpoint); the orchestrator work loop that owns the lifecycle from `trigger-accepted` to step08 close.
- Context D — **Deployment surface** (child `#361.4`, `architectural-layer: infrastructure — deployment surface`): Helm chart under `scripts/templates/infra/orchestrator/`; egress `NetworkPolicy`; ESO-mounted credential references; Kubernetes `ServiceAccount` wired to the factory bot identity from `#334`.
- Context E — **`usability-pragmatist` expert + #369 closure** (child `#361.5`, `bounded-context: expert-panel`): the `usability-pragmatist` PERSONA.md at `.agents/personas/usability-pragmatist/PERSONA.md` (authored against the 6-section PERSONA.md template established by ADR-issue-364 § 3); the C3 matrix wiring at step01/04/05/08 gated by the FR-012 `ui-fidelity-or-a11y` predicate (OR-form covering both new user-facing flows AND accessibility-only changes to existing surfaces); `AGENTS.backlog.md` `#369` entry marked `(incorporated: issue-361.5)`; architecture-sign-off exception to the ADR-issue-364 expert-ceiling-of-8 authored as an ADR amendment (per parent spec § Notes for Child Intake — EXACTLY ONE OF a `Status: amended` note on ADR-issue-364 OR a new narrowly-scoped `ADR-issue-361.5-usability-pragmatist-ceiling-exception.md`; PERSONA.md front-matter cites the chosen ADR by path, NOT informal inline prose). The PERSONA.md file IS the interface contract between the SDD step (sealed actor of record per ADR-issue-364 § 2) and the expert-panel review lens layer, which is why the `bounded-context: expert-panel` classification (multi-axis exception per ADR-issue-337-light-decomposition-policy amended 2026-06-19) is the strategically-correct fit rather than bending the child into the `architectural-layer` axis.

## High-Level Component Design
- **Domain layer (Context A):**
  - `DispatchMatrix` — typed value object loaded from the contract markdown; rows are `MatrixRow(step, skill, expert_slugs, lead_voice, convergence_mode, predicate)`.
  - `ConvergenceEngine` — three strategies: `ParallelThenMerge`, `SequentialLens`, `StructuredDisagreement`. Each accepts a list of `ExpertVerdict` and returns an `AggregatedVerdict` carrying the merged verdict + the populated `merger_overhead` bookkeeping.
  - `SchemaValidator` — extracts the `## Required Output Schema` fenced ```yaml jsonschema``` block from a `SKILL.md`, parses to JSON Schema, and validates a candidate skill-output object; raises `SchemaValidationError` on mismatch.
  - `PredicateRegistry` — typed predicate evaluator (FR-012); the first predicate ships is `ui-fidelity-or-a11y` (gating `usability-pragmatist`; OR-form: `( has-user-facing-flow: true AND diff-touches-frontend-paths ) OR diff-touches-accessibility-relevant-paths`).
- **Application layer (orchestrator package):**
  - `WorkLoop` (Context C) — async coroutine: `await trigger_subscriber.recv() → load_matrix(step) → for each expert: dispatch via openhands_client → validate via SchemaValidator → ConvergenceEngine.merge() → C7Emitter.emit() → advance phase`.
  - `ReviewerRotationPicker` (Context B) — `pick(ticket_id) → routing_keys[]`; queries the bus, normalizes via `model_family(s)`, returns a heterogeneous routing-key set.
  - `TicketTokenAccumulator` (Context B) — in-process per-ticket accumulator across phase boundaries within the same work-loop execution; emits `ticket_token_summary` at step08 close. Rebuilt from the durable bus on pod restart (NFR-REL-001).
- **Infrastructure adapters (Context C + D):**
  - `OpenHandsAgentServerClient` — HTTP/REST client against `#335`'s API surface.
  - `RabbitMqTriggerSubscriber` — AMQP subscriber consuming `#336`'s work queue with manual ack discipline (NFR-REL-001 at-least-once).
  - `RabbitMqC7Publisher` — AMQP publisher to the durable bus C7 stream.
  - `EsoSecretVolumeReader` — reads ESO-mounted secret values from mounted volume paths (NOT env vars per NFR-SEC-001).
- **Presentation/API/workflow boundaries:**
  - FastAPI internal-only routes: `GET /healthz` (liveness), `GET /readyz` (readiness — synthetic AMQP probe), `GET /metrics` (Prometheus exposition).
  - No public HTTP API; the orchestrator is a consumer-and-emitter of events, not an HTTP service for external clients.

## Integration and Dependency Edges
- Upstream dependencies:
  - `#336` (RabbitMQ trigger queue + webhook receiver + GitHub Actions workflows) — orchestrator is the subscriber. Per #336, the `trigger-accepted` publisher is an **in-cluster Python webhook-receiver service** that fronts the RabbitMQ queue; the GitHub Actions reusable workflows under `.github/workflows/factory-webhook-bridge.yml` POST to the receiver over authenticated HTTPS. GitHub-hosted Actions runners cannot reach the SKE-internal RabbitMQ directly (public RabbitMQ exposure is rejected by NFR-SEC-001 + the #334 egress NetworkPolicy). The orchestrator subscribes to the queue and is agnostic to the publisher topology — its contract is "consume from a RabbitMQ work queue", nothing upstream of that. Spec-complete blocker for `#361.3`.
  - `#335` (OpenHands Agent Server + LiteLLM gateway) — orchestrator is the API client. OpenHands is self-hosted in the SKE factory namespace per #335 — in-cluster Helm chart deployed via ArgoCD (sibling pattern to Keycloak); LiteLLM is the only true managed-external dependency (pre-existing enterprise gateway, accessed via HTTPS — #335 configures access, does NOT deploy LiteLLM). Spec-complete blocker for `#361.3`.
  - `#360` (personas + skill `SKILL.md` runbooks + `## Required Output Schema` jsonschema blocks) — orchestrator's `SchemaValidator` consumes these. CLOSED 2026-06-03 — unblocked.
  - `#334` (factory bot identity + ServiceAccount + ESO credentials) — orchestrator's pod identity. Spec-complete blocker for `#361.4`.
- Downstream dependencies:
  - `#350` (consumer-side C7 ingest + Grafana dashboard) — consumes the C7 events the orchestrator emits.
  - `#338` (Phase 3 data feed) — consumes the `outcome_details.expert_verdicts[]` and `outcome_details.token_usage` extension fields.
- Data/API/event contracts touched:
  - `docs/blueprint/autonomous-factory/design-contracts.md` § Contract C3 (dispatch matrix — read-only at startup), § Contract C7 (event schema — emit), § Contract C8 (consumer-shipped surface — adds orchestrator Helm chart row).
  - `ADR-issue-337-c7-emission-mechanism.md` (FR-019 emitter rule + `event_id` derivation).
  - `ADR-issue-364-expert-persona-model.md` § 4 / § 5 (convergence modes), § 6 (always-respond verdict contract), § 9 (`ExpertVerdictSummary` shape).
  - `ADR-issue-368-factory-cost-telemetry-routing-fixture.md` (additive extension fields: `routing_keys` covering all phases, `token_usage`, `merger_overhead`, `ticket_token_summary`).

## Non-Functional Architecture Notes
- Security: NFR-SEC-001 — non-root distroless runtime; read-only root filesystem; ESO volume-mounted credentials only (no env-var secret injection); egress NetworkPolicy denies public internet; the orchestrator never holds Anthropic API keys (all model calls route through LiteLLM owned by `#335`).
- Observability: NFR-OBS-001 — structured JSON stdout logs with `ticket_id` / `phase` / `rerun_round` / `event_id` / `decision_summary` on every dispatch, validation, and emission; Prometheus `/metrics` counters for dispatched skills, schema validation failures, C7 emissions by phase, panel convergence outcomes by mode; per-expert `token_usage` on every panel-dispatched C7 event so per-ticket cost is queryable from the C7 stream alone.
- Reliability and rollback: NFR-REL-001 — restart-safe; in-flight panel invocations resume from the durable bus event log on pod restart; per-ticket token accumulator rebuilt from the bus; Helm rolling-update with `maxUnavailable: 0` / `maxSurge: 1`; rollback is `helm rollback orchestrator <previous-revision>`. The deterministic `event_id` ensures duplicate emissions from at-least-once trigger delivery collapse at the bus.
- Monitoring/alerting: NFR-OPS-001 — TCP liveness probe on `/metrics` port; AMQP readiness probe; runbook entries for draining the trigger queue, reading C7 events from the durable bus, and looking up the most recent `phase: implement` event for reviewer-rotation debugging.

## Risks and Tradeoffs
- Risk 1 — `#335` / `#336` spec drift: Authoring `#361.3` (RabbitMQ subscriber + OpenHands API client) against an unfinished server contract risks rework. Mitigation: file `#361.3` only after `#335` + `#336` reach spec-complete (Q-1 recommendation). The pure-core children `#361.1` + `#361.2`, the deployment-surface child `#361.4`, and the usability-pragmatist governance-docs child `#361.5` proceed independently.
- Risk 2 — `usability-pragmatist` expert ceiling exception: ADR-issue-364 seals the expert roster at 8. Pulling in `#369` brings the standing roster to 9, requiring an architecture-sign-off exception. Mitigation: the conditional-dispatch predicate (FR-012) ensures `usability-pragmatist` fires only on UI work items, preventing token-cost amplification on non-UI tickets — this is the safety property the ADR exception is conditioned on.
- Risk 3 — Single-replica orchestrator: NFR-OPS-001 ships `replicas: 1` to avoid contention on the per-ticket token accumulator. If throughput needs grow, this becomes a bottleneck. Mitigation: deferred-proposal entry tracks the horizontal-scaling decision; the bus-rebuild-on-restart pattern leaves the door open to a shared-lock-service refactor.
- Tradeoff 1 — Pure-Python core vs language uniformity with `#336`: The webhook handler is also Python; the orchestrator inherits that runtime so the in-process schema validator + dispatch matrix loader can be shared library code if `#350` ingest later wants to revalidate C7 events. The cost is one more Python service to operate.
- Tradeoff 2 — Naive string-equality finding dedup vs embedding-based dedup: ADR-issue-364 § 11 defers embedding-based dedup. v1 ships string-equality. If duplicate-finding sprawl shows up in `merger_overhead.findings_before_dedup - findings_after_dedup`, the deferred backlog entry surfaces.
