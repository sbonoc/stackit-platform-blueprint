# Specification

## Spec Readiness Gate (Blocking)
<!-- SPEC_PRODUCT_READY=true: intake gate — Product sign-off only; unlocks agent ADR drafting.
     SPEC_READY=true: implementation gate — all sign-offs required; unlocks coding. -->
- SPEC_READY: false
- SPEC_PRODUCT_READY: false
- Open questions count: 0
- Unresolved alternatives count: 0
- Unresolved TODO markers count: 0
- Pending assumptions count: 0
- Open clarification markers count: 0
- Product sign-off: pending
- Architecture sign-off: pending
- Security sign-off: pending
- Operations sign-off: pending
- Missing input blocker token: BLOCKED_MISSING_INPUTS
- ADR path: docs/blueprint/architecture/decisions/ADR-issue-347-human-sdd-c7-symmetry.md
- ADR status: proposed
- SPEC_READY_EXCEPTION: none
- authorized-by: none

## Applicable Guardrail Controls (Normative)
- Applicable control IDs: SDD-C-001, SDD-C-002, SDD-C-003, SDD-C-004, SDD-C-005, SDD-C-006, SDD-C-007, SDD-C-008, SDD-C-009, SDD-C-010, SDD-C-011, SDD-C-012, SDD-C-013, SDD-C-014, SDD-C-016, SDD-C-017, SDD-C-019, SDD-C-020, SDD-C-021, SDD-C-023, SDD-C-024
- Control exception rationale: none

## Implementation Stack Profile (Normative)
- Backend stack profile: python_plus_fastapi_pydantic_v2
- Frontend stack profile: vue_router_pinia_onyx
- Test automation profile: pytest_vitest_playwright_pact
- Agent execution model: specialized-subagents-isolated-worktrees
- Managed service preference: stackit-managed-first
- Managed service exception rationale: none
- Runtime profile: local-first-docker-desktop-kubernetes
- Local Kubernetes context policy: docker-desktop-preferred
- Local provisioning stack: crossplane-plus-helm
- Runtime identity baseline: eso-plus-argocd-plus-keycloak
- Local-first exception rationale: none

## Objective
- Business outcome: Human-driven SDD sessions emit Contract C7 lifecycle events with the same eleven-field minimum schema and the same deterministic envelope construction as autonomous factory runs — so once the subscriber-side ingest lands (deferred follow-up #350, blocked by #336), the metrics dashboard, the reviewer-heterogeneity audit predicate (#337), and the future Central Brain index (Epic #343) see one coherent SDD timeline regardless of who (or what) drove the work. This work item ships the producer side only: helper, JSONL sink, opt-out audit, skill addenda, contract amendments, and structural-integrity scanner.
- Success metric: After this work item ships, ≥ 95% of new PRs opened on the blueprint repo carry an `artifacts/c7/<slug>.jsonl` sink with ≥ 1 C7 event per executed SDD step, measured over the first 30 PRs post-merge; opt-outs (counted by presence of `c7-emission-opted-out` events in the JSONL sink) MUST be ≤ 5% of new PRs over the same window. Bus-side success metrics (Grafana panel coverage, reviewer-heterogeneity audit pair completeness from #337) are scoped to follow-up #350.

## Normative Requirements

### Functional Requirements (Normative)
- FR-001 The C7 `emitter` JSON Schema enum (`docs/blueprint/autonomous-factory/design-contracts.md` Contract C7 § Emission mechanism) MUST be widened from `{orchestrator, webhook-handler}` to EXACTLY THREE values `{orchestrator, webhook-handler, local-cli}`. Any value outside this enum MUST be REJECTED by subscribers.
- FR-002 Every SDD step skill listed in `CLAUDE.md` § Skills (`blueprint-sdd-step01-intake` through `blueprint-sdd-step07-pr-packager`) MUST emit EXACTLY ONE C7 lifecycle event per step execution via a deterministic shared helper. The helper MUST be the sole writer of `emitter: local-cli` C7 events. LLM personas MUST NOT write C7 envelope fields and MUST NOT have direct write access to the JSONL sink.
- FR-003 The helper MUST append emitted events to `artifacts/c7/<work-item-slug>.jsonl` in the work-item working tree, one canonical JSON object per line, in append-only order. The file MUST be committed to the work-item branch.
- FR-004 For `emitter: local-cli` events the `event_id` field MUST be derived as `sha256(ticket_id|phase|rerun_round|emitter)` — the four-input variant. The five-input webhook discriminator variant MUST NOT be used; the JSONL append is the local single source of truth.
- FR-005 For `emitter: local-cli` events the `persona` field MUST be the SDD step skill basename (e.g., `blueprint-sdd-step01-intake`). The `model` field MUST be the best-effort LLM model identifier exposed by the operator's coding assistant, OR the sealed sentinel string `unknown` when no model identifier is resolvable. The eleven-field minimum schema MUST remain typed `string` and required — no nullable types and no emitter-conditional required-set variants.
- FR-006 Every C7 event from any emitter MUST carry the extension field `execution_mode` (string enum, two values): `autonomous` when `emitter ∈ {orchestrator, webhook-handler}`, `human-assisted` when `emitter: local-cli`. The field MUST be carried under `additionalProperties: true` and MUST NOT be added to the eleven-field required minimum.
- FR-007 Emission MUST be opt-out-able via a sealed mechanism: the environment variable `BLUEPRINT_SDD_C7_EMIT=0` SHALL suppress JSONL writes for the current shell session. The opt-out SHALL be audited: the first SDD step executed under opt-out MUST emit EXACTLY ONE `c7-emission-opted-out` extension event with reason carried in `additionalProperties.opt_out_reason`; subsequent steps under the same opt-out scope MUST NOT re-emit.
  Opt-out surface: env var only (Q-1 → Option A, owner comment 2026-05-30). Env var travels through subshell invocation without per-skill flag plumbing; the opt-out audit event ensures discoverability.

- FR-010 Contract C7 (`docs/blueprint/autonomous-factory/design-contracts.md`) MUST be amended to: (a) widen issue #339 sealed-emitter rule from two emitters to three; (b) widen the JSON Schema `emitter.enum` to include `local-cli`; (c) extend the `persona` and `model` field descriptions to enumerate the `local-cli` sentinel rules; (d) document `execution_mode` in the extension-field vocabulary; (e) document the four-input `event_id` derivation for `local-cli`. The bootstrap mirror at `scripts/templates/blueprint/bootstrap/docs/blueprint/autonomous-factory/design-contracts.md` MUST be re-synced via `scripts/lib/docs/sync_blueprint_template_docs.py`.
- FR-011 A new ADR `docs/blueprint/architecture/decisions/ADR-issue-347-human-sdd-c7-symmetry.md` MUST be authored (Status: proposed at PR open, advanced to accepted on merge). The ADR MUST record decisions D-1 through D-4 from issue #347 verbatim and MUST reference Contract C7 + issue #339 sealed-emitter rule + `ADR-issue-337-c7-emission-mechanism.md` as the architectural baseline being extended.
- FR-012 Every `.agents/skills/blueprint-sdd-step*/SKILL.md` (seven skills) MUST receive a uniform "## C7 Emission" section that instructs the skill to invoke the shared helper at step boundary. The section text MUST be identical across all seven skills (modulo the per-skill `phase` enum value).
- FR-013 A `.gitattributes` rule `artifacts/c7/*.jsonl  linguist-generated=true  diff=none` MUST be added so PR diff renderers hide the JSONL sink by default.
- FR-014 Backfill of historical PRs MUST NOT be performed. Only PRs opened after this work item merges are audited under the `local-cli` emission surface.
- FR-015 `scripts/bin/quality/check_sdd_assets.py` MUST be extended with a SKILL.md structural integrity scanner that: (a) asserts every `.agents/skills/*/SKILL.md` contains the required structural sections (`## Guardrails`, `## Workflow`, `## Required Report Format`); and (b) asserts the "## C7 Emission" addendum is byte-identical (modulo per-skill `phase` enum value) across all seven `blueprint-sdd-step*/SKILL.md` files. Both checks MUST run as part of the existing `make quality-sdd-check` target with no new make target required. Incorporated from parked proposal `issue-247-step05-slice-done-gate`.

### Non-Functional Requirements (Normative)
- NFR-SEC-001 The shared helper (`scripts/lib/sdd/c7_emit.py`) MUST be the sole writer of `emitter: local-cli` C7 events. LLM personas (Claude Code, Codex, Cursor, etc.) MUST NOT bypass the helper to write JSONL lines directly. This preserves the issue #339 sealed-emitter rule anti-LLM-hallucination property: the LLM calls the skill as a tool; the skill (deterministic Python) computes the envelope and appends.
- NFR-REL-001 Helper failure (disk full, malformed input, sink path not writable) MUST NOT block SDD step execution. The helper MUST log the failure to stderr and return success to its caller. SDD step pass/fail MUST be determined by the step's own work product, NOT by C7 emission success.
- NFR-OPS-001 The helper MUST compute `event_id` deterministically from the four-input formula so identical `(ticket_id, phase, rerun_round, emitter)` tuples produce byte-identical `event_id` values regardless of when or where the helper runs. Duplicate lines in the local JSONL file after rebase / squash / manual conflict resolution are tolerated — the subscriber-side dedupe contract (delivered by follow-up #350) absorbs them; the local file is append-only and the helper never rewrites prior lines.
- NFR-A11Y-001 N/A — this work item adds no UI surface.

## Normative Option Decision
- Option A: Third sealed emitter `local-cli` with skill-as-tool deterministic helper and JSONL sink committed to branch. Subscriber-side ingest (parsing the JSONL out of the PR head SHA and republishing onto the durable bus) is delivered by follow-up issue #350 once #336 (the webhook handler runtime) exists. (D-4 + D-3 locked; ingest delivery cleaved into #350 to avoid conflating the local emission contract with the unrelated webhook-handler greenfield build.)
- Option B: Direct push from local helper to the durable bus over network (no JSONL sink, no #336 ingest). REJECTED — local environments do not have credentials for the STACKIT-managed bus; would require credential distribution to every operator; would lose the git-history audit trail.
- Option C: Ship the local emission contract AND build the #336 webhook handler in the same PR. REJECTED — #336 is its own Phase 1 ticket of Epic #332 with its own contracts surface, sign-off lifecycle, and acceptance criteria; bundling would balloon the PR and obscure the human-assisted emission decisions that are this work item's actual subject.
- Selected option: OPTION_A
- Rationale: Option A preserves the issue #339 sealed-emitter rule anti-LLM-hallucination property by keeping emission deterministic and local. The committed JSONL sink doubles as a git-history audit trail that survives even if the bus pipeline regresses. Splitting the ingest path into #350 lets this work item land independently and exercise the operator-facing surface immediately; the ingest predicate ships when its prerequisite runtime (#336) does. Option B's network coupling and credential distribution would invert the local-first runtime baseline (SDD-C-014); Option C would bundle two distinct architectural surfaces into one un-reviewable PR.

## Contract Changes (Normative)
- Config/Env contract: New environment variable `BLUEPRINT_SDD_C7_EMIT` (default `1`; set `0` to opt out). Documented in `blueprint/contract.yaml` under `spec.spec_driven_development_contract.c7_emission`.
- API contract: none (this work item ships producer side only; the subscriber-side PR-event handlers in #336 are scoped to follow-up #350).
- OpenAPI / Pact contract path: none
- Event contract: Contract C7 § Emission mechanism widens `emitter` enum to three values; adds `local-cli` sentinel rules for `persona` and `model`; documents `execution_mode` extension field; documents four-input `event_id` derivation for `local-cli`. Bootstrap mirror re-synced.
- Make/CLI contract: Implementations MUST surface the helper through deterministic CLI invocation `python3 scripts/bin/sdd/c7_emit.py emit --phase <enum> --skill <basename> [--outcome <enum>]`; skill runbooks call this CLI rather than importing Python directly.
- Docs contract: New ADR `ADR-issue-347-human-sdd-c7-symmetry.md`. Update to `ADR-issue-337-c7-emission-mechanism.md` to reference the three-emitter rule (or alternatively a new "Extension" subsection). Update to `docs/blueprint/governance/sdd_execution_guide.md` describing the new `BLUEPRINT_SDD_C7_EMIT` env var and the JSONL sink path. Bootstrap mirrors re-synced for both.

## Blueprint Upstream Defect Escalation (Normative)
- Upstream issue URL: none
- Temporary workaround path: none
- Replacement trigger: none
- Workaround review date: none

## Normative Acceptance Criteria
- AC-001 A human SDD session executed from `make spec-scaffold` through `gh pr create --draft` on a fresh work item MUST produce AT LEAST ONE C7 event per executed SDD step in `artifacts/c7/<slug>.jsonl`. A full lifecycle (Step 01 through Step 07) MUST produce ≥ 7 events.
- AC-002 Every emitted `local-cli` event MUST validate against the amended C7 JSON Schema with `additionalProperties: true`; each event MUST carry `emitter: local-cli` AND `execution_mode: human-assisted`.
- AC-004 Setting `BLUEPRINT_SDD_C7_EMIT=0` and running any SDD step MUST suppress the per-step C7 event AND MUST emit EXACTLY ONE `c7-emission-opted-out` extension event on the first step under opt-out for the given work-item slug. Verified by unit test on the helper.
- AC-006 The `.gitattributes` rule MUST hide `artifacts/c7/*.jsonl` from the GitHub PR diff renderer. Verified manually on this work item's own Draft PR.
- AC-007 `make quality-sdd-check`, `make docs-build`, `make docs-smoke`, and the new helper's pytest unit/contract suite MUST pass with zero failures after all amendments + bootstrap mirror sync.

## Informative Notes (Non-Normative)
- Context: The current Contract C7 sealed two-emitter rule (issue #339 sealed-emitter rule) was authored to prevent LLM-hallucinated audit events. Human-driven SDD sessions were initially excluded as out-of-scope. With Epic #343 (Central Brain) in the pipeline and the solo-operator topology dominating real activity, the exclusion now leaves a substantial blind spot. This work item extends the sealed rule to three emitters by applying the same "deterministic wrapper around an LLM-driven phase boundary" pattern to local SDD execution.
- Tradeoffs:
  - Committed JSONL sink adds files to PR diffs. Mitigated by `.gitattributes` `diff=none` rule (FR-013).
  - Best-effort model ID with `unknown` sentinel (D-2) means the reviewer-heterogeneity audit predicate (#337) will need to treat both-unknown pairs as inconclusive once it ingests local-cli events; that exemption is part of follow-up #350 (subscriber-side work blocked by #336).
  - Skill-as-tool pattern requires every step skill runbook to call the helper. Mitigated by uniform addendum text (FR-012) and the runbook compatibility checker.
  - JSONL sink is written today but not yet ingested onto the durable bus (subscriber-side ingest deferred to #350, blocked by #336). The local sink is a forward-compatible storage format — events committed under #347 will be ingested by #350 the first time the handler runs against any PR carrying the sink.
- Clarifications (all resolved 2026-05-30 via owner PR comment):
  - Q-2 JSONL line signing: No signing in v1 (Option A). Git history + `git blame` is the integrity surface for committed files; HMAC with an operator-held key is security theater. Park signing if/when the threat model requires keys outside operator reach.
  - Q-3 Self-bootstrap: This work item #347 is exempt from C7 emission (Option A). The helper does not exist for the steps that author it; emission becomes obligatory for the first new work item started after #347 merges. Backfilled events would be reconstructions that dilute the audit surface's truth claim.
  - Q-4 Model detection fallback chain: Env var priority chain `$CLAUDE_CODE_MODEL` → `$CODEX_MODEL` → `$CURSOR_MODEL` → `unknown` sentinel (Option A). Env vars are operator-controlled, stable across assistant releases, and trivially testable. Session-log parsing is fragile and a version-coupling smell.
  - Q-5 `rerun_round` semantics: Count prior committed events for the same `(ticket_id, phase)` tuple in the local JSONL file; `rerun_round=0` on first emission (Option A). Self-contained; matches orchestrator semantics; keeping it at 0 always would make every rerun collide on the same `event_id` and get deduped away.
  - Q-6 Skill addendum scope: Seven `blueprint-sdd-stepXX-*` step skills only (Option A). `blueprint-sdd-traceability-keeper` requires a separate "auxiliary phase" extension with its own audit-predicate semantics — tracked as a follow-up issue (see Explicit Exclusions). Consumer-ops skills are a different bounded context and contract surface.

## Explicit Exclusions
- IDE-extension / VS Code / JetBrains integration — helper is CLI-only.
- Automatic backfill of historical PRs — only post-merge PRs are audited (FR-014).
- Cross-repo aggregation of consumer-repo C7 events — blueprint repo only; consumer-repo emission is a follow-up after `artifacts/c7/*.jsonl` is a stable contract.
- `blueprint-sdd-traceability-keeper` skill emission — excluded (Q-6 → Option A). Requires a separate "auxiliary phase" contract extension; tracked as a follow-up issue.
- Consumer-ops skills (`blueprint-consumer-ops`, `blueprint-consumer-upgrade`) emission — outside the SDD lifecycle; different bounded context and contract surface.
- Self-bootstrap emission for this work item #347 — excluded (Q-3 → Option A). Helper does not exist for the steps that author it; emission obligatory from the first new work item after #347 merges.
- Subscriber-side ingest of the JSONL sink onto the durable bus — deferred to follow-up issue #350 (blocked by #336). The deferred surface includes: the three PR-event handlers in #336 (`pull_request.opened`/`synchronize`/`reopened`), the schema-validate + dedupe + republish flow, the reviewer-heterogeneity audit predicate (#337) `unknown`-model exemption, the Grafana `execution_mode` panel facet, and the bus-side integration test. PR #348 ships the producer side only; subscriber side ships when #336 runtime exists.
