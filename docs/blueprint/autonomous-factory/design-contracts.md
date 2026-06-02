# Autonomous Software Factory — Design Contracts (C1–C8)

**Issue:** #339
**Spec:** `specs/2026-05-28-issue-339-factory-design-contracts/`
**ADR:** [`../architecture/decisions/ADR-issue-339-factory-design-contracts.md`](../architecture/decisions/ADR-issue-339-factory-design-contracts.md)
**Status:** approved
**Factory contract version:** 1.0.0 (semver — see Contract C8 § Compatibility posture)

## Purpose

This document pins the cross-ticket interface conventions that the Phase 1 autonomous-factory tickets (#333, #334, #335, #336) and the Phase 0 sibling #337 depend on, AND enumerates the consumer-shipped surface (Contract C8) the blueprint publishes so each consumer repo can instantiate its own per-consumer factory.

Contracts C1–C4 are **identical conventions** — applied unchanged by the blueprint repo and by every consumer repo. Contracts C5–C7 are **parameterized** — the rule is identical for every factory instance, the blueprint records its own values under `### Blueprint instance`, and consumer repos populate their own values via the `### Consumer overlay` schema. Contract C8 enumerates the **consumer-shipped surface** (docs/ADRs, Terraform/Helm module wrappers, Make targets + skill runbooks, GitHub App + Actions workflows) consumer repos inherit via the existing blueprint `contract.yaml` mechanism.

## Review Conventions

- **Deferred-decision placeholder token.** The blueprint's `unresolved_marker_tokens` validator (in `make quality-sdd-check`) scans `specs/<slug>/` for the literal token `TBD`. That validator does NOT scan `docs/blueprint/`, so this document uses the placeholder token freely inside `### Open Decisions` subsections. The token is enumerated here once so that the blueprint-side spec, tasks, and traceability artifacts under `specs/2026-05-28-issue-339-factory-design-contracts/` are free of the literal token at `SPEC_READY=true` (per FR-003).
- **Open Decisions.** Every deferred value MUST live under an explicit `### Open Decisions` subsection naming the deferring ticket and the resolve-by deadline. Deferred-decision placeholders outside such a subsection MUST be rejected by review (FR-003).
- **`Referenced by:` lines.** Every contract section ends with a `Referenced by:` line. The union across the eight sections covers `{#333, #334, #335, #336, #337, #338}` with no orphan ticket (FR-002, AC-002). Contract C8 additionally cites #342 (Phase 1 factory upgrade process) per AC-012.
- **Normative language.** Contract sections use `MUST` / `MUST NOT`. Plain-language softeners are not in scope here — every clause is normative unless prefixed with "Informative:".
- **Sign-off policy.** The four canonical sign-off phrases from `AGENTS.md § Sign-off Phrases (Deterministic)` are required before merge: `SPEC_PRODUCT_READY: approved` (Product), `ARCHITECTURE_SIGNOFF: approved` (Architecture), `SECURITY_SIGNOFF: approved` (Security), `OPERATIONS_SIGNOFF: approved` (Operations). Plain-language variants do NOT count.
- **Genesis exception (C2 front-matter).** The SDD artifacts produced by this work item (PR #340) — this document, `ADR-issue-339-factory-design-contracts.md`, `spec.md`, `traceability.md`, `evidence_manifest.json`, `context_pack.md` — are EXEMPT from the C2 front-matter requirement. They are the genesis artifacts that established the convention; the front-matter block requirement applies to every factory-governed SDD artifact authored in a subsequent work item. The C2 enforcement tooling (deferred per AC-013) will gate future artifacts, not these genesis files.

## Sign-off Block

| Role | Canonical phrase | Status |
|---|---|---|
| Product | `SPEC_PRODUCT_READY: approved` | approved |
| Architecture | `ARCHITECTURE_SIGNOFF: approved` | approved |
| Security | `SECURITY_SIGNOFF: approved` | approved |
| Operations | `OPERATIONS_SIGNOFF: approved` | approved |

---

## Contract C1 — Branch Naming (Identical Convention)

Every factory instance — blueprint repo and every consumer repo alike — MUST select branch names from the existing `repository.branch_naming.purpose_prefixes` set declared in its own `blueprint/contract.yaml` (inherited from the upstream blueprint via the existing `contract.yaml` inheritance mechanism). The blueprint's authoritative set today is `{feature/, fix/, hotfix/, chore/, docs/, refactor/, test/, ci/}` and the pattern is `<prefix><YYYY-MM-DD>-<work-item-slug>` (`repository.branch_contract.branch_name_pattern`).

**Bot prefix selection.** The factory bot MUST select the prefix that matches the work-item type:

| Work-item type | Required prefix |
|---|---|
| Bug-fix ticket | `fix/` |
| New capability / feature | `feature/` |
| Maintenance / cleanup | `chore/` |
| Documentation-only | `docs/` |
| Refactor (no behavior change) | `refactor/` |
| Test-only | `test/` |
| CI / pipeline | `ci/` |
| Production hotfix | `hotfix/` |

**Slug shape.** Factory-driven branches MUST use:

- Single-ticket runs: `issue-<issue-number>-<short-slug>` (e.g., `issue-339-factory-design-contracts`).
- Decomposed children: `issue-<parent-issue>-<child-issue>-<short-slug>`.

**Rejected alternative.** A parallel `factory/` prefix is REJECTED: it would bypass the pre-push `quality validate branch naming` hook, omit the `<YYYY-MM-DD>` date segment, and erase semantic intent. Bot vs human parity is preserved at the branch layer; bot attribution is recorded via Contract C5, not via the branch prefix.

Referenced by: #333, #335, #336

---

## Contract C2 — Spec Directory Layout (Identical Convention)

Every factory instance MUST place work-item specs at `specs/<YYYY-MM-DD>-<work-item-slug>/` under the repo root. This convention is applied independently by the blueprint repo and by each consumer repo; specs are NOT inherited from the blueprint and are NOT part of the C8 consumer-shipped surface. The existing `blueprint/contract.yaml` already enforces this boundary: `spec.repository.ownership_path_classes.source_only` lists `specs`, and `spec.repository.consumer_init.source_artifact_prune_globs_on_init` prunes dated spec directories on consumer init.

**Decomposed children.** Children of a decomposed parent MUST live at `specs/<YYYY-MM-DD>-<parent-slug>/children/<child-issue>-<child-slug>/`. Each child spec MUST reference the parent spec path and the boundary type cited by the `blueprint-ticket-decompose-light` skill.

### SDD-artifact front-matter (FR-005, AC-013)

Every SDD artifact authored under this contract MUST carry a YAML front-matter block at the top of the file, fenced by two `---` lines. Artifact scope: spec documents under `specs/<slug>/`, ADR records under `docs/blueprint/architecture/decisions/`, traceability matrices, and evidence manifests.

Required keys (each MUST be present; absence MUST be rejected by `make quality-sdd-check`):

| Key | Type | Definition |
|---|---|---|
| `id` | string | Stable, globally-unique artifact identifier (e.g., `spec-2026-05-28-issue-339`). |
| `artifact_kind` | enum string | One of `spec`, `adr`, `traceability`, `evidence-manifest`. |
| `work_item_slug` | string | Matches the parent directory `<YYYY-MM-DD>-<work-item-slug>`. |
| `owner_team` | string | GitHub team slug owning the work item (e.g., `@sbonoc/factory-architecture`). |
| `schema_version` | string | Semver string matching the factory contract version (FR-019). |

Worked examples — one per `artifact_kind` value:

`artifact_kind: spec` — `specs/2026-05-28-issue-339-factory-design-contracts/spec.md`:

```yaml
---
id: spec-2026-05-28-issue-339
artifact_kind: spec
work_item_slug: 2026-05-28-issue-339-factory-design-contracts
owner_team: "@sbonoc/factory-architecture"
schema_version: 1.0.0
---
```

`artifact_kind: adr` — `docs/blueprint/architecture/decisions/ADR-issue-339-factory-design-contracts.md`:

```yaml
---
id: adr-issue-339-factory-design-contracts
artifact_kind: adr
work_item_slug: 2026-05-28-issue-339-factory-design-contracts
owner_team: "@sbonoc/factory-architecture"
schema_version: 1.0.0
---
```

`artifact_kind: traceability` — `specs/2026-05-28-issue-339-factory-design-contracts/traceability.md`:

```yaml
---
id: traceability-2026-05-28-issue-339
artifact_kind: traceability
work_item_slug: 2026-05-28-issue-339-factory-design-contracts
owner_team: "@sbonoc/factory-architecture"
schema_version: 1.0.0
---
```

`artifact_kind: evidence-manifest` — `specs/2026-05-28-issue-339-factory-design-contracts/evidence_manifest.json` (front-matter expressed as a top-level JSON object since JSON has no YAML fences):

```json
{
  "id": "evidence-2026-05-28-issue-339",
  "artifact_kind": "evidence-manifest",
  "work_item_slug": "2026-05-28-issue-339-factory-design-contracts",
  "owner_team": "@sbonoc/factory-architecture",
  "schema_version": "1.0.0",
  "evidence": []
}
```

**Downstream consumers.** The front-matter convention is identical for the blueprint repo and every consumer repo. Downstream observers (the future Central Brain index per Epic #343) will rely on these keys to attribute and version every ingested artifact. No ingestion logic is owned by this work item; any change to the required-key set MUST go through #339 sign-off.

Referenced by: #333, #336, #338

---

## Contract C3 — OpenHands Microagent ↔ Persona Mapping (Identical Convention)

Every factory instance MUST map OpenHands microagents to personas by **name equality**: the microagent name MUST equal the persona file basename (without extension). Selection is governed by the persona's `## Activation Triggers` section (authoritative for when the microagent is selected). Execution scope is governed by the persona's `## Skills Invoked` section (authoritative for what the microagent is permitted to call).

This convention is identical for the blueprint repo and every consumer repo. Consumer-authored personas live under the consumer namespace defined by Contract C8 § FR-018; blueprint-authored personas live under `.agents/personas/`.

Referenced by: #333, #335

---

## Contract C4 — Integration Acceptance Criteria Format (Identical Convention)

Every parent issue that decomposes into child tickets MUST carry an `## Integration Acceptance Criteria` section in the parent issue body. The section MUST contain checkboxes that are only satisfiable by **cross-child behavior** (no checkbox is satisfiable by a single child in isolation).

Parent closure MUST depend on BOTH:

1. All children merged, AND
2. Every `## Integration Acceptance Criteria` checkbox ticked by a **human bounded-context reviewer** (the factory bot MUST NOT tick these checkboxes).

This convention is identical for the blueprint repo and every consumer repo.

Referenced by: #333, #336, #338

---

## Contract C5 — Factory Bot Identity + SoD Detection (Parameterized)

### Identical rule

Every factory instance MUST authenticate as a single GitHub machine user (one bot login per instance). The multi-author Separation-of-Duties (SoD) suppression rule MUST apply **exact-string equality** on the PR comment author's GitHub login. Substring matching, regex matching, and display-name heuristics MUST NOT be used (NFR-SEC-001).

Concretely: a PR comment counts toward multi-author SoD if and only if `comment.user.login != factory_bot_login` under exact-string comparison. Any sign-off phrase posted by the factory bot MUST be ignored for SoD purposes.

### Blueprint instance

The blueprint factory instance bot login is `stackit-factory-bot` (Q-1 resolved 2026-05-28 in PR #340).

### Consumer overlay

Consumer repos MUST declare their own bot login. The blueprint's value MUST NOT be inherited (every consumer factory authenticates as its own machine user — inheriting `stackit-factory-bot` would cross consumer tenancy boundaries).

| Schema field | Type | Configuration location | Validation rule |
|---|---|---|---|
| `bot_identity.github_login` | string | `spec.factory_contract.bot_identity.github_login` in consumer `contract.yaml` | Non-empty; MUST match the actual GitHub login of the consumer's machine user; MUST differ from the blueprint's `stackit-factory-bot`. |

### Open Decisions

- **Reserve and verify the bot identity on GitHub** — deferring ticket: **#334** (factory runtime on SKE — Secrets Manager + ESO + egress NetworkPolicy + bot identity); resolve-by deadline: **Phase 1 close (Epic #332 acceptance gate)**. Placeholder: `<TBD: reserve-and-verify in #334>`.

Referenced by: #334, #335, #336, #337

---

## Contract C6 — CODEOWNERS Team Slugs (Parameterized)

### Identical rule

Every factory instance MUST resolve the four canonical sign-off roles (Product, Architecture, Security, Operations) to **real GitHub team slugs**, each carrying **at least two members**. A single collapsed pool is REJECTED (would break the multi-author SoD rule from Contract C5 in small organisations).

Each role's team slug MUST be referenced from the consumer repo's `.github/CODEOWNERS` for the paths that role owns.

Informative: a GitHub team can hold any number of members. To provide backup coverage within a role — so sign-off is not blocked when the primary person is unavailable — add two or more people to the role's team. Any single member of the team satisfies the sign-off requirement; the ≥ 2 members constraint ensures a second person is always available without requiring a separate schema field or team slug per backup.

### Blueprint instance

The blueprint factory instance maps the four canonical roles to (Q-2 resolved 2026-05-28 in PR #340):

| Role | Blueprint team slug |
|---|---|
| Product | `@sbonoc/factory-product` |
| Architecture | `@sbonoc/factory-architecture` |
| Security | `@sbonoc/factory-security` |
| Operations | `@sbonoc/factory-operations` |

Bounded-context teams are kept **separate** from the four sign-off teams (no role-tagging committee). The concrete bounded-context enumeration for the blueprint instance is `{factory, infra, docs, governance}` (Q-3 resolved 2026-05-28 in PR #345 — `specs/2026-05-28-issue-337-factory-phase-0-foundations/spec.md`). The corresponding GitHub team slugs are:

| Bounded context | Blueprint team slug |
|---|---|
| `factory` | `@sbonoc/factory-context-factory` |
| `infra` | `@sbonoc/factory-context-infra` |
| `docs` | `@sbonoc/factory-context-docs` |
| `governance` | `@sbonoc/factory-context-governance` |

These slugs are wired into `.github/CODEOWNERS` Gate 2 per FR-011 (PR #345).

### Consumer overlay

Consumer repos MUST declare their own four team slugs. The blueprint's slugs MUST NOT be inherited.

| Schema field | Type | Configuration location | Validation rule |
|---|---|---|---|
| `codeowners.product` | string | `spec.factory_contract.codeowners.product` in consumer `contract.yaml` | GitHub team slug starting with `@`; the underlying team MUST have ≥2 members. |
| `codeowners.architecture` | string | `spec.factory_contract.codeowners.architecture` | Same as above. |
| `codeowners.security` | string | `spec.factory_contract.codeowners.security` | Same as above. |
| `codeowners.operations` | string | `spec.factory_contract.codeowners.operations` | Same as above. |

### Open Decisions

- **Concrete blueprint-instance team provisioning on GitHub** (create the eight teams — four sign-off + four bounded-context — and populate ≥2 members each) — deferring ticket: **#337**; resolve-by deadline: **#337 close**. The bounded-context enumeration is now pinned above; what remains is the GitHub-side team creation and membership population, which is an operational task tracked under #337's Operations sign-off scope.

Referenced by: #336, #337

---

## Contract C7 — Metrics Dashboard + Event Schema (Parameterized)

### Identical rule

Every factory instance MUST emit a lifecycle event for every persona phase transition. This emission requirement covers both **autonomous execution** (factory bot runs triggered by the GitHub webhook pipeline) and **human-assisted local execution** (a developer invoking the SDD step skills manually via Claude Code or any other local CLI). The local-execution exemption that previously appeared in this section is CLOSED by `ADR-issue-347-human-sdd-c7-symmetry.md`, which adds `local-cli` as the third sealed emitter. Local emissions write to a JSONL sink (`artifacts/c7/<work-item-slug>.jsonl`) committed to the branch; the durable-bus ingest path is delivered by follow-up issue #350 (blocked by #336 runtime).

The minimum event field set is a named JSON schema with explicit types and nullability per field:

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "FactoryLifecycleEventV1",
  "type": "object",
  "additionalProperties": true,
  "required": [
    "event_id",
    "ticket_id",
    "parent_ticket_id",
    "phase",
    "persona",
    "model",
    "timestamp",
    "outcome",
    "rerun_round",
    "owner_team",
    "emitter"
  ],
  "properties": {
    "event_id":         { "type": "string",  "description": "Deterministic dedupe key with **emitter-conditional derivation**: `sha256(ticket_id|phase|rerun_round|emitter)` for `emitter: orchestrator`; `sha256(ticket_id|phase|rerun_round|emitter|webhook_event_key)` for `emitter: webhook-handler` (the five-input variant; see § Contract C7 emission idempotency for the `webhook_event_key` sourcing rule). Populated by the emitter (orchestrator #333 or webhook handler #336) before publish; identical retries MUST produce the identical `event_id` so subscribers can dedupe at-least-once delivery." },
    "ticket_id":        { "type": "string",  "description": "GitHub issue identifier (e.g., '339'). This is the canonical work-item identifier referenced as `ticket_id` throughout the C7 contract; FR-019 and ADR-issue-337-c7-emission-mechanism.md describe the same identifier — terminology is unified on `ticket_id` to match this schema field name (renaming is forbidden under FR-017(b))." },
    "parent_ticket_id": { "type": ["string", "null"], "description": "Parent issue identifier for decomposed children; null for top-level tickets." },
    "phase":            { "type": "string",  "enum": ["intake", "resolve-questions", "spec-complete", "plan-slicer", "implement", "document-sync", "pr-packager", "agent-pr-review", "c7-emission-opted-out"] },
    "persona":          { "type": "string",  "description": "For `emitter: orchestrator` events: the persona file basename (matches Contract C3 microagent name). For `emitter: webhook-handler` events (which have no persona invocation — rerun-cap, bot-tick block, rotation-violation, etc.): the sealed sentinel string `webhook-handler`. For `emitter: local-cli` events: the SDD step skill basename invoked by the operator (e.g., `blueprint-sdd-step01-intake`, `blueprint-sdd-step05-implement`). The field stays `type: string` and required in all eleven-field events; the sentinel value preserves the sealed minimum schema while reflecting that the deterministic webhook handler emitter is itself the actor of record." },
    "model":            { "type": "string",  "description": "For `emitter: orchestrator` events: the LLM model identifier resolved via LiteLLM (e.g., `claude-opus-4-7`). For `emitter: webhook-handler` events (which have no LLM invocation): the sealed sentinel string `n/a`. For `emitter: local-cli` events: the model identifier resolved from the operator environment via the priority chain `$CLAUDE_CODE_MODEL` → `$CODEX_MODEL` → `$CURSOR_MODEL`; if none of these env vars is set, the sealed sentinel string `unknown` is used. The field stays `type: string` and required in all eleven-field events; the sentinel value preserves the sealed minimum schema. Webhook-handler rotation-violation events MAY additionally carry the violating model identifier as the non-required extension field `violating_model` (permitted by `additionalProperties: true`) for audit traceability — this is NOT part of the eleven-field minimum." },
    "timestamp":        { "type": "string",  "format": "date-time", "description": "RFC 3339 UTC timestamp at emission." },
    "outcome":          { "type": "string",  "enum": ["success", "rejected", "retried", "human-handoff"] },
    "rerun_round":      { "type": "integer", "minimum": 0, "description": "Zero on first attempt; incremented on each persona rerun." },
    "owner_team":       { "type": "string",  "description": "GitHub team slug owning the work item (matches C2 front-matter `owner_team`)." },
    "emitter":          { "type": "string",  "enum": ["orchestrator", "webhook-handler", "local-cli"], "description": "Names the deterministic emitter surface that wrote the event. The three-emitter sealed rule (FR-019, extended by ADR-issue-347-human-sdd-c7-symmetry.md) MUST be enforced by subscribers — any value outside this enum is REJECTED. Required for the `event_id` derivation to be globally unique across all three surfaces." }
  }
}
```

Consumers MUST NOT remove, rename, or change the type of any of the eleven minimum fields. Addition of further fields is permitted (sealed under FR-017(b); see Contract C8).

**Extension-field vocabulary.** The following non-required extension fields are STANDARDIZED (emitters SHOULD populate them when applicable; subscribers SHOULD NOT reject events that omit them):

| Extension field | Type | Populated by | Description |
|---|---|---|---|
| `execution_mode` | `string` enum (`autonomous` \| `human-assisted`) | All three emitter surfaces | Discriminator for downstream filtering and Grafana faceting. `orchestrator` and `webhook-handler` events carry `autonomous`; `local-cli` events carry `human-assisted`. |
| `webhook_event_key` | `string` | `webhook-handler` only | Discriminator for the five-input `event_id` derivation; see § Emission idempotency. |
| `violating_model` | `string` | `webhook-handler` only (rotation-violation events) | The model ID that triggered the FR-008 rotation-violation rejection. |

The `phase` enum carries one entry per blueprint SDD step in `.agents/skills/blueprint-sdd-step0N-<name>/` — stripping the `step0N-` prefix from the skill basename yields the enum value (e.g., `blueprint-sdd-step08-agent-pr-review` → `agent-pr-review`). The `agent-pr-review` entry is REQUIRED for the FR-008 reviewer-heterogeneity audit invariant, which pairs the C7 event with `phase: implement` (emitted by step05) and the C7 event with `phase: agent-pr-review` (emitted by step08) on the same `ticket_id` and asserts the `model` field on the `implement` event differs from the `model` field on the `agent-pr-review` event; a schema that lacks `agent-pr-review` makes the audit unimplementable. The audit predicate MUST reference C7 `phase` enum values, not the originating skill basenames — emitters write the unprefixed enum value into the `phase` field, so a predicate written against `step05-implement` or `step08-agent-pr-review` would never match a schema-valid event. Consumers MUST NOT remove any of these enum values; additions to the enum are out of scope for consumer overlays and require a #339 sign-off cycle. The reserved value `c7-emission-opted-out` is a `local-cli`-only pseudo-phase written by `OptOutAuditUseCase` when `BLUEPRINT_SDD_C7_EMIT=0`; it does not correspond to any SDD step skill and MUST NOT be used as the `phase` field on any orchestrator or webhook-handler event. Subscriber-side ingest (#350) MUST handle this value explicitly (e.g., route to an opt-out audit table rather than the main phase-boundary timeline).

**Emission transport (sealed).** Events MUST be emitted to a **durable, replayable bus** with the following semantics:

- **Durability** — events MUST be persisted before the producer returns; transient in-memory queues MUST NOT be used.
- **Replayability** — subscribers MUST be able to replay historic ranges (consumer-position tracking is the subscriber's responsibility, not the producer's).
- **Async fire-and-forget** — the factory runtime MUST NOT block on subscriber acknowledgement or on any downstream availability. A subscriber outage MUST NOT degrade factory throughput.
- **Multi-subscriber** — the bus MUST support multiple independent consumer groups so that the metrics dashboard (Contract C7 § Blueprint instance), the GitHub Actions webhook bridge (#336), and downstream observers (Epic #343 Central Brain ingest) can each subscribe with independent positions.

Synchronous writes to a dashboard MUST NOT replace the bus emission. The Grafana dashboard target (Blueprint instance) MUST subscribe to the bus, not receive synchronous writes.

**Cross-link to downstream observers.** The future Central Brain index (Epic #343) MUST subscribe to the same bus with its own consumer group. Any change to the eleven-field minimum schema MUST go through #339 sign-off — out-of-band schema changes by downstream consumers are REJECTED.

**Emission mechanism (sealed).** C7 events MUST be emitted by EXACTLY ONE OF three deterministic surfaces — personas, skills, OpenHands itself, workspace pods, and LiteLLM MUST NOT emit C7 events under any condition:

1. **Orchestrator (#333)** — the persistent Python control-plane service that owns the factory work loop emits every phase-boundary event (one C7 event per skill execution, with the `phase` field carrying the enum value derived from the skill basename — e.g., `phase: intake` for `blueprint-sdd-step01-intake` … `phase: agent-pr-review` for `blueprint-sdd-step08-agent-pr-review`, per the phase-enum-naming convention above). The orchestrator wraps each persona invocation as a structured operation: it constructs the C7 envelope before calling the OpenHands session API, validates the persona's structured output against a skill-runbook output schema (a fenced ```yaml jsonschema``` block in each `SKILL.md` per FR-002 — schema authoring is owned by #333), records the outcome on the envelope, and writes the event to the durable bus. Phase-boundary outcomes (`success`, `rejected`, `retried`) flow through this surface.
2. **Webhook handler (#336)** — the GitHub webhook ingestion service emits the events that originate from observable GitHub state and are not visible to the orchestrator: escalate-class blocks, agent-stop human-handoffs, rerun-cap breaches, integration-criteria-bot-tick blocks, ceiling-hit human-handoffs, and the rotation-violation rejection from the FR-008 audit invariant. The webhook handler observes the GitHub event, decides the outcome class, writes the C7 envelope, and emits to the durable bus.
3. **Local CLI helper (`local-cli`, issue #347)** — the deterministic Python helper (`scripts/bin/sdd/c7_emit.py`) invoked by the SDD step skill addendum at the end of each operator-driven skill execution. The helper is invoked by the skill runbook (not by the LLM directly — skill-as-tool pattern enforces the anti-hallucination property); it constructs the C7 envelope, appends it to the local JSONL sink (`artifacts/c7/<work-item-slug>.jsonl`), and returns. The JSONL file is committed to the branch so it is available for ingest by the durable-bus handler once follow-up issue #350 ships. Local-CLI emission MUST be enabled by default and can be suppressed per work item by setting `BLUEPRINT_SDD_C7_EMIT=0` (opt-out audit event `c7-emission-opted-out` is written in place of the skipped event when suppression is active).

Trigger acceptance is NOT a C7 event. When an authorized actor applies the `factory-trigger-accepted` label, the webhook handler publishes a `trigger-accepted` work message onto a separate RabbitMQ work queue that the orchestrator subscribes to — this is the trigger-handoff transport, not a lifecycle event, and it has no entry in the C7 `phase` enum. The first C7 event for an accepted trigger is the orchestrator's `phase: intake` event emitted when the intake persona is invoked (see `ADR-issue-337-c7-emission-mechanism.md` § Webhook handler emission responsibilities for the canonical responsibility table).

Emission MUST be idempotent. The `event_id` derivation is **emitter-conditional** because the three emitter surfaces have structurally different uniqueness guarantees on the `(ticket_id, phase, rerun_round)` tuple:

- For `emitter: orchestrator` events: `event_id = sha256(ticket_id|phase|rerun_round|emitter)`. The orchestrator emits EXACTLY ONE C7 event per persona phase boundary per the sealed-emitter rule, so the `(ticket_id, phase, rerun_round)` tuple is unique per orchestrator emission and the four-input hash collision-free.
- For `emitter: webhook-handler` events: `event_id = sha256(ticket_id|phase|rerun_round|emitter|webhook_event_key)`. The webhook handler can legitimately emit multiple distinct C7 events on the same `(ticket_id, phase, rerun_round)` tuple (e.g., successive `integration-criteria-bot-tick-blocked` rejections from repeated bot-tick attempts on the same phase; a `rerun-cap-exceeded` rejection followed by a separately-triggered `rotation-violation` rejection on the same phase); the discriminator MUST therefore be included to prevent distinct events from collapsing to the same `event_id`. The discriminator `webhook_event_key` is sourced as follows: when the C7 emission is triggered by an inbound GitHub webhook payload, `webhook_event_key` MUST be the GitHub `X-GitHub-Delivery` UUID (which GitHub preserves across redeliveries, so subscriber-side dedupe still absorbs webhook-handler retries); when the emission is triggered by an internal audit invariant with no inbound GitHub webhook (e.g., the FR-008 rotation-violation pairing), `webhook_event_key` MUST be `sha256(rejection_reason|outcome|trigger_timestamp_rfc3339)` from the handler-internal trigger context. `webhook_event_key` is carried as a non-required extension field (permitted by C7's `additionalProperties: true`) — it is NOT part of the eleven-field minimum schema, because orchestrator events do not populate it; webhook-handler emissions MUST populate it on every emission.
- For `emitter: local-cli` events: `event_id = sha256(ticket_id|phase|rerun_round|emitter)`. The local-cli helper emits EXACTLY ONE C7 event per SDD step skill execution, so the four-input hash is collision-free within a single operator session. `rerun_round` is computed by the helper from prior committed events for the same `(ticket_id, phase)` pair in the local JSONL sink before constructing the envelope, ensuring deterministic idempotency across reruns.

The derivation inputs are all schema fields: `ticket_id` is the GitHub issue identifier declared above (the same identifier referenced as `work_item_id` in some earlier ADR prose — terminology is unified on `ticket_id` to match the schema field name); `emitter` is the three-value enum (`orchestrator` | `webhook-handler` | `local-cli`) declared above; `phase` and `rerun_round` are the schema fields of the same name; `webhook_event_key` is the non-required extension field defined above (required only when `emitter: webhook-handler`). `event_id` itself is also a required schema field — emitters MUST populate it before publish, and subscribers MUST use it as the dedupe key. LLM personas MUST NOT carry C7 envelope fields in their structured output and MUST NOT have direct access to the durable bus or local JSONL sink — the emission contract is enforced at the orchestrator, webhook handler, and local-cli helper exclusively. This design ensures C7 cannot drift on LLM-side prompt regressions, persona renames, or skill reorganization: the schema and the emission surfaces are all controlled deterministically by the three named services.

### Blueprint instance

The blueprint factory metrics dashboard target is **STACKIT-managed Grafana** via the existing `OBSERVABILITY_ENABLED` module declared in `blueprint/contract.yaml` (Q-3 resolved 2026-05-28 in PR #340). The dashboard subscribes to the durable bus rather than receiving synchronous writes.

**Retention and owner (Q-4 resolved 2026-05-28 in PR #345 — `specs/2026-05-28-issue-337-factory-phase-0-foundations/spec.md`).** Lifecycle event retention on the durable bus and on the Grafana dashboard MUST be **13 months** (one full year plus one month for year-over-year comparison). The dashboard and durable-bus subscription owner is `@sbonoc/factory-operations`. Operational details — dashboard URL, panel inventory, replay procedure, alert rules, owner-team breakdown, weekly review cadence — are codified in [`instrumentation-plan.md`](instrumentation-plan.md). The pre-factory baseline measurements that the live dashboard MUST be compared against are codified in [`pre-factory-baselines.md`](pre-factory-baselines.md).

**Durable-bus platform (Q-5 resolved 2026-05-28 in PR #345 — `specs/2026-05-28-issue-337-factory-phase-0-foundations/spec.md`).** The blueprint factory instance MUST use **STACKIT Managed RabbitMQ** as the durable bus, with the SKE-hosted Strimzi-Kafka fallback codified in `instrumentation-plan.md` if a measurable trigger threshold from that plan is breached. The RabbitMQ deployment MUST use **stream queues** (`x-queue-type: stream`) for the C7 lifecycle event topic — streams provide the log-structured offset-replay semantics required by the C7 Replayability rule (any subscriber, including a newly attached one, can replay historic ranges from a known offset within the bus retention window) AND the durability required by the Durability rule (events are persisted to disk before producer return, replicated across the managed-cluster nodes). Per-ticket ordering is achieved by routing-key partitioning on the work-item ID across stream consumer groups. The 13-month retention configured on the stream queue satisfies the dashboard / forensic-cross-correlation windows; LogMe WORM (#334) remains the audit-of-record for compliance retention beyond the bus window, not a substitute for in-bus replayability.

### Consumer overlay

Consumer repos MUST declare their own dashboard target. The blueprint's target MUST NOT be inherited (cross-tenant dashboard pollution is REJECTED).

| Schema field | Type | Configuration location | Validation rule |
|---|---|---|---|
| `dashboard.platform` | enum string | `spec.factory_contract.dashboard.platform` in consumer `contract.yaml` | One of `stackit-managed-grafana`, `self-hosted-grafana`, `other`. |
| `dashboard.url` | string | `spec.factory_contract.dashboard.url` | HTTPS URL of the consumer's dashboard. |
| `dashboard.bus_subscription` | object | `spec.factory_contract.dashboard.bus_subscription` | Records the consumer-group identifier used to subscribe to the durable bus. |

### Open Decisions

- (none — Q-4 retention/owner and Q-5 durable-bus platform pick RESOLVED in PR #345 on 2026-05-28; concrete dashboard URLs and panel inventories are tracked in [`instrumentation-plan.md`](instrumentation-plan.md) under `@sbonoc/factory-operations` ownership and do not require a C7 amendment.)

Referenced by: #335, #336, #337

---

## Contract C8 — Consumer Surface (Blueprint → Consumer Inheritance)

Contract C8 enumerates the complete surface the blueprint ships so each consumer repo can instantiate its own per-consumer factory. The surface is partitioned into EXACTLY FOUR named categories (FR-013). Every enumerated surface item carries a **stability tier** (FR-015: `stable` / `preview` / `internal`) and an **extensibility tier** (FR-017: `sealed` / `parameterized` / `extensible`, default `extensible`).

The inheritance mechanism is the **existing** blueprint `contract.yaml` mechanism — no new machinery is introduced. Consumer repos that adopt the autonomous factory inherit C8 surface via the existing path that already exposes `docs/blueprint/`, module wrappers, Make targets, skill runbooks, and GitHub workflows to consumers.

### Category (a) — Documentation and ADRs

**Inheritance-mechanism note.** Rows marked `internal` below are blueprint-source-only normative references — the *rules* they encode are inherited via this C7/C8 contract surface and via the consumer-overlay parameter mechanism, but the *files themselves* are not mirrored to consumer repos (pruned at consumer init per `blueprint/contract.yaml` `source_artifact_prune_globs_on_init: docs/blueprint/architecture/decisions/ADR-*.md`, and absent from `template_sync_allowlist`). Per-instance parameterization callouts that previously sat on the ADR rows (FR-003 authorized-actor list, FR-007 ceiling values, FR-009 threshold values, FR-010 bounded-context catalogue) are inherited by consumers via the consumer-overlay surface, not via the ADR file. Rows marked `stable` are mirrored to consumers via `template_sync_allowlist` and ARE consumer-visible source-of-truth files.

| Surface item | Stability tier | Extensibility tier |
|---|---|---|
| `docs/blueprint/autonomous-factory/design-contracts.md` (this file) | `stable` | `sealed` (sole source of truth for C1–C8) |
| `docs/blueprint/autonomous-factory/` (directory; future runbooks land here) | `stable` | `extensible` |
| `docs/blueprint/architecture/decisions/ADR-issue-339-factory-design-contracts.md` | `internal` | n/a (normative reference) |
| `docs/blueprint/architecture/decisions/` (directory; future factory ADRs land here) | `stable` | `extensible` |
| `docs/blueprint/architecture/decisions/ADR-issue-337-factory-phase-0-foundations.md` (meta-ADR + sign-off envelope) | `internal` | n/a (normative reference) |
| `docs/blueprint/architecture/decisions/ADR-issue-337-llm-model-router-policy.md` (FR-001) | `internal` | n/a (normative reference) |
| `docs/blueprint/architecture/decisions/ADR-issue-337-persona-skill-contract.md` (FR-002) | `internal` | n/a (normative reference) |
| `docs/blueprint/architecture/decisions/ADR-issue-337-trigger-authorization-model.md` (FR-003) | `internal` | n/a (normative reference) |
| `docs/blueprint/architecture/decisions/ADR-issue-337-sovereignty-zdr-posture.md` (FR-004) | `internal` | n/a (normative reference; rule content also sealed under FR-017(b) item 4) |
| `docs/blueprint/architecture/decisions/ADR-issue-337-separation-of-duties-at-factory-velocity.md` (FR-005) | `internal` | n/a (normative reference) |
| `docs/blueprint/architecture/decisions/ADR-issue-337-reject-rerun-cap.md` (FR-006) | `internal` | n/a (normative reference; rule content also sealed under FR-017(b) item 5) |
| `docs/blueprint/architecture/decisions/ADR-issue-337-per-ticket-wall-clock-cost-ceiling.md` (FR-007) | `internal` | n/a (normative reference) |
| `docs/blueprint/architecture/decisions/ADR-issue-337-reviewer-model-heterogeneity.md` (FR-008) | `internal` | n/a (normative reference) |
| `docs/blueprint/architecture/decisions/ADR-issue-337-triage-size-threshold.md` (FR-009) | `internal` | n/a (normative reference) |
| `docs/blueprint/architecture/decisions/ADR-issue-337-light-decomposition-policy.md` (FR-010) | `internal` | n/a (normative reference) |
| `docs/blueprint/architecture/decisions/ADR-issue-337-c7-emission-mechanism.md` (FR-019 of #337 spec) | `internal` | n/a (normative reference; rule content also sealed under FR-017(b) item 8) |
| `docs/blueprint/autonomous-factory/instrumentation-plan.md` (FR-012/013/016) | `stable` | `extensible` (per-instance dashboard URLs, panel inventories, and durable-bus subscription details overlaid by consumer) |
| `docs/blueprint/autonomous-factory/pre-factory-baselines.md` (FR-014) | `stable` | `extensible` (each consumer records its own pre-factory baseline measurements in the same shape) |
| `docs/blueprint/autonomous-factory/triage-decomposition-data-feed.md` (FR-015) | `stable` | `extensible` (each consumer accumulates its own per-cycle triage/decomposition records in the same shape) |

### Category (b) — Terraform / Helm Module Wrappers

| Surface item | Stability tier | Extensibility tier | Owning ticket |
|---|---|---|---|
| `scripts/templates/infra/<ske-foundation-cluster-wrapper>` | `preview` | `parameterized` (per-consumer cluster name, region, node-pool sizing; consumer may point the wrapper at an existing SKE cluster) | #334 |
| `scripts/templates/infra/<stackit-secrets-manager-wrapper>` | `preview` | `parameterized` (per-consumer project + instance naming) | #334 |
| `scripts/templates/infra/<eso-cluster-secret-store-wrapper>` | `preview` | `parameterized` (per-consumer ClusterSecretStore name binding ESO to the consumer's STACKIT Secrets Manager instance) | #334 |
| `scripts/templates/infra/<logme-worm-retention-wrapper>` | `preview` | `parameterized` (13-month SOC 2 retention floor pinned per FR-017(b); per-consumer storage class and retention extension via parameter) | #334 |
| `scripts/templates/infra/<factory-egress-networkpolicy-wrapper>` | `preview` | `parameterized` (per-consumer LiteLLM gateway endpoint + optional additional permitted egress endpoints; default-deny posture is sealed) | #334 |
| `scripts/templates/infra/<factory-bot-identity-wrapper>` | `preview` | `parameterized` (per-consumer factory-bot GitHub login + fine-grained PAT scope; exact-string-equality detection rule is sealed per FR-017(b) item 1) | #334 |
| `scripts/templates/infra/<openhands-agent-server-wrapper>` | `preview` | `parameterized` | #335 |
| `scripts/templates/infra/<eso-factory-binding-wrapper>` | `preview` | `parameterized` (per-consumer ExternalSecret manifests that pull the LiteLLM credential out of the #334 ClusterSecretStore for the OpenHands runtime) | #335 |
| `scripts/templates/infra/<webhook-receiver-wrapper>` | `preview` | `parameterized` | #336 |

Every consumer-shipped module wrapper enumerated in this category MUST default to STACKIT-managed runtimes (SDD-C-013) and to local-first execution under the existing `docker-desktop-preferred` Kubernetes context policy (SDD-C-014) per NFR-OPS-002. The concrete per-wrapper realization is owned by #334/#335/#336.

### Category (c) — Make Targets and Skill Runbooks

| Surface item | Stability tier | Extensibility tier | Owning ticket |
|---|---|---|---|
| Make target `factory-bootstrap` (to be added by #334/#335) | `preview` | `extensible` | #334/#335 |
| Make target `factory-smoke` (to be added by #335) | `preview` | `extensible` | #335 |
| `.agents/skills/blueprint-sdd-step01-intake/` | `stable` | `extensible` (consumer may shadow under `.agents/skills/consumer/`) | #333 |
| `.agents/skills/blueprint-sdd-step02-resolve-questions/` | `stable` | `extensible` | #333 |
| `.agents/skills/blueprint-sdd-step03-spec-complete/` | `stable` | `extensible` | #333 |
| `.agents/skills/blueprint-sdd-step04-plan-slicer/` | `stable` | `extensible` | #333 |
| `.agents/skills/blueprint-sdd-step05-implement/` | `stable` | `extensible` | #333 |
| `.agents/skills/blueprint-sdd-step06-document-sync/` | `stable` | `extensible` | #333 |
| `.agents/skills/blueprint-sdd-step07-pr-packager/` | `stable` | `extensible` | #333 |
| `.agents/skills/blueprint-sdd-step08-agent-pr-review/` | `stable` | `extensible` (consumer may shadow under `.agents/skills/consumer/`) | #333 |
| `.agents/skills/blueprint-ticket-triage-size/` | `stable` | `extensible` (consumer may shadow under `.agents/skills/consumer/`) | #333 |
| `.agents/skills/blueprint-ticket-decompose-light/` | `stable` | `extensible` (consumer may shadow under `.agents/skills/consumer/`) | #333 |
| `.agents/skills/blueprint-agent-secret-scan/` | `stable` | `extensible` (consumer may shadow under `.agents/skills/consumer/`) | #333 |
| `.agents/skills/blueprint-agent-handoff/` | `stable` | `extensible` (consumer may shadow under `.agents/skills/consumer/`) | #333 |
| `.agents/skills/blueprint-spec-revision-handoff/` | `stable` | `extensible` (consumer may shadow under `.agents/skills/consumer/`) | #333 |
| `.agents/skills/blueprint-spec-review-prep/` | `stable` | `extensible` (consumer may shadow under `.agents/skills/consumer/`) | #333 |
| `.agents/skills/blueprint-human-review-prep/` | `stable` | `extensible` (consumer may shadow under `.agents/skills/consumer/`) | #333 |
| `.agents/skills/blueprint-pr-review-respond/` | `stable` | `extensible` (consumer may shadow under `.agents/skills/consumer/`) | #333 |
| `.agents/skills/blueprint-agent-stop-cleanup/` | `stable` | `extensible` (consumer may shadow under `.agents/skills/consumer/`) | #333 |
| `.agents/personas/po-analyst.md` | `stable` | `extensible` (consumer may shadow under `.agents/personas/consumer/`) | #333 |
| `.agents/personas/architect.md` | `stable` | `extensible` (consumer may shadow under `.agents/personas/consumer/`) | #333 |
| `.agents/personas/tech-lead.md` | `stable` | `extensible` (consumer may shadow under `.agents/personas/consumer/`) | #333 |
| `.agents/personas/implementer.md` | `stable` | `extensible` (consumer may shadow under `.agents/personas/consumer/`) | #333 |
| `.agents/personas/devsecops-qa.md` | `stable` | `extensible` (consumer may shadow under `.agents/personas/consumer/`) | #333 |
| `.agents/personas/doc-keeper.md` | `stable` | `extensible` (consumer may shadow under `.agents/personas/consumer/`) | #333 |
| `.agents/personas/security-reviewer.md` | `stable` | `extensible` (consumer may shadow under `.agents/personas/consumer/`) | #333 |
| `.agents/personas/architecture-reviewer.md` | `stable` | `extensible` (consumer may shadow under `.agents/personas/consumer/`) | #333 |
| `.agents/personas/contract-reviewer.md` | `stable` | `extensible` (consumer may shadow under `.agents/personas/consumer/`) | #333 |
| `.agents/personas/test-coverage-reviewer.md` | `stable` | `extensible` (consumer may shadow under `.agents/personas/consumer/`) | #333 |
| `.agents/personas/` (blueprint persona files) | `stable` | `extensible` (consumer may shadow under `.agents/personas/consumer/`) | #333 |

### Category (d) — GitHub App Manifest and Reusable Actions Workflows

| Surface item | Stability tier | Extensibility tier | Owning ticket |
|---|---|---|---|
| GitHub App manifest (`.github/factory-app-manifest.yml` or equivalent) | `preview` | `parameterized` (consumer installs on its own repo) | #336 |
| Reusable workflow `.github/workflows/factory-orchestrator.yml` | `preview` | `extensible` | #336 |
| Reusable workflow `.github/workflows/factory-webhook-bridge.yml` | `preview` | `extensible` | #336 |
| Reusable workflow `.github/workflows/factory-sign-off-collector.yml` | `preview` | `sealed` (the canonical sign-off phrases are sealed under FR-017(b)) | #336 |

### External service — LiteLLM access configuration (FR-014)

LiteLLM is a **pre-existing external service**. The blueprint does NOT ship a LiteLLM deployment. Consumer repos configure access to an existing LiteLLM gateway. The configuration shape lives at `spec.factory_contract.litellm` under a new top-level `spec.factory_contract:` block in `blueprint/contract.yaml` (Q-4 resolved 2026-05-28 in PR #340):

```yaml
spec:
  factory_contract:
    litellm:
      gateway_url: "https://litellm.example.stackit.cloud"
      auth_secret_ref:
        store: "factory-cluster-secret-store"   # ESO ClusterSecretStore name
        key:   "litellm/api-key"                # key within the store
      model_allowlist:
        - "claude-opus-4-7"
        - "claude-sonnet-4-6"
        - "claude-haiku-4-5"
```

Field shape:

| Field | Type | Definition |
|---|---|---|
| `gateway_url` | string (HTTPS URL) | LiteLLM gateway endpoint. |
| `auth_secret_ref.store` | string | ESO ClusterSecretStore name. Inline credentials MUST NOT be used. |
| `auth_secret_ref.key` | string | Key within the secret store containing the LiteLLM API token. |
| `model_allowlist` | list of strings | LiteLLM model identifiers the factory is permitted to call. |

Stability tier: `preview`. Extensibility tier: `parameterized` (consumer overlay required).

### Extensibility tier dimension (FR-017, AC-010)

Three values apply orthogonally to the stability tier:

- **`sealed`** — consumer instance MUST inherit identically; the artifact MUST NOT be shadowed, renamed, or overridden. Addition of net-new sibling artifacts of the same kind is permitted.
- **`parameterized`** — consumer instance MUST inherit the artifact identically; values MUST be populated via the `### Consumer overlay` schemas from FR-008 / FR-009 / FR-010 / FR-014 (Contracts C5, C6, C7, and the LiteLLM access shape above).
- **`extensible`** (default) — consumer instance is permitted to shadow the artifact by placing a same-named file under the consumer namespace (see FR-018 § Discovery convention below); the consumer-namespace file MUST take precedence. Addition of net-new sibling artifacts is permitted. Absence of a shadow leaves the blueprint artifact authoritative.

The default tier for any C8 surface item MUST be `extensible` unless the item is explicitly listed in the FR-017(b) sealed list below.

### FR-017(b) sealed list (pinned exactly — additions require a new C8 amendment via #339 sign-off)

1. **NFR-SEC-001 bot-identity exact-string rule** (Contract C5 § Identical rule) — consumers MUST NOT replace exact-string equality with substring, regex, or display-name heuristics.
2. **The four canonical sign-off phrases** from `AGENTS.md § Sign-off Phrases (Deterministic)` — `SPEC_PRODUCT_READY: approved`, `ARCHITECTURE_SIGNOFF: approved`, `SECURITY_SIGNOFF: approved`, `OPERATIONS_SIGNOFF: approved`. Consumers MUST NOT introduce plain-language equivalents.
3. **Contract C5 multi-author SoD identical rule** — at least two distinct human authors required; the factory bot does NOT count.
4. **#337 sovereignty / ZDR (Zero-Data-Retention) ADR identical-rule content** — sovereignty/ZDR posture is sealed across consumer instances.
5. **#337 reject-rerun cap identical-rule content** — the maximum-rerun count and the reject behaviour are sealed.
6. **Contract C7 minimum lifecycle-event field set** — the eleven fields (`event_id`, `ticket_id`, `parent_ticket_id`, `phase`, `persona`, `model`, `timestamp`, `outcome`, `rerun_round`, `owner_team`, `emitter`); consumers MUST NOT remove, rename, or change the type of any of these. Addition is permitted. (`event_id` and `emitter` were added in round-13 so that the C7 idempotency rule — `event_id = sha256(ticket_id|phase|rerun_round|emitter)` — is derivable from declared schema fields alone; their addition is permitted under the same "Addition is permitted" clause that this item itself carries.)
7. **Contract C7 emission-transport rule** — durable, replayable bus with async fire-and-forget semantics. Consumers MUST NOT replace this with synchronous dashboard writes.
8. **Contract C7 emission-mechanism rule** (per #337 FR-019 ADR, extended by ADR-issue-347-human-sdd-c7-symmetry.md) — C7 events MUST be emitted exclusively by the orchestrator (#333) for phase-boundary events, by the webhook handler (#336) for GitHub-observable events, and by the local-cli helper (`scripts/bin/sdd/c7_emit.py`, issue #347) for human-assisted SDD sessions. Personas, skills, OpenHands runtime, workspace pods, and LiteLLM MUST NOT emit C7 events. Consumers MUST NOT widen the emitter set or move emission into persona/skill output.
9. **Contract C2 SDD-artifact front-matter required-key set** — `id`, `artifact_kind`, `work_item_slug`, `owner_team`, `schema_version`; consumers MUST NOT remove or rename required keys. Addition is permitted.

### Consumer-extension discovery convention (FR-018, AC-011)

Consumer-authored extensions MUST live under namespaced subdirectories so the OpenHands loader and the GitHub Actions workflows can distinguish blueprint-inherited artifacts from consumer-authored ones **without parsing file front-matter**:

| Artifact kind | Blueprint namespace | Consumer namespace |
|---|---|---|
| Personas | `.agents/personas/` | `.agents/personas/consumer/` |
| Skills | `.agents/skills/<name>/` | `.agents/skills/consumer/<name>/` |
| SDD steps (slash-commands) | `blueprint-sdd-stepXY-<name>` | `consumer-sdd-stepXY-<name>` |

**Loader resolution.** When an `extensible` blueprint artifact has a same-basename file in the consumer namespace, the consumer-namespace file MUST take precedence. **Sealed-shadow rejection.** Shadow attempts against `sealed` artifacts MUST be rejected by the loader at startup; silent ignore is REJECTED.

**Shadow baseline recording.** Every consumer shadow file — a file whose basename matches a blueprint-namespace artifact — MUST carry a `blueprint-baseline-sha:` field in its YAML front-matter. The value MUST be the SHA-256 of the blueprint source artifact at shadow creation time. The upgrade skill (#342) uses this field to generate a precise upstream delta: the exact changes made to the blueprint artifact between the consumer's recorded baseline and the current blueprint content, independently of any edits the consumer has made to their own shadow. Absence of `blueprint-baseline-sha:` from a shadow file MUST be treated as a compliance gap by the upgrade skill; the skill MUST surface it as requiring a manual baseline stamp before the upgrade can proceed. Net-new consumer additions (files with no same-basename blueprint artifact) MUST NOT carry `blueprint-baseline-sha:` — no upstream baseline exists.

Worked examples — one per artifact kind:

**Persona shadow (extensible — consumer overrides blueprint persona).** A consumer repo wants its `architect` persona to require an additional acceptance criterion. The consumer creates `.agents/personas/consumer/architect.md` with the same basename. The loader resolves `architect` → `.agents/personas/consumer/architect.md` (consumer wins). The blueprint's `.agents/personas/architect.md` is shadowed for that consumer instance only. The shadow file MUST include `blueprint-baseline-sha:` in its front-matter, set to the SHA-256 of `.agents/personas/architect.md` at shadow creation time (required per Shadow baseline recording above).

**Skill addition (extensible — net-new consumer-authored skill).** A consumer repo adds a domain-specific skill not present in the blueprint, e.g., `payments-pci-checklist`. The consumer creates `.agents/skills/consumer/payments-pci-checklist/SKILL.md`. The skill is loaded under its consumer namespace and surfaced as `/payments-pci-checklist`. No blueprint artifact is shadowed; the addition is purely additive.

**SDD step addition (extensible — net-new consumer-authored SDD step).** A consumer repo wants to add a domain-specific PCI compliance review step. The consumer creates `.agents/skills/consumer-sdd-step01-pci-compliance-review/SKILL.md` (consumer-authored steps live in their own sequential whole-number series under the `consumer-sdd-step` namespace, mirroring the blueprint's `blueprint-sdd-stepXY-<name>` convention). Execution position relative to blueprint steps is declared in the consumer step's own metadata (e.g., `runs_after: blueprint-sdd-step06-document-sync`), not encoded in the step number. The new step is loaded under the `consumer-sdd-step` namespace; the blueprint steps remain authoritative and execute in their pinned order.

### Compatibility posture — semver factory contract version (FR-019, AC-012)

The factory contract version follows **semver**:

- **Major** versions MAY introduce breaking changes (removal or rename of a surface item, removal of a required field, narrowing of a value enum). Every major version MUST ship with explicit migration notes.
- **Minor** versions add new fields, new artifacts, or new optional capabilities without removing any existing surface.
- **Patch** versions are bug-fix only (no surface change).

Every enumerated C8 surface item MUST carry the factory-contract-version range it is compatible with (recorded in its owning module/skill/workflow metadata). The supported-major window (whether N-1 majors remain co-supported alongside N, and for how long) is owned by **#342** (Phase 1 factory upgrade process) — not pinned by this document.

This document declares **factory contract version `1.0.0`**.

### Upstream-candidate front-matter convention (FR-020, AC-012)

Consumer-authored extensions under FR-018 MAY carry `upstream-candidate: true` in their YAML front-matter to signal that the consumer believes the extension is general-purpose and a candidate for upstream contribution to the blueprint. Example:

```yaml
---
id: persona-architect-consumer-override
artifact_kind: persona
work_item_slug: consumer-domain-2026-05-28
owner_team: "@consumer-org/architecture"
schema_version: 1.0.0
blueprint-baseline-sha: "<sha256-of-blueprint-personas-architect-md-at-shadow-creation-time>"
upstream-candidate: true
---
```

The absence of the flag MUST be interpreted as **strictly local with no upstream intent**. Blueprint maintainers MUST NOT bear an obligation to accept upstream-candidate extensions; any upstream contribution MUST follow the normal blueprint SDD / sign-off flow.

### Open Decisions

- (none — Q-4 and Q-5 RESOLVED in PR #340 on 2026-05-28; concrete tier-marker authoring on individual personas/skills/workflows beyond the FR-017(b) sealed list is owned by #333/#334/#335/#336 under the default-`extensible` rule.)

Referenced by: #333, #334, #335, #336, #337, #342

---

## Coverage Summary

| Contract | Section type | Identical / Parameterized | `Referenced by:` |
|---|---|---|---|
| C1 — Branch naming | Identical | Identical | #333, #335, #336 |
| C2 — Spec directory layout + SDD-artifact front-matter | Identical | Identical | #333, #336, #338 |
| C3 — OpenHands ↔ persona mapping | Identical | Identical | #333, #335 |
| C4 — Integration AC format | Identical | Identical | #333, #336, #338 |
| C5 — Factory bot identity + SoD | Parameterized | 3 subsections + Open Decisions | #334, #335, #336, #337 |
| C6 — CODEOWNERS team slugs | Parameterized | 3 subsections + Open Decisions | #336, #337 |
| C7 — Metrics dashboard + event schema + emission transport | Parameterized | 3 subsections + Open Decisions | #335, #336, #337 |
| C8 — Consumer surface | Enumeration | 4 categories + LiteLLM + tier/extensibility/version/upstream-candidate | #333, #334, #335, #336, #337, #342 |

**Union of `Referenced by:`** = `{#333, #334, #335, #336, #337, #338, #342}` — covers the required set `{#333, #334, #335, #336, #337, #338}` per AC-002, plus #342 per AC-012.
