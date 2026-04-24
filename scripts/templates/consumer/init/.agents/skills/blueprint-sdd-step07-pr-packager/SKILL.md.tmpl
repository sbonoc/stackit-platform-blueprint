---
name: blueprint-sdd-step07-pr-packager
description: Execute SDD Steps 8 and 9 — fill pr_context.md and hardening_review.md, create GitHub issues for each deferred proposal, mark all tasks complete, pass all quality gates, mark the Draft PR as ready, and post the @codex review comment. Renamed and adjusted from blueprint-sdd-pr-packager to fit the single-PR lifecycle model.
---

# Blueprint SDD Step 08 — Publish + Mark PR Ready

## Steps covered

- **Step 8** — Publish (fill artifacts, file deferred-proposal issues, run quality gates)
- **Step 9** — Mark Draft PR ready + trigger CI

## When to Use

Invoke after Document + Operate is complete (Step 7 complete). This is the final
step before the PR is merged. All tasks in `tasks.md` must be marked `[x]`.

## Actor

Software Engineer (invokes agent).

## Guardrails

1. Do not mark the PR ready while any task in `tasks.md` is unchecked.
2. Do not mark the PR ready while `hardening_review.md` or `pr_context.md`
   have unfilled sections.
3. Every deferred proposal MUST have a corresponding GitHub issue filed and
   its URL recorded in `pr_context.md` Deferred Proposals and `AGENTS.backlog.md`.
   This is the mechanism that prevents proposals from being silently dropped.
4. Do not implement deferred proposals in this phase — file them as issues and
   move on. The issue is the action item.
5. The PR being marked ready is the same Draft PR opened in Step 2.
   No new PR is opened.
6. All commits go to the existing branch before marking ready.
7. `pr_context.md` headings must match the repository pull-request template.

## Workflow

```
STEP 8 — PUBLISH ARTIFACTS

1. Fill hardening_review.md — all four sections required:
   - Repository-Wide Findings Fixed
   - Observability and Diagnostics Changes
   - Architecture and Code Quality Compliance
   - Proposals Only (Not Implemented)

2. Fill pr_context.md — all six sections required:
   - Summary (one paragraph)
   - Requirement Coverage (REQ-### → implementation → test evidence table)
   - Key Reviewer Files (high-signal changed files, not the full diff)
   - Validation Evidence (exact commands run and their pass/fail output)
   - Risk and Rollback (explicit rollback steps)
   - Deferred Proposals (non-implemented improvements with rationale)

3. FILE DEFERRED PROPOSAL ISSUES (required for every non-trivial proposal):
   For each entry in "Proposals Only (Not Implemented)" and Deferred Proposals:
   a. Create a GitHub issue:
      gh issue create \
        --title "proposal(<slug>): <brief proposal title>" \
        --body "**Source:** PR #<number>, \`hardening_review.md\` / \`pr_context.md\`

   **Context:** <one-paragraph description of the proposal>

   **Rationale for deferral:** <why it was not implemented in this work item>

   **Suggested approach:** <brief notes from the hardening review>"
   b. Record the issue URL in:
      - pr_context.md Deferred Proposals section (inline after each proposal)
      - AGENTS.backlog.md (new entry with issue link, priority TBD)
   If a proposal is purely cosmetic or already tracked elsewhere, mark it
   explicitly as "no issue filed — [rationale]" rather than silently omitting.

4. Mark all tasks complete in tasks.md (P-001, P-002, P-003 last).

5. Run quality gates — all must pass:
   make quality-hooks-fast         # SDD check + docs drift + infra contract tests
   make quality-hardening-review   # hardening_review.md completeness

6. Commit final artifacts:
   git add specs/YYYY-MM-DD-<slug>/pr_context.md \
           specs/YYYY-MM-DD-<slug>/hardening_review.md \
           specs/YYYY-MM-DD-<slug>/tasks.md \
           AGENTS.backlog.md
   git commit -m "feat(<slug>): publish artifacts — pr_context, hardening_review, deferred issues filed"
   git push

STEP 9 — MARK PR READY

7. Update the PR description to reflect final state:
   - Replace the Open Questions section (should already be gone from Step 3).
   - Ensure the description summarises the full pr_context.md content.

8. Mark the Draft PR as ready:
   gh pr ready <number>

9. Post the review request comment:
   gh pr comment <number> --body "@codex review this PR"
```

## Deferred proposal lifecycle

Deferred proposals are not optional documentation — they are action items. The
GitHub issue is the contract that a proposal will be revisited or explicitly
rejected. Without an issue, proposals disappear when the PR closes.

The expected lifecycle of a filed deferred-proposal issue:
1. Filed at Step 8 — appears in `AGENTS.backlog.md` with `Status: proposed`.
2. Triaged at the next backlog review — assigned a priority or closed with rationale.
3. Picked up as a future work item (starts a new SDD cycle) or explicitly rejected
   with a closing comment explaining why.

This ensures every proposal either ships in a future iteration or is consciously
discarded — never silently forgotten.

## pr_context.md section contract

| Section | Content |
|---|---|
| Summary | One paragraph: what changed, why, scope |
| Requirement Coverage | REQ-###, NFR-###, AC-### → implementation file → test name/path |
| Key Reviewer Files | 5–10 high-signal files; explain why each is reviewer-relevant |
| Validation Evidence | Exact commands run + excerpt of pass output |
| Risk and Rollback | Explicit rollback steps; blast radius; feature-flag status |
| Deferred Proposals | Items not implemented; GitHub issue URL; owner |

## Useful Commands

```bash
make spec-pr-context
make quality-hardening-review
make quality-hooks-fast
make quality-sdd-check
gh issue create --title "..." --body "..."
gh pr ready <number>
gh pr comment <number> --body "@codex review this PR"
```

## Required Report Format

Return:

1. `pr_context.md` section completeness (each section: populated / missing).
2. `hardening_review.md` section completeness (each section: populated / missing).
3. Deferred proposals filed as issues (list with issue URLs, or "none").
4. `AGENTS.backlog.md` entries added (count).
5. `tasks.md` — all tasks checked? (yes/no; list any unchecked).
6. `quality-hooks-fast` result.
7. `quality-hardening-review` result.
8. Final commit SHA pushed.
9. PR marked ready (yes/no) + PR URL.
10. `@codex review this PR` comment posted (yes/no).

## References

- PR packaging checklist: `references/pr_packaging_checklist.md`
