# PR Context

## Summary
- Work item: issue-163 — Fresh-environment simulation in upgrade smoke gate
- Objective: Add `make blueprint-upgrade-fresh-env-gate` — runs `infra-validate` and `blueprint-upgrade-consumer-postcheck` inside a clean git worktree (HEAD checkout) after the postcheck gate passes, exposing CI-invisible failures caused by bootstrap-created files persisting in the developer working tree.
- Scope boundaries: new shell wrapper + Python module + make target + contract declaration; additive-only changes to SKILL.md, quickstart.md, troubleshooting.md, and their templates; no changes to existing gate behaviour.

## Requirement Coverage
- Requirement IDs covered: FR-001, FR-002, FR-003, FR-004, FR-005, FR-006, NFR-SEC-001, NFR-OBS-001, NFR-REL-001, NFR-OPS-001
- Acceptance criteria covered: AC-001 (fail on missing file), AC-002 (pass when files reproduce), AC-003 (error on worktree creation failure), AC-004 (EXIT trap on SIGINT/SIGTERM), AC-005 (worktree absent after successful run)
- Contract surfaces changed: `blueprint/contract.yaml` and template — new required target `blueprint-upgrade-fresh-env-gate`; `make/blueprint.generated.mk` and template — new `.PHONY` + recipe; `SKILL.md` and template — step 6 added to upgrade sequence.

## Key Reviewer Files
- Primary files to review first:
  - `scripts/bin/blueprint/upgrade_fresh_env_gate.sh`
  - `scripts/lib/blueprint/upgrade_fresh_env_gate.py`
  - `tests/blueprint/test_upgrade_fresh_env_gate.py`
- High-risk files: `blueprint/contract.yaml` (required target list); `make/blueprint.generated.mk` and `scripts/templates/blueprint/bootstrap/make/blueprint.generated.mk.tmpl` (must stay in sync)

## Validation Evidence
- Required commands executed: `pytest tests/blueprint/test_upgrade_fresh_env_gate.py` — 16 passed in 2.44s; `make quality-sdd-check` — clean; `make infra-validate` — clean; `make quality-hardening-review` — clean; `make quality-docs-check-changed` — clean after regenerating core_targets.generated.md and classifying test file
- Result summary: all 16 tests green (8 unit + 8 integration); no TODO/FIXME/dead code; docs and test pyramid contract up to date; infra-validate confirms makefile and contract in sync
- Artifact references: `specs/2026-04-23-issue-163-fresh-env-smoke-gate/`, `docs/blueprint/architecture/decisions/ADR-20260423-issue-163-fresh-env-smoke-gate.md`

## Risk and Rollback
- Main risks: (1) Worktree creation fails if the issue-163 branch is already checked out elsewhere (workaround: detached-HEAD mode is used by design). (2) Gate may produce false negatives if divergences are env-var-driven rather than file-based (follow-up work item).
- Rollback strategy: remove `blueprint-upgrade-fresh-env-gate` from `blueprint/contract.yaml` and make target list, revert SKILL.md step 6 — gate is additive and has no side effects on existing upgrade targets.

## Deferred Proposals
- none
