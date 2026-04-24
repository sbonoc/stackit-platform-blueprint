---
name: blueprint-sdd-step08-pr-packager
description: Execute SDD Steps 8 and 9 — fill pr_context.md and hardening_review.md, mark all tasks complete, pass all quality gates, mark the Draft PR as ready, and post the @codex review comment. Renamed and adjusted from blueprint-sdd-pr-packager to fit the single-PR lifecycle model.
---

# Blueprint SDD Step 08 — Publish + Mark PR Ready

## Steps covered

- **Step 8** — Publish (fill artifacts, run quality gates)
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
3. Do not implement deferred proposals in this phase — record them in the
   `Proposals Only (Not Implemented)` section of `hardening_review.md`.
4. The PR being marked ready is the same Draft PR opened in Step 2.
   No new PR is opened.
5. All commits go to the existing branch before marking ready.
6. `pr_context.md` headings must match the repository pull-request template.

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

3. Mark all tasks complete in tasks.md (P-001, P-002, P-003 last).

4. Run quality gates — all must pass:
   make quality-hooks-fast         # SDD check + docs drift + infra contract tests
   make quality-hardening-review   # hardening_review.md completeness

5. Commit final artifacts:
   git add specs/YYYY-MM-DD-<slug>/pr_context.md \
           specs/YYYY-MM-DD-<slug>/hardening_review.md \
           specs/YYYY-MM-DD-<slug>/tasks.md
   git commit -m "feat(<slug>): publish artifacts — pr_context, hardening_review"
   git push

STEP 9 — MARK PR READY

6. Update the PR description to reflect final state:
   - Replace the Open Questions section (should already be gone from Step 3).
   - Ensure the description summarises the full pr_context.md content.

7. Mark the Draft PR as ready:
   gh pr ready <number>

8. Post the review request comment:
   gh pr comment <number> --body "@codex review this PR"
```

## pr_context.md section contract

| Section | Content |
|---|---|
| Summary | One paragraph: what changed, why, scope |
| Requirement Coverage | REQ-###, NFR-###, AC-### → implementation file → test name/path |
| Key Reviewer Files | 5–10 high-signal files; explain why each is reviewer-relevant |
| Validation Evidence | Exact commands run + excerpt of pass output |
| Risk and Rollback | Explicit rollback steps; blast radius; feature-flag status |
| Deferred Proposals | Items not implemented; owner + follow-up issue if applicable |

## Useful Commands

```bash
make spec-pr-context
make quality-hardening-review
make quality-hooks-fast
make quality-sdd-check
gh pr ready <number>
gh pr comment <number> --body "@codex review this PR"
```

## Required Report Format

Return:

1. `pr_context.md` section completeness (each section: populated / missing).
2. `hardening_review.md` section completeness (each section: populated / missing).
3. `tasks.md` — all tasks checked? (yes/no; list any unchecked).
4. `quality-hooks-fast` result.
5. `quality-hardening-review` result.
6. Final commit SHA pushed.
7. PR marked ready (yes/no) + PR URL.
8. `@codex review this PR` comment posted (yes/no).

## References

- PR packaging checklist: `references/pr_packaging_checklist.md`
