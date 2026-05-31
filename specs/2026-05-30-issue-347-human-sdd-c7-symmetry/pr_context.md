# PR Context

## Summary
- Work item: 2026-05-30-issue-347-human-sdd-c7-symmetry
- Objective: Extend Contract C7 (sealed-two-emitter rule, FR-019) to a sealed-three-emitter rule by adding `local-cli` for human-driven SDD sessions, with a deterministic CLI helper and a committed JSONL sink at `artifacts/c7/<slug>.jsonl`. Producer-side only — subscriber-side ingest (PR-event handlers in `services/webhook_handler/`) is deferred to companion issue #350.
- Scope boundaries: Blueprint repo only; seven SDD step skills (`blueprint-sdd-step01-intake` through `blueprint-sdd-step07-pr-packager`); no backfill of historical PRs; no consumer-repo emission in this iteration.

## Requirement Coverage
- Requirement IDs covered: FR-001..FR-007, FR-010..FR-015, NFR-SEC-001, NFR-REL-001, NFR-OPS-001, NFR-A11Y-001 (N/A — no UI surface).
- Deferred to #350: FR-008, FR-009 (reviewer-heterogeneity audit & webhook ingest), NFR-SEC-002, NFR-OBS-001, NFR-OBS-002 (subscriber-side observability).
- Acceptance criteria covered: AC-001, AC-002, AC-004, AC-006, AC-007.
- Contract surfaces changed: Contract C7 (`emitter.enum` widened to `{orchestrator, webhook-handler, local-cli}`, `persona.description`, `model.description`, extension-field vocabulary, `event_id` derivation for `local-cli`), pre-commit hook contract, `blueprint/contract.yaml` (`spec.spec_driven_development_contract.c7_emission` block).

## Key Reviewer Files
- Primary files to review first:
  - `docs/blueprint/autonomous-factory/design-contracts.md` (Contract C7 amendment)
  - `docs/blueprint/architecture/decisions/ADR-issue-347-human-sdd-c7-symmetry.md` (new ADR)
  - `docs/blueprint/governance/sdd_execution_guide.md` (operator-facing C7 section, env vars, FR-007 dedup semantics)
  - `scripts/lib/sdd/c7_emit.py` (helper library — `EmitC7EventUseCase`, `OptOutAuditUseCase`, `validate_event`)
  - `scripts/bin/sdd/c7_emit.py` (CLI entrypoint with NFR-REL-001 non-blocking failure path)
  - `.agents/skills/blueprint-sdd-step*/SKILL.md` (uniform C7 addendum across seven skills)
  - `scripts/bin/quality/check_sdd_assets.py` (FR-015(a) skill structural-sections scanner)
  - `.gitattributes` (FR-013 — `artifacts/c7/*.jsonl  linguist-generated=true  diff=none`)
- High-risk files:
  - Contract C7 schema (enum widening — subscribers in #350 must accept the three-emitter union)
  - `scripts/lib/sdd/c7_emit.py` `OptOutAuditUseCase` (FR-007 dedup is enforced by reading the sink file; tampering with the sink resets the scope — documented in `sdd_execution_guide.md`)

## Validation Evidence
- Required commands executed: pytest (66 tests), make quality-sdd-check, docs-build/smoke, manual AC-001 + AC-004 rehearsals — all pass
  - `uv run python3 -m pytest tests/sdd/ -v` → 43 passed, 0 failed (covers FR-001..FR-007, FR-013, NFR-REL-001, NFR-OPS-001, T-103)
  - `uv run python3 -m pytest tests/infra/test_sdd_asset_checker.py -q` → 17 passed (covers FR-015(a) skill structural-sections scanner)
  - `make quality-sdd-check` → zero violations
  - Manual AC-001 rehearsal: 7 sequential CLI invocations (`uv run python3 scripts/bin/sdd/c7_emit.py emit`) for ticket 999 across the seven SDD phases under `CLAUDE_CODE_MODEL=claude-opus-4-7` produced 7 JSONL lines in `artifacts/c7/rehearsal-999.jsonl`, all with `emitter=local-cli`, `execution_mode=human-assisted`, `model=claude-opus-4-7`, `rerun_round=0`, distinct `event_id`s — confirms one event per SDD step.
  - Manual AC-004 / FR-007 rehearsal: 3 sequential opt-out invocations (`BLUEPRINT_SDD_C7_EMIT=0 BLUEPRINT_SDD_C7_OPT_OUT_REASON=ci-rehearsal`) for ticket 999 under slug `optout-999` produced exactly 1 `c7-emission-opted-out` event in `artifacts/c7/optout-999.jsonl` with `opt_out_reason=ci-rehearsal`; invocations 2 and 3 short-circuited and logged the FR-007 dedup branch to stderr.
- Result summary: All in-scope FRs, NFRs, and ACs covered by automated tests or the documented manual rehearsal. No deterministic-check failures.
- Artifact references:
  - Rehearsal sinks captured under `/tmp/c7-rehearsal-7/artifacts/c7/rehearsal-999.jsonl` and `/tmp/c7-rehearsal-bool/artifacts/c7/optout-999.jsonl` (transient — not committed; documented here for reviewer reproducibility).
  - Reproduce: see the env-var table and step-by-step block in `docs/blueprint/governance/sdd_execution_guide.md` (operator-facing C7 section).

## Risk and Rollback
- Main risks: self-bootstrap paradox; unknown model sentinel; sink-file dedup scope boundary
  - Self-bootstrap paradox: this work item itself cannot emit C7 via the helper it authors; one-time backfill noted in implementation log but not required for merge.
  - Best-effort model ID: degrades the (deferred-to-#350) FR-008 reviewer-heterogeneity audit signal for operators whose coding assistant exposes no model env var (`unknown` sentinel resolved by `EnvVarModelResolver`).
  - Sink-file dedup boundary: FR-007 opt-out scope is the JSONL file itself; if an operator clears the sink (`git rm artifacts/c7/<slug>.jsonl`) and re-runs an SDD step, a fresh audit event will fire. Documented as expected behavior in `sdd_execution_guide.md`.
- Rollback strategy: A single PR reverts the contract amendment, ADR, helper, CLI, governance guide addendum, skill addenda, and asset-checker rule atomically. No migration required — no historical JSONL state exists pre-merge. Subscriber-side #350 can be merged or reverted independently because nothing in this PR depends on it.

## Deferred Proposals
- Proposal 1 (parked): Consumer-repo C7 emission — defer until `artifacts/c7/*.jsonl` is a stable contract on the blueprint side. Parked — trigger: triage: next-session — re-evaluate after first 30 PRs ship with local-cli post-merge. AGENTS.backlog.md entry added.
- Proposal 2 (rejected): JSONL line signing / HMAC — rejected at PR #348 closure. Q-2 resolved as "no signing"; committed-file + git-blame audit trail is sufficient anti-tamper. Consciously discarded. AGENTS.backlog.md entry added.
- Proposal 3 (parked): IDE-extension direct emission (VS Code / JetBrains) — helper remains CLI-only. Parked — trigger: on-scope: c7-emission — surfaces when any future work touches the C7 emission surface. AGENTS.backlog.md entry added.
- Proposal 4 (implemented): Consumer `.gitignore` `artifacts/c7/` exception — consumer repos that carry `artifacts/*` in their existing `.gitignore` will silently fail to stage JSONL files (git honours the ignore rule; `git add` exits 0 but no file is staged). Fixed by adding `scripts/templates/consumer/init/.gitignore.tmpl` seeded into consumer repos with the standard ignore rules including `artifacts/*` + `!artifacts/c7/` + `!artifacts/c7/*.jsonl`. Wired into `consumer_seeded` in `blueprint/contract.yaml` and its bootstrap mirror. Raised by @claude re-review of commit 598d725.
