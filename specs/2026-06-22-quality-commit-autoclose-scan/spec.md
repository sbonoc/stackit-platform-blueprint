# Specification

## Spec Readiness Gate (Blocking)
<!-- SPEC_PRODUCT_READY=true: intake gate — Product sign-off only; unlocks agent ADR drafting.
     SPEC_READY=true: implementation gate — all sign-offs required; unlocks coding. -->
- SPEC_READY: true
- SPEC_PRODUCT_READY: true
- Unresolved TODO markers count: 0
- Pending assumptions count: 0
- Open clarification markers count: 0
- Product sign-off: approved
- Architecture sign-off: approved
- Security sign-off: approved
- Operations sign-off: approved
- Missing input blocker token: none
- ADR path: none
- ADR status: n/a
- SPEC_READY_EXCEPTION: chore
- authorized-by: sbonoc

## Applicable Guardrail Controls (Normative)
- Applicable control IDs: SDD-C-001, SDD-C-003, SDD-C-007, SDD-C-009, SDD-C-024
- Control exception rationale: SDD-C-002 (multi-slice plan) does not apply — bypass-track chore; single delivery slice. SDD-C-005 (ADR required) does not apply — bypass-track chore; no new architectural decision. SDD-C-014, SDD-C-015, SDD-C-018, SDD-C-022 do not apply — quality tooling only, no runtime service, no upstream dependency, no HTTP routes.

## Implementation Stack Profile (Normative)
- Backend stack profile: python_plus_fastapi_pydantic_v2
- Frontend stack profile: none
- Test automation profile: pytest_vitest_playwright_pact
- Agent execution model: specialized-subagents-isolated-worktrees
- Managed service preference: none
- Managed service exception rationale: n/a
- Runtime profile: none
- Has user-facing flow: false <!-- inferred from intake: no UI/flow signals — quality CI tooling only; confirm before SPEC_READY -->

## Context

Parent issue #361 (orchestrator coordination spec) was auto-closed TWICE on 2026-06-22 when PR commit bodies narrated the auto-close bug class and were matched by GitHub keyword parser. The existing `PARENT_AUTOCLOSE_REGEX` in `tests/blueprint/test_issue_361_file_children_script.py` correctly detects this pattern but only guards GENERATED content (children body templates, deferred-trigger rationale). It does NOT scan commit-message subjects or bodies on the PR branch. This work item ships the generalised version as a pre-push quality check.

## Functional Requirements (Normative)

- REQ-001 The check MUST accept as input a list of must-not-auto-close issue numbers. The primary source MUST be `Tracks #N` markers parsed from the current branch's open PR body (via `gh pr view --json body,title`). If no open PR exists, the check MUST fall back to a `.github/no-auto-close-issues.yml` config file; if that file is also absent, the check MUST exit 0 (no-op).
- REQ-002 The check MUST scan EXACTLY the following surfaces: (a) PR title, (b) PR body, (c) every commit message subject and body on the branch since diverging from the default branch (`git log origin/main..HEAD --pretty=format:%H%n%s%n%b`). Scanning file diffs MUST NOT be done.
- REQ-003 The check MUST use the canonical AC-013 regex `\b(close[ds]?|fix(?:e[ds])?|resolve[ds]?):?\s+#N\b` (case-insensitive) where `N` is each protected issue number. This regex MUST be defined once in `scripts/lib/quality/autoclose_regex.py` as a module-level constant.
- REQ-004 When a match is found, the check MUST exit non-zero and print a human-readable error identifying: (a) the surface (PR title / PR body / `<commit-hash>`), (b) the matching line text, (c) the protected issue number matched, (d) the `#allow-auto-close: #N` override token that would suppress the error if acceptable.
- REQ-005 The check MUST support a per-PR override token. If the PR body contains `#allow-auto-close: #N1,#N2`, the listed issue numbers MUST be excluded from the protected set for that PR invocation.
- REQ-006 The check MUST be wired as a `pre-push` stage entry in `.pre-commit-config.yaml` under id `quality-pr-commit-autoclose-check` with `always_run: true`.
- REQ-007 The check MUST be available as a `make quality-pr-commit-autoclose-check` target.
- REQ-008 The script and config entry MUST be placed in bootstrap-template-synced paths so consumer repos inherit the check automatically.

## Non-Functional Requirements (Normative)

- NFR-PERF-001 The check MUST complete in ≤ 5 seconds on a branch with ≤ 200 commits and a PR body of ≤ 50 KB. MUST NOT call the GitHub API more than once per invocation.
- NFR-REL-001 If `gh` CLI is not authenticated or the PR does not yet exist (first push before PR creation), the check MUST exit 0 and emit an informational message; it MUST NOT block the push.
- NFR-MAINT-001 The canonical regex MUST live in `scripts/lib/quality/autoclose_regex.py`. The existing `PARENT_AUTOCLOSE_REGEX` in `tests/blueprint/test_issue_361_file_children_script.py` MUST be replaced with an import from that module.

## Acceptance Criteria (Normative)

- AC-001 [Unit: regex matches all GitHub auto-close keyword forms] — verified by T-001, which MUST assert that `build_pattern(361).search(text)` returns a non-None match for each of: `Closes #361`, `closes #361`, `Closes: #361`, `Fixed #361`, `Resolves #361`, `auto-closed #361`; and returns None for `Tracks #361`, `references #361`, `see #361`, `blocked-by #361`.
- AC-002 [Unit: PR body Tracks #N parsing extracts protected set] — verified by T-002, which MUST assert that given a PR body containing `Tracks #361` and `Tracks #332`, the parser returns `{361, 332}`; and that `#allow-auto-close: #361` removes 361 from the protected set.
- AC-003 [Unit: commit-log scanner detects violation and reports commit hash] — verified by T-003, which MUST assert that the scanner returns a non-empty findings list including the commit hash when given a log containing `auto-closed #361` in a body with #361 protected; and an empty list when the log contains only `Tracks #361`.
- AC-004 [Unit: no-open-PR fallback reads config file] — verified by T-004, which MUST assert that when `gh pr view` returns a non-zero exit code, the scanner reads `.github/no-auto-close-issues.yml` and protects listed numbers; and exits 0 when both PR and config file are absent.
- AC-005 [Integration: pre-push hook exits non-zero on violation] — verified by T-005, which MUST assert that running the check script against a test branch whose newest commit body contains `auto-closed #361` with #361 in the protected list exits non-zero and names the offending commit; and exits 0 when no violation is present.
- AC-006 [Regression: existing per-spec test still passes after regex refactor] — verified by T-006, which MUST assert that `tests/blueprint/test_issue_361_file_children_script.py` passes after `PARENT_AUTOCLOSE_REGEX` is replaced with an import from `scripts/lib/quality/autoclose_regex.py`.

## Potential Deferred Proposals

- Multi-repo consumer PR CI enforcement (not just pre-push): pre-push is the primary safety layer; per-PR CI enforcement requires consumer-repo workflow changes.
- Inline per-line override token: per-PR override covers all known real cases.
- Stale issue-number detection: adds a second GitHub API call without proportional safety gain.
