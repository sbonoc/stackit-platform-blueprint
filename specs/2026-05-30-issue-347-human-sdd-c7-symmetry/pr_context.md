# PR Context

## Summary
- Work item: 2026-05-30-issue-347-human-sdd-c7-symmetry
- Objective: Extend Contract C7 (sealed-two-emitter rule, FR-019) to a sealed-three-emitter rule by adding `local-cli` for human-driven SDD sessions, with a deterministic CLI helper, committed JSONL sink at `artifacts/c7/<slug>.jsonl`, and #336 PR-event ingest at `pull_request.opened/synchronize/reopened`. Restores parity between human SDD throughput and autonomous factory throughput on the metrics dashboard, the FR-008 reviewer-heterogeneity audit, and the Central Brain index (Epic #343).
- Scope boundaries: Blueprint repo only; seven SDD step skills (`blueprint-sdd-step01-intake` through `blueprint-sdd-step07-pr-packager`); no backfill of historical PRs.

## Requirement Coverage
- Requirement IDs covered: FR-001..FR-014, NFR-SEC-001, NFR-SEC-002, NFR-OBS-001, NFR-OBS-002, NFR-REL-001, NFR-OPS-001, NFR-A11Y-001
- Acceptance criteria covered: AC-001..AC-007
- Contract surfaces changed: Contract C7 (`emitter.enum`, `persona.description`, `model.description`, extension-field vocabulary, `event_id` derivation), GitHub webhook handler event vocabulary (3 new event types), pre-commit hook contract, `blueprint/contract.yaml` (`spec.spec_driven_development_contract.c7_emission` block).

## Key Reviewer Files
- Primary files to review first:
  - `docs/blueprint/autonomous-factory/design-contracts.md` (Contract C7 amendment)
  - `docs/blueprint/architecture/decisions/ADR-issue-347-human-sdd-c7-symmetry.md` (new ADR)
  - `scripts/lib/sdd/c7_emit.py` (helper module)
  - `scripts/bin/sdd/c7_emit.py` (CLI entrypoint)
  - `.agents/skills/blueprint-sdd-step*/SKILL.md` (uniform addendum across seven skills)
  - `services/webhook_handler/...` (three new PR-event handlers + fetch logic)
- High-risk files:
  - Contract C7 schema (enum widening — breaks subscribers that hard-code the two-emitter union)
  - `services/webhook_handler/...` (new fetch path against GitHub contents API)

## Validation Evidence
- Required commands executed: (pending — Step 5 implementation phase)
- Result summary: (pending)
- Artifact references: (pending — manual rehearsal screenshot for AC-005 captured on PR merge)

## Risk and Rollback
- Main risks: Self-bootstrap paradox (this work item itself cannot emit C7 via the helper it authors); best-effort model ID degrades FR-008 audit signal for operators whose coding assistant exposes no model env var; rebase/squash conflict in append-only JSONL absorbed by subscriber-side dedupe.
- Rollback strategy: A single PR reverts the contract amendment, ADR, helper, skill addenda, and #336 handlers atomically; no migration is required because no historical JSONL state exists pre-merge.

## Deferred Proposals
- Proposal 1 (not implemented): Consumer-repo C7 emission — defer until `artifacts/c7/*.jsonl` is a stable contract on the blueprint side. Re-evaluate after first 30 PRs ship locally.
- Proposal 2 (not implemented): JSONL line signing / HMAC — pending Q-2 resolution; default no, on the assumption that committed-file + git-blame audit trail is sufficient anti-tamper.
- Proposal 3 (not implemented): IDE-extension / VS Code / JetBrains direct emission — helper remains CLI-only in this iteration.
