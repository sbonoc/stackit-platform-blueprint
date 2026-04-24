# ADR: Issue #189 — Prune-Glob Enforcement in Upgrade Validate and Postcheck

- **Status**: proposed
- **Date**: 2026-04-24
- **Issue**: #189
- **Work item**: `specs/2026-04-24-issue-189-prune-glob-enforcement/`

## Context

`blueprint/contract.yaml` declares `source_artifact_prune_globs_on_init` under
`spec.optional_modules.consumer_init`. These patterns (`specs/YYYY-MM-DD-*`,
`docs/blueprint/architecture/decisions/ADR-*.md`) are applied at init time to
remove blueprint-internal artifacts from generated-consumer repos.

The upgrade tooling has no awareness of these globs. During a consumer upgrade,
an operator who manually adds "missing" files (e.g. comparing the local repo
against the blueprint source) can re-introduce files that match the prune globs
with no warning from any upgrade gate. Reported from sbonoc/dhe-marketplace#40
— 25 ADRs re-introduced in a correction commit after PR review.

## Decision

Add a prune glob scan to `upgrade_consumer_validate.py` (post-apply validate
phase). The scan reads `source_artifact_prune_globs_on_init` from
`blueprint/contract.yaml`, glob-matches the consumer working tree, and emits
violations as a `prune_glob_check` section in `upgrade_validate.json`. A
non-empty violations list causes validate to exit non-zero. The postcheck reads
the `prune_glob_check` section from the validate report and adds
`prune-glob-violations` to `blocked_reasons` when violations are present.

The upgrade skill runbook receives an explicit required check step instructing
operators to verify prune globs after manual merge resolution.

## Alternatives Considered

**Option B — add to upgrade planner**: add `prune-glob-excluded` /
`prune-glob-violation` action types to `upgrade_consumer.py`. Rejected: requires
plan JSON schema changes, planner complexity, and is a pre-apply concern for a
violation that can only manifest after the operator has resolved merges.

## Consequences

- `scripts/lib/blueprint/upgrade_consumer_validate.py`: new `_scan_prune_glob_violations()` function; new `prune_glob_check` JSON section; updated status gate and summary counts; new stderr diagnostics.
- `scripts/lib/blueprint/upgrade_consumer_postcheck.py`: reads `prune_glob_check` from validate report; new `prune_glob_violations` section in postcheck JSON; new `prune-glob-violations` blocked reason.
- `.agents/skills/blueprint-consumer-upgrade/SKILL.md`: new required check step in Required Checks section.
- `docs/blueprint/architecture/execution_model.md`: document prune glob check in validate phase.
- No plan/apply JSON schema changes. No new environment variables. No CLI flag changes.
- Tests: unit tests for scan function (positive, negative, skipped); integration tests for validate and postcheck exit codes.
