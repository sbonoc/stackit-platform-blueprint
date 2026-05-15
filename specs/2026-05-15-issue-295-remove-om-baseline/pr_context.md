# PR Context

## Summary
- Work item: 2026-05-15-issue-295-remove-om-baseline — verify and close OpenMetadata baseline removal
- Objective: Issue #295 asked whether OpenMetadata should remain hardcoded in blueprint templates or be removed. Audit found the templates were already clean; `AGENTS.decisions.md` already recorded the decision. This PR closes the governance loop: backlog updated, issue closed, decision confirmed.
- Scope: `AGENTS.backlog.md` (P1 entries updated, #248 unblocked) + this spec as the audit record. No template or code changes.

## Requirement Coverage
- Acceptance criteria covered: AC-001 (`AGENTS.backlog.md` no longer lists #295 as open, #248 gate removed), AC-002 (GitHub issue #295 closed with explanation comment)

## Key Reviewer Files
- Primary files to review first:
  - `AGENTS.backlog.md` — P1 section updated; #295, #277, #275 marked closed; #248 unblocked
  - `specs/2026-05-15-issue-295-remove-om-baseline/spec.md` — audit finding and decision rationale

## Validation Evidence
- Grep of all `scripts/templates/blueprint/bootstrap/` paths for `openmetadata|OpenMetadata|open_metadata` → zero matches
- `AGENTS.decisions.md` line 81: "OpenMetadata remains consumer/product-owned and is out of blueprint scope unless a future decision records otherwise" — decision already in place
- `make quality-hooks-fast` — PASS

## Risk and Rollback
- No code or template changes. Rollback is a revert of the `AGENTS.backlog.md` edit.
- No consumer upgrade impact — templates were already clean before this PR.

## Deferred Proposals
- None. If a second consumer adopts OpenMetadata in the future, the opt-in module wrapper can be evaluated at that point with two real usage patterns to compare (YAGNI deferred correctly).
