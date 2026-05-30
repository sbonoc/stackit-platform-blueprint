# Architecture

## Context
- Work item: 2026-05-30-issue-347-human-sdd-c7-symmetry — third sealed C7 emitter `local-cli` for human-driven SDD sessions
- Owner: @sbonoc (solo-operator topology — see project memory `feedback_solo_operator_topology`)
- Date: 2026-05-30

## Stack and Execution Model
- Backend stack profile: python_plus_fastapi_pydantic_v2 (helper module + #336 ingest extension)
- Frontend stack profile: vue_router_pinia_onyx (N/A — no UI surface introduced)
- Test automation profile: pytest_vitest_playwright_pact (pytest unit + contract tests on helper; pytest integration test on #336 ingest)
- Agent execution model: specialized-subagents-isolated-worktrees (this work item itself; the artifact being delivered targets human + LLM-assisted SDD sessions)

## Problem Statement
- What needs to change and why: Contract C7 (`docs/blueprint/autonomous-factory/design-contracts.md`) currently exempts human-driven SDD sessions from lifecycle event emission. The exemption was authored on the assumption that local activity would be a marginal fraction of real SDD throughput. Under the solo-operator topology, local activity is a substantial fraction, and the exemption now leaves the metrics dashboard undercounting throughput, the FR-008 reviewer-heterogeneity audit silent on human runs, and the Central Brain index (Epic #343) blind to half its potential training corpus. This work item extends the sealed two-emitter rule (FR-019) to a sealed three-emitter rule by adding `local-cli` and codifying the deterministic CLI helper + committed JSONL sink + #336 PR-event ingest pipeline.
- Scope boundaries:
  - Blueprint repo only — consumer-repo C7 emission is a follow-up after `artifacts/c7/*.jsonl` is a stable contract.
  - Seven SDD step skills (`blueprint-sdd-step01-intake` through `blueprint-sdd-step07-pr-packager`) — cross-cutting `blueprint-sdd-traceability-keeper` and consumer-ops skills are pending Q-6 resolution and default-excluded.
  - PRs opened after this work item merges — no backfill of historical PRs.
- Out of scope:
  - IDE-extension / VS Code / JetBrains integration (helper is CLI-only).
  - Direct push to durable bus from operator workstation (rejected — Option B in ADR).
  - JSONL line signing / HMAC (pending Q-2 resolution; default no).
  - Self-bootstrap emission for this work item #347 (pending Q-3 resolution; default no).
  - Cross-repo aggregation of consumer-repo C7 events.

## Bounded Contexts and Responsibilities
- Context A — SDD local execution surface (this work item authors)
  - Owns the deterministic CLI helper (`scripts/lib/sdd/c7_emit.py` + `scripts/bin/sdd/c7_emit.py`).
  - Owns the JSONL sink contract: path `artifacts/c7/<work-item-slug>.jsonl`, append-only, one canonical JSON object per line, committed to the work-item branch.
  - Owns the uniform "## C7 Emission" addendum text in every `.agents/skills/blueprint-sdd-step*/SKILL.md`.
  - Owns the `BLUEPRINT_SDD_C7_EMIT` env var + opt-out audit event.
- Context B — Webhook handler (#336) ingest extension
  - Owns three new PR-event handlers: `pull_request.opened`, `pull_request.synchronize`, `pull_request.reopened`.
  - Owns the fetch-at-head-SHA logic via the GitHub contents API (existing GitHub App installation token).
  - Owns schema validation + dedupe-by-event_id + republish onto the durable bus.
- Context C — Contract surface (#339 amendment + this ADR)
  - Owns the widened `emitter` enum (`{orchestrator, webhook-handler, local-cli}`).
  - Owns the new ADR (`ADR-issue-347-human-sdd-c7-symmetry.md`) and the cross-link annotation on `ADR-issue-337-c7-emission-mechanism.md`.
  - Owns the `execution_mode` extension-field vocabulary documentation.
  - Owns the bootstrap mirror re-sync.
- Context D — Orchestrator (#333) — UNCHANGED
  - The autonomous emission path is the template `local-cli` mirrors. No code change in #333; only documentation cross-link.
- Context E — Downstream observers
  - Grafana dashboard (Blueprint instance) consumes `execution_mode` as a facet for autonomous vs human-assisted segmentation.
  - Central Brain ([#343](https://github.com/sbonoc/stackit-platform-blueprint/issues/343)) starts receiving `human-assisted` events on first new work item post-merge.
  - FR-008 audit predicate runs against `local-cli`-emitted events with the documented `unknown`-model exemption.

## High-Level Component Design
- Domain layer:
  - `LifecycleEvent` value object (Pydantic v2 model) — the eleven-field C7 minimum schema + `execution_mode` extension; lives in `scripts/lib/sdd/c7_emit.py`.
  - `EventIdDerivation` strategy — four-input variant for `local-cli` (`sha256(ticket_id|phase|rerun_round|emitter)`); reuses the orchestrator's hash format for byte-for-byte parity.
- Application layer:
  - `EmitC7EventUseCase` — orchestrates env var resolution → model resolution (best-effort chain) → rerun_round computation (read prior JSONL entries for the `(ticket_id, phase)` tuple) → envelope build → append.
  - `OptOutAuditUseCase` — checks `BLUEPRINT_SDD_C7_EMIT=0`; on first invocation per work-item slug, emits the `c7-emission-opted-out` extension event; subsequent invocations no-op silently.
- Infrastructure adapters:
  - `JsonlSinkAdapter` — file-system writer with `O_APPEND` semantics; creates `artifacts/c7/` directory on first write; idempotent on conflict.
  - `EnvVarModelResolver` — reads `$CLAUDE_CODE_MODEL`, `$CODEX_MODEL`, `$CURSOR_MODEL` in priority order; returns `unknown` sentinel on miss.
  - `JsonlReaderAdapter` — reads prior committed events to compute `rerun_round`; tolerates missing file (returns 0).
- Presentation/API/workflow boundaries:
  - CLI entrypoint `scripts/bin/sdd/c7_emit.py emit --phase <enum> --skill <basename> [--outcome <enum>] [--ticket <id>]` is the sole public surface; skill runbooks invoke this CLI rather than importing Python directly.
  - Pre-commit hook (`.pre-commit-config.yaml` extension) schema-validates `artifacts/c7/<slug>.jsonl` so malformed events are rejected at commit time, not at #336 ingest time.

## Integration and Dependency Edges
- Upstream dependencies:
  - Contract C7 § Emission mechanism (#339 — the sealed two-emitter rule that becomes the sealed three-emitter rule here). Hard dependency on the round-18 contract surface that landed in PR #345 (merged commit `35f5d9d`).
  - ADR-issue-337-c7-emission-mechanism.md (#337 — the architectural baseline being extended). Same PR #345 dependency.
  - GitHub App installation token (existing #336 credential — no new credential surface).
- Downstream dependencies:
  - #336 webhook handler: gains three new event-type handlers and the GitHub contents API fetch logic. No new HTTP endpoint exposed.
  - Every `.agents/skills/blueprint-sdd-step*/SKILL.md` runbook: gains the uniform "## C7 Emission" section (FR-012).
  - Grafana dashboard (Blueprint instance, Contract C7 § Blueprint instance): consumes `execution_mode` as a panel facet (NFR-OBS-001).
  - Central Brain (Epic #343): consumes `human-assisted` events on first new work item post-merge.
  - FR-008 reviewer-heterogeneity audit predicate: gains the `unknown`-model exemption (NFR-OBS-002).
- Data/API/event contracts touched:
  - C7 JSON Schema (`emitter.enum`, `persona.description`, `model.description` widened; `execution_mode` documented in extension-field vocabulary).
  - GitHub webhook event vocabulary (#336 adds three new event-type handlers).
  - Pre-commit hook contract (`.pre-commit-config.yaml` gains schema validation entry).
  - `blueprint/contract.yaml` (`spec.spec_driven_development_contract.c7_emission` block added).

## Non-Functional Architecture Notes
- Security: The deterministic helper is the SOLE writer of `emitter: local-cli` C7 events (NFR-SEC-001). LLM personas MUST NOT bypass the helper to write JSONL lines directly — the FR-019 anti-LLM-hallucination property is preserved by structural pattern (skill-as-tool), not by network boundary. No new credential surface is introduced (NFR-SEC-002): the helper writes a local file (no credentials needed); #336 fetches via its existing GitHub App installation token. The committed JSONL sink doubles as a git-history audit trail (`git blame` surfaces tampering).
- Observability: Every `local-cli` event is observable on the Grafana dashboard with `execution_mode` as a panel facet (NFR-OBS-001). The FR-008 audit predicate runs against `local-cli` events with the `unknown`-model exemption (NFR-OBS-002 — pair carrying `model: unknown` on both sides marks the pair inconclusive rather than emitting a `rotation-violation` rejection). The `c7-emission-opted-out` extension event provides operator-counted opt-out telemetry.
- Reliability and rollback: Helper failure (disk full, malformed input, sink path not writable) MUST log to stderr and return success to the calling skill — SDD step pass/fail is determined by the step's own work product, NOT by C7 emission success (NFR-REL-001). Rollback path: a single PR can revert the contract amendment + ADR + helper + skill addenda + #336 handlers atomically; no migration is required because no historical JSONL state exists.
- Monitoring/alerting: The opt-out rate (count of `c7-emission-opted-out` events / count of new PRs) is a Grafana panel; threshold-based alert fires if opt-out > 5% rolling 30-day. Helper-failure logs are surfaced via the operator's existing stderr capture (no platform-side ingest for helper failures — local-first by design).

## Risks and Tradeoffs
- Risk 1 — Self-bootstrap paradox. This work item authors the helper but its own SDD steps cannot use the helper (the helper does not exist yet). Mitigation: spec § Explicit Exclusions documents the self-bootstrap exemption (pending Q-3 confirmation); emission becomes obligatory for the first new work item started after #347 merges.
- Risk 2 — Best-effort model ID degrades the FR-008 audit signal. Operators whose coding assistant does not expose a model env var emit `unknown`; pair-of-unknowns is inconclusive. Mitigation: NFR-OBS-002 documents the exemption; Grafana panel surfaces the `inconclusive` count separately so SREs can act if the rate climbs.
- Risk 3 — Rebase / squash conflict in `artifacts/c7/<slug>.jsonl`. The append-only file can grow duplicate lines if an operator rebases a branch with prior commits. Mitigation: NFR-OPS-001 — helper is idempotent on rebase; subscriber-side dedupe at #336 absorbs duplicates by `event_id`. Operators MAY manually deduplicate the file as part of conflict resolution, but they are not required to.
- Risk 4 — `.gitattributes` `diff=none` rule is per-clone configurable. A reviewer with `--no-renames` or a non-default git config could still see the JSONL in their diff. Mitigation: cosmetic-only risk; the JSONL is by design committed and reviewable on demand. Documented in `pr_context.md` as a known cosmetic edge case.
- Risk 5 — Skill addendum drift. If the seven step skills' addendum text diverges over time, schema-evolution cost balloons. Mitigation: a runbook-compatibility checker (extension to existing `check_sdd_assets.py`) asserts the addendum text is byte-identical modulo the per-skill `phase` enum value; CI gate fails on drift.
- Tradeoff 1 — Skill-as-tool indirection adds one process boundary per SDD step (the helper CLI invocation). The latency cost is negligible (≪ 100ms per call), and the determinism benefit (no LLM in the emission path) is load-bearing for the anti-hallucination property the entire C7 contract rests on.
- Tradeoff 2 — Committed JSONL adds files to PR diffs. The `.gitattributes` `diff=none` rule hides it for typical reviewers; on-demand inspection remains possible. The audit-trail benefit (git history of every C7 event) is worth the cosmetic cost.
- Tradeoff 3 — `BLUEPRINT_SDD_C7_EMIT=0` as env-var-only (Q-1 recommendation) means CLI `--no-c7` discoverability is lost. The opt-out audit event captures the reason at first opt-out, so operators discovering the env var via the audit event log catch up quickly; the flag-plumbing-through-seven-skills cost outweighs the marginal discoverability gain.
