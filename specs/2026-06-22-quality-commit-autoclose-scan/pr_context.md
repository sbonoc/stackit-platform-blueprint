# PR Context — quality-commit-autoclose-scan

## Summary
- Work item: 2026-06-22-quality-commit-autoclose-scan (issue #380, PR #381)
- Objective: Ship a pre-push quality check (`quality-pr-commit-autoclose-check`) that scans PR title, PR body, and branch commit messages for GitHub auto-close keywords targeting must-not-auto-close issues. Protected issues are sourced from `Tracks #N` markers in the open PR body, with fallback to `.github/no-auto-close-issues.yml`. Motivated by parent issue #361 being auto-closed twice on 2026-06-22 when commit bodies narrated the auto-close bug class.
- Scope boundaries: Quality CI tooling only — no runtime service, no HTTP routes, no UI. New files in `scripts/lib/quality/` and `scripts/bin/quality/` (blueprint-managed roots). Pre-push hook and Make target added. Bootstrap template synced. Existing per-spec `PARENT_AUTOCLOSE_REGEX` refactored to import from the new module (NFR-MAINT-001).

## Requirement Coverage
- Requirement IDs covered: REQ-001, REQ-002, REQ-003, REQ-004, REQ-005, REQ-006, REQ-007, REQ-008, NFR-PERF-001, NFR-REL-001, NFR-MAINT-001, AC-001, AC-002, AC-003, AC-004, AC-005, AC-006
- Acceptance criteria covered: AC-001 (T-001 — 11 regex assertions pass), AC-002 (T-002 — Tracks #N parsing + allow-auto-close override), AC-003 (T-003 — commit-log scanner detects violation with commit hash), AC-004 (T-004 — fallback config file + no-PR exit-0 path), AC-005 (T-005 — exit-code integration assertions), AC-006 (T-006 — existing test_issue_361_file_children_script.py passes after PARENT_AUTOCLOSE_REGEX import refactor)
- Contract surfaces changed: `.pre-commit-config.yaml` (new `quality-pr-commit-autoclose-check` pre-push entry); `scripts/templates/blueprint/bootstrap/.pre-commit-config.yaml` (mirrored); `make/blueprint.generated.mk` (new target rendered from template); `scripts/templates/blueprint/bootstrap/make/blueprint.generated.mk.tmpl` (template source); `docs/reference/generated/core_targets.generated.md` (new row)

## Key Reviewer Files
- Primary files to review first:
  - `scripts/lib/quality/autoclose_regex.py` — canonical regex; single source of truth for all consumers (REQ-003, NFR-MAINT-001)
  - `scripts/bin/quality/check_pr_commit_autoclose.py` — CLI entrypoint; `fetch_pr_body_title`, `parse_protected_issues`, `scan_surface`, `scan_commit_log`, `main`
  - `tests/blueprint/test_quality_commit_autoclose.py` — T-001..T-006, 28 unit assertions
- High-signal supporting files: `tests/blueprint/test_issue_361_file_children_script.py` (NFR-MAINT-001 refactor — `PARENT_AUTOCLOSE_REGEX` replaced with `build_pattern(361)` import); `.pre-commit-config.yaml` + `scripts/templates/blueprint/bootstrap/.pre-commit-config.yaml` (REQ-006 hook wiring); `scripts/lib/quality/test_pyramid_contract.json` (new test file classified under `unit` scope)

## Validation Evidence
- Required commands executed: `uv run python3 -m pytest tests/blueprint/test_quality_commit_autoclose.py tests/blueprint/test_issue_361_file_children_script.py -v`, `uv run python3 -m pytest tests/ -q`, `make quality-hooks-fast`, `make quality-hardening-review`, `make quality-spec-pr-ready`
- Result summary: All quality gates pass. 28 unit tests green (T-001..T-006). Full pytest suite (1475 tests) green in 184.50s. TDD red→green cycle: failing tests committed in `a8e04dd6`, implementation in `cd0ad810`. `quality-hooks-fast` 11/11 PASS (2026-06-29). `quality-hardening-review` PASS (bypass-track active, chore, authorized-by: sbonoc).

## Risk and Rollback
- Main risks: R1 — per-spec test refactor (`PARENT_AUTOCLOSE_REGEX` import) could break existing tests if module path is wrong — mitigated by T-006 + full suite run confirming 1475/1475 pass. R2 — `gh pr view` rate-limiting on repos with many PRs — mitigated by single-call design + exit 0 on auth failure (NFR-REL-001 — never blocks push). R3 — override token (`#allow-auto-close: #N`) could mask real violations if misused — accepted; token is visible in PR body for reviewer audit.
- Rollback strategy: Remove `quality-pr-commit-autoclose-check` from `.pre-commit-config.yaml` and `scripts/templates/blueprint/bootstrap/.pre-commit-config.yaml`; remove the Make target from `scripts/templates/blueprint/bootstrap/make/blueprint.generated.mk.tmpl` and re-render. The script, regex module, and tests can remain in place without effect — the hook is the only activation point. No consumer data or infrastructure affected.

## Review Guide
- Primary files to review first:
  - `scripts/lib/quality/autoclose_regex.py` — canonical regex; single source of truth
  - `scripts/bin/quality/check_pr_commit_autoclose.py` — CLI entrypoint and public API
  - `tests/blueprint/test_quality_commit_autoclose.py` — T-001..T-006 unit tests

## Deferred Proposals
- Proposal 1 (multi-repo consumer CI enforcement): Parked — trigger: on-scope: quality — consumer repo workflow changes require separate intake; pre-push is the primary safety layer for this cut. Not filed as an issue (low urgency, no current blocker). Recorded in AGENTS.backlog.md under `### on-scope: quality`.
- Proposal 2 (inline per-line override token): Rejected at PR closure — per-PR override covers all known real cases; inline per-line token adds regex + parsing complexity with no current use case.
- Proposal 3 (stale issue-number detection): Rejected at PR closure — adds a second GitHub API call, violates NFR-PERF-001 constraint (≤ 1 API call per invocation), no proportional safety gain.
