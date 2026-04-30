# PR Context

## Summary
- Work item: 2026-04-30-issue-236-237-quality-gate-extensions
- Objective: Add pnpm lockfile pre-push gate (Issue #236) and consumer quality gate extension stubs (Issue #237) to the blueprint bootstrap template
- Scope boundaries: Additive-only changes to three template files and their live mirrors; no existing targets or hooks removed or modified

## Requirement Coverage
- Requirement IDs covered: FR-001, FR-002, FR-003, FR-004, FR-005, FR-006, FR-007, NFR-REL-001, NFR-UPG-001
- Acceptance criteria covered: AC-001 through AC-007
- Contract surfaces changed:
  - `.pre-commit-config.yaml` (template + live mirror) — two new hook blocks
  - `blueprint.generated.mk.tmpl` (template + live mirror) — two stub targets, quality-ci-blueprint extension
  - `scripts/templates/consumer/init/AGENTS.md.tmpl` — Consumer Extension Targets section added

## Key Reviewer Files
- Primary files to review first:
  - `scripts/templates/blueprint/bootstrap/.pre-commit-config.yaml` — two new hook blocks (pnpm-lockfile-sync, quality-consumer-pre-push)
  - `scripts/templates/blueprint/bootstrap/make/blueprint.generated.mk.tmpl` — two new stub targets, quality-ci-blueprint extended
  - `tests/blueprint/test_quality_contracts.py` — seven new contract assertions (T-101/T-102/T-201..T-204/T-211)
- High-risk files:
  - `make/blueprint.generated.mk` — live mirror of template; must remain byte-for-byte identical to `blueprint.generated.mk.tmpl`
  - `.pre-commit-config.yaml` — live mirror of template; drift causes `infra-validate` failure

## Validation Evidence
- Required commands executed: `make infra-contract-test-fast` (136 passed), `make quality-sdd-check` (PASS), `make quality-hardening-review` (PASS), `make infra-validate` (PASS), `make docs-build && make docs-smoke` (PASS)
- Result summary: All 136 contract assertions pass; 7 new assertions green; docs lint clean across 96 markdown files; no template drift
- Artifact references:
  - `specs/2026-04-30-issue-236-237-quality-gate-extensions/spec.md` — SPEC_READY: true, all sign-offs approved
  - `specs/2026-04-30-issue-236-237-quality-gate-extensions/traceability.md` — full FR/AC coverage
  - `specs/2026-04-30-issue-236-237-quality-gate-extensions/graph.json` — graph nodes and edges

## Risk and Rollback
- Main risks: `pnpm-lockfile-sync` hook runs `pnpm install --frozen-lockfile --prefer-offline` on pre-push when package.json changes; requires fresh local pnpm store (same failure mode as CI). Consumer stubs default to no-op so no consumer action required on upgrade.
- Rollback strategy: `git revert` the blueprint upgrade commit in the consumer repo; no runtime state, no database migrations, no infra changes

## Deferred Proposals
- Proposal 1 (not implemented): Parallel quality-hooks execution (Alternative D in ADR) — Parked — trigger: on-scope: quality — already tracked as `proposal(quality-hooks-keep-going-mode): parallel execution of independent quality-hooks checks` in AGENTS.backlog.md; no new entry required
