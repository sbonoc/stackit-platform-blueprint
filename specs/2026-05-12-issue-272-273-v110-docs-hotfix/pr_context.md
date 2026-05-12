# PR Context

## Summary

- Work item: specs/2026-05-12-issue-272-273-v110-docs-hotfix
- Objective: Fix two v1.10.0 regressions in `scripts/lib/docs/site.sh`. #272: `--ignore-workspace` removed from three pnpm invocations, causing `docs/node_modules/` to be silently empty on consumers whose root `pnpm-workspace.yaml` excludes `docs/`. #273: `_docs_assert_pnpm_version` error message omits the root `package.json#packageManager` field and CI corepack prepare pin as pnpm version-truth sources.
- Scope boundaries: `scripts/lib/docs/site.sh` (sole implementation file — atomic flag additions + one message rewrite); `tests/infra/test_docs_site_sh_issue_272_273.py` (new regression tests); `docs/platform/consumer/troubleshooting.md` + bootstrap template mirror (consumer docs). No new Make targets, no new scripts, no contract changes.

## Requirement Coverage

- Requirement IDs covered: FR-001, FR-002, NFR-SEC-001, NFR-OBS-001, NFR-REL-001, NFR-OPS-001, NFR-A11Y-001 (N/A), AC-001, AC-002
- Acceptance criteria covered: AC-001 — `--ignore-workspace` in all three pnpm functions (verified by `Issue272PnpmIgnoreWorkspaceTests`, 3 tests GREEN); AC-002 — `log_fatal` names "root package.json" and "corepack prepare" (verified by `Issue273PnpmVersionErrorMessageTests`, 2 tests GREEN)
- Contract surfaces changed: no new Make targets; `make docs-install`/`docs-build`/`docs-smoke` behavior corrected (false-failure removed for non-workspace `docs/`); `docs/platform/consumer/troubleshooting.md` updated with v1.10.0 docs build section

## Key Reviewer Files

- Primary files to review first:
  - `scripts/lib/docs/site.sh` — sole implementation file; 3 pnpm calls gain `--ignore-workspace`; `_docs_assert_pnpm_version` `log_fatal` message expanded to name all three version sources
  - `tests/infra/test_docs_site_sh_issue_272_273.py` — new content-level regression tests; 6 tests confirming both regressions are caught and both fixes verified
- High-risk files: `scripts/lib/docs/site.sh` — only risky file; both changes are additive (flag restoration + message text expansion); no logic branches altered

## Validation Evidence

- Required commands executed: `uv run python3 -m pytest tests/infra/test_docs_site_sh_issue_272_273.py -v` (6/6 PASS); `uv run python3 -m pytest tests/infra/ -q --ignore=tests/infra/modules` (106/106 PASS); `make infra-validate` (PASS); `make quality-hooks-fast` (8/9 PASS — `quality-spec-pr-ready` pre-publish expected); `make quality-hardening-review` (PASS)
- Result summary: all regression tests GREEN; no regressions in broader suite; `make docs-build && make docs-smoke` deferred to CI (requires live pnpm+docusaurus not available locally; content-level fix verified by regression tests)
- Artifact references: `tests/infra/test_docs_site_sh_issue_272_273.py` (test evidence); `docs/platform/consumer/troubleshooting.md` (docs evidence); `specs/2026-05-12-issue-272-273-v110-docs-hotfix/traceability.md` (checksums)

## Risk and Rollback

- Main risks: `--ignore-workspace` is additive — forces standalone resolution for `docs/` regardless of root `pnpm-workspace.yaml` globs; safe for consumers who include or exclude `docs/` from workspace. Expanded `log_fatal` message is diagnostic-only — does not affect exit codes, pipeline artifacts, or artifact schemas.
- Rollback strategy: `git revert <commit-sha>` on `scripts/lib/docs/site.sh` (single-file revert, no side effects). Test file and troubleshooting doc additions are safe to leave in place after rollback — they describe the regressed behavior and will fail until fix is re-applied.

## Deferred Proposals

- Proposal 1: `blueprint-align-pnpm-pins` Make target — script that rewrites all `packageManager` fields to match `docs/package.json` pin. Parked — trigger: on-scope: blueprint — migration script expands hotfix scope; Option A error message improvement is sufficient for manual operator resolution.
- Proposal 2: Preflight pnpm version drift detection — `quality-pnpm-version-contract` check scanning all `package.json#packageManager` fields before install. Parked — trigger: on-scope: quality — new quality hook out of scope for a two-line hotfix.
