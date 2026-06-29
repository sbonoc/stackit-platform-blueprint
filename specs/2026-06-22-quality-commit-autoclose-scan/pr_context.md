# PR Context — quality-commit-autoclose-scan

## Work Item Summary

**Issue:** #380 — chore(quality): commit-message auto-close-keyword scan for must-not-auto-close issues
**Track:** bypass-track chore (SPEC_READY_EXCEPTION: chore; authorized-by: sbonoc)
**Spec:** specs/2026-06-22-quality-commit-autoclose-scan/spec.md

## Problem Statement

Parent issue #361 was auto-closed TWICE on 2026-06-22 when PR commit bodies narrated the auto-close bug class and were matched by GitHub keyword parser. The existing PARENT_AUTOCLOSE_REGEX test guard covers generated content only, not commit-message bodies on the branch being pushed. This PR ships the generalised pre-push version.

## Deliverables

1. scripts/lib/quality/autoclose_regex.py — shared regex constant; per-spec test imports from here.
2. scripts/bin/quality/check_pr_commit_autoclose.py — CLI entrypoint: parses Tracks #N from open PR, scans PR title/body + commit log, honours override token, falls back to .github/no-auto-close-issues.yml.
3. .pre-commit-config.yaml — new quality-pr-commit-autoclose-check pre-push entry.
4. Makefile — new quality-pr-commit-autoclose-check target.
5. tests/blueprint/test_quality_commit_autoclose.py — unit tests T-001..T-006.
6. Bootstrap template sync — script + config land in template-synced paths.

## Review Guide

- Primary files to review first:
  - scripts/lib/quality/autoclose_regex.py — canonical regex; single source of truth
  - scripts/bin/quality/check_pr_commit_autoclose.py — CLI entrypoint and public API
  - tests/blueprint/test_quality_commit_autoclose.py — T-001..T-006 unit tests

## Acceptance Gate

uv run python3 -m pytest tests/blueprint/test_quality_commit_autoclose.py tests/blueprint/test_issue_361_file_children_script.py -q — MUST pass.

## Risks

- R1: Per-spec test refactor (PARENT_AUTOCLOSE_REGEX import) could break existing tests if module path is wrong — mitigated by T-006 + full suite run before merge.
- R2: gh pr view rate-limiting on repos with many PRs — mitigated by single-call design + exit 0 on auth failure (never block push).
- R3: Override token could mask real violations if misused — accepted; token is visible in PR body for reviewer audit.
