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

- **Reserve and verify the bot identity on GitHub** — deferring ticket: **#334** (Confidential K8s + bot provisioning); resolve-by deadline: **Phase 1 close (Epic #332 acceptance gate)**. Placeholder: `<TBD: reserve-and-verify in #334>`.

Referenced by: #334, #335, #336, #337

---

## Contract C6 — CODEOWNERS Team Slugs (Parameterized)

### Identical rule

Every factory instance MUST resolve the four canonical sign-off roles (Product, Architecture, Security, Operations) to **real GitHub team slugs**, each carrying **at least two members**. A single collapsed pool is REJECTED (would break the multi-author SoD rule from Contract C5 in small organisations).

Each role's team slug MUST be referenced from the consumer repo's `.github/CODEOWNERS` for the paths that role owns.

### Blueprint instance

The blueprint factory instance maps the four canonical roles to (Q-2 resolved 2026-05-28 in PR #340):

| Role | Blueprint team slug |
|---|---|
| Product | `@sbonoc/factory-product` |
| Architecture | `@sbonoc/factory-architecture` |
| Security | `@sbonoc/factory-security` |
| Operations | `@sbonoc/factory-operations` |

Bounded-context teams are kept **separate** from the four sign-off teams (no role-tagging committee). The provisional bounded-context list is `{factory, infra, docs, governance}`; the concrete list is owned by #337.

### Consumer overlay

Consumer repos MUST declare their own four team slugs. The blueprint's slugs MUST NOT be inherited.

| Schema field | Type | Configuration location | Validation rule |
|---|---|---|---|
| `codeowners.product` | string | `spec.factory_contract.codeowners.product` in consumer `contract.yaml` | GitHub team slug starting with `@`; the underlying team MUST have ≥2 members. |
| `codeowners.architecture` | string | `spec.factory_contract.codeowners.architecture` | Same as above. |
| `codeowners.security` | string | `spec.factory_contract.codeowners.security` | Same as above. |
| `codeowners.operations` | string | `spec.factory_contract.codeowners.operations` | Same as above. |

### Open Decisions

- **Concrete blueprint-instance team provisioning** (create teams on GitHub, populate ≥2 members each, full bounded-context enumeration) — deferring ticket: **#337** (Phase 0 ADRs, CODEOWNERS, instrumentation); resolve-by deadline: **#337 close**. Placeholder: `<TBD: concrete team provisioning in #337>`.

Referenced by: #336, #337

---

## Contract C7 — Metrics Dashboard + Event Schema (Parameterized)

### Identical rule

Every factory instance MUST emit a lifecycle event for every persona phase transition. The minimum event field set is a named JSON schema with explicit types and nullability per field:

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "FactoryLifecycleEventV1",
  "type": "object",
  "additionalProperties": true,
  "required": [
    "ticket_id",
    "parent_ticket_id",
    "phase",
    "persona",
    "model",
    "timestamp",
    "outcome",
    "rerun_round",
    "owner_team"
  ],
  "properties": {
    "ticket_id":        { "type": "string",  "description": "GitHub issue identifier (e.g., '339')." },
    "parent_ticket_id": { "type": ["string", "null"], "description": "Parent issue identifier for decomposed children; null for top-level tickets." },
    "phase":            { "type": "string",  "enum": ["intake", "resolve-questions", "spec-complete", "plan-slicer", "implement", "document-sync", "pr-packager"] },
    "persona":          { "type": "string",  "description": "Persona file basename (matches Contract C3 microagent name)." },
    "model":            { "type": "string",  "description": "LLM model identifier resolved via LiteLLM (e.g., 'claude-opus-4-7')." },
    "timestamp":        { "type": "string",  "format": "date-time", "description": "RFC 3339 UTC timestamp at emission." },
    "outcome":          { "type": "string",  "enum": ["success", "rejected", "retried", "human-handoff"] },
    "rerun_round":      { "type": "integer", "minimum": 0, "description": "Zero on first attempt; incremented on each persona rerun." },
    "owner_team":       { "type": "string",  "description": "GitHub team slug owning the work item (matches C2 front-matter `owner_team`)." }
  }
}
```

Consumers MUST NOT remove, rename, or change the type of any of the nine minimum fields. Addition of further fields is permitted (sealed under FR-017(b); see Contract C8).

**Emission transport (sealed).** Events MUST be emitted to a **durable, replayable bus** with the following semantics:

- **Durability** — events MUST be persisted before the producer returns; transient in-memory queues MUST NOT be used.
- **Replayability** — subscribers MUST be able to replay historic ranges (consumer-position tracking is the subscriber's responsibility, not the producer's).
- **Async fire-and-forget** — the factory runtime MUST NOT block on subscriber acknowledgement or on any downstream availability. A subscriber outage MUST NOT degrade factory throughput.
- **Multi-subscriber** — the bus MUST support multiple independent consumer groups so that the metrics dashboard (Contract C7 § Blueprint instance), the GitHub Actions webhook bridge (#336), and downstream observers (Epic #343 Central Brain ingest) can each subscribe with independent positions.

Synchronous writes to a dashboard MUST NOT replace the bus emission. The Grafana dashboard target (Blueprint instance) MUST subscribe to the bus, not receive synchronous writes.

**Cross-link to downstream observers.** The future Central Brain index (Epic #343) MUST subscribe to the same bus with its own consumer group. Any change to the nine-field minimum schema MUST go through #339 sign-off — out-of-band schema changes by downstream consumers are REJECTED.

### Blueprint instance

The blueprint factory metrics dashboard target is **STACKIT-managed Grafana** via the existing `OBSERVABILITY_ENABLED` module declared in `blueprint/contract.yaml` (Q-3 resolved 2026-05-28 in PR #340). The dashboard subscribes to the durable bus rather than receiving synchronous writes.

### Consumer overlay

Consumer repos MUST declare their own dashboard target. The blueprint's target MUST NOT be inherited (cross-tenant dashboard pollution is REJECTED).

| Schema field | Type | Configuration location | Validation rule |
|---|---|---|---|
| `dashboard.platform` | enum string | `spec.factory_contract.dashboard.platform` in consumer `contract.yaml` | One of `stackit-managed-grafana`, `self-hosted-grafana`, `other`. |
| `dashboard.url` | string | `spec.factory_contract.dashboard.url` | HTTPS URL of the consumer's dashboard. |
| `dashboard.bus_subscription` | object | `spec.factory_contract.dashboard.bus_subscription` | Records the consumer-group identifier used to subscribe to the durable bus. |

### Open Decisions

- **Concrete STACKIT-managed durable-bus platform pick** (e.g., STACKIT-managed Kafka or equivalent SKE-hosted fallback) — deferring ticket: **#337** (instrumentation plan; availability spike required as a Phase 0 prerequisite); resolve-by deadline: **#337 Phase 0 close**. Placeholder: `<TBD: durable-bus platform pick in #337 Phase 0>`. This contract pins the durability / replay / async semantics; the platform pick is deferred per AC-014.
- **Concrete blueprint-instance dashboard URLs and instrumentation wiring** — deferring ticket: **#337**; resolve-by deadline: **#337 close**. Placeholder: `<TBD: concrete dashboard URLs in #337>`.

Referenced by: #335, #336, #337

---

## Contract C8 — Consumer Surface (Blueprint → Consumer Inheritance)

Contract C8 enumerates the complete surface the blueprint ships so each consumer repo can instantiate its own per-consumer factory. The surface is partitioned into EXACTLY FOUR named categories (FR-013). Every enumerated surface item carries a **stability tier** (FR-015: `stable` / `preview` / `internal`) and an **extensibility tier** (FR-017: `sealed` / `parameterized` / `extensible`, default `extensible`).

The inheritance mechanism is the **existing** blueprint `contract.yaml` mechanism — no new machinery is introduced. Consumer repos that adopt the autonomous factory inherit C8 surface via the existing path that already exposes `docs/blueprint/`, module wrappers, Make targets, skill runbooks, and GitHub workflows to consumers.

### Category (a) — Documentation and ADRs

| Surface item | Stability tier | Extensibility tier |
|---|---|---|
| `docs/blueprint/autonomous-factory/design-contracts.md` (this file) | `stable` | `sealed` (sole source of truth for C1–C8) |
| `docs/blueprint/autonomous-factory/` (directory; future runbooks land here) | `stable` | `extensible` |
| `docs/blueprint/architecture/decisions/ADR-issue-339-factory-design-contracts.md` | `stable` | `sealed` |
| `docs/blueprint/architecture/decisions/` (directory; future factory ADRs land here) | `stable` | `extensible` |

### Category (b) — Terraform / Helm Module Wrappers

| Surface item | Stability tier | Extensibility tier | Owning ticket |
|---|---|---|---|
| `scripts/templates/infra/<consumer-confidential-k8s-wrapper>` | `preview` | `parameterized` (overlay schema in consumer `contract.yaml`) | #334 |
| `scripts/templates/infra/<openhands-agent-server-wrapper>` | `preview` | `parameterized` | #335 |
| `scripts/templates/infra/<eso-factory-binding-wrapper>` | `preview` | `parameterized` | #335 |
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
        - "claude-haiku-4-5-20251001"
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
6. **Contract C7 minimum lifecycle-event field set** — the nine fields (`ticket_id`, `parent_ticket_id`, `phase`, `persona`, `model`, `timestamp`, `outcome`, `rerun_round`, `owner_team`); consumers MUST NOT remove, rename, or change the type of any of these. Addition is permitted.
7. **Contract C7 emission-transport rule** — durable, replayable bus with async fire-and-forget semantics. Consumers MUST NOT replace this with synchronous dashboard writes.
8. **Contract C2 SDD-artifact front-matter required-key set** — `id`, `artifact_kind`, `work_item_slug`, `owner_team`, `schema_version`; consumers MUST NOT remove or rename required keys. Addition is permitted.

### Consumer-extension discovery convention (FR-018, AC-011)

Consumer-authored extensions MUST live under namespaced subdirectories so the OpenHands loader and the GitHub Actions workflows can distinguish blueprint-inherited artifacts from consumer-authored ones **without parsing file front-matter**:

| Artifact kind | Blueprint namespace | Consumer namespace |
|---|---|---|
| Personas | `.agents/personas/` | `.agents/personas/consumer/` |
| Skills | `.agents/skills/<name>/` | `.agents/skills/consumer/<name>/` |
| SDD steps (slash-commands) | `blueprint-sdd-stepXY-<name>` | `consumer-sdd-stepXY-<name>` |

**Loader resolution.** When an `extensible` blueprint artifact has a same-basename file in the consumer namespace, the consumer-namespace file MUST take precedence. **Sealed-shadow rejection.** Shadow attempts against `sealed` artifacts MUST be rejected by the loader at startup; silent ignore is REJECTED.

Worked examples — one per artifact kind:

**Persona shadow (extensible — consumer overrides blueprint persona).** A consumer repo wants its `architect` persona to require an additional acceptance criterion. The consumer creates `.agents/personas/consumer/architect.md` with the same basename. The loader resolves `architect` → `.agents/personas/consumer/architect.md` (consumer wins). The blueprint's `.agents/personas/architect.md` is shadowed for that consumer instance only.

**Skill addition (extensible — net-new consumer-authored skill).** A consumer repo adds a domain-specific skill not present in the blueprint, e.g., `payments-pci-checklist`. The consumer creates `.agents/skills/consumer/payments-pci-checklist/SKILL.md`. The skill is loaded under its consumer namespace and surfaced as `/payments-pci-checklist`. No blueprint artifact is shadowed; the addition is purely additive.

**SDD step addition (extensible — net-new consumer-authored SDD step).** A consumer repo wants to insert a domain-specific compliance step between the blueprint `blueprint-sdd-step06-document-sync` and `blueprint-sdd-step07-pr-packager`. The consumer creates `.agents/skills/consumer-sdd-step65-pci-compliance-review/SKILL.md` (the `65` slot expresses "between 6 and 7"; sequential whole numbers per the blueprint naming convention). The new step is loaded under the `consumer-sdd-step` namespace; the blueprint steps remain authoritative and execute in their pinned order.

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
