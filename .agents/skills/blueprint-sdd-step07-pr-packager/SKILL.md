---
name: blueprint-sdd-step07-pr-packager
description: Execute SDD Steps 8 and 9 — fill pr_context.md and hardening_review.md, create GitHub issues for each deferred proposal, mark all tasks complete, pass all quality gates, mark the Draft PR as ready, and post the @codex review comment. Renamed and adjusted from blueprint-sdd-pr-packager to fit the single-PR lifecycle model.
---

# Blueprint SDD Step 07 — Publish + Mark PR Ready

## Steps covered

- **Step 8** — Publish (fill artifacts, file deferred-proposal issues, run quality gates)
- **Step 9** — Mark Draft PR ready + trigger CI

## When to Use

Invoke after Document + Operate is complete (Step 7 complete). This is the final
step before the PR is merged. All tasks in `tasks.md` must be marked `[x]`.

## Actor

Software Engineer (invokes agent).

## Governance Context

`AGENTS.md` is the canonical policy source for this skill. Sections that apply in this phase:

- `§ Publish Gate` — explicit checklist that must be satisfied before marking the PR ready.
- `§ Hardening Review Gate` — all four sections of `hardening_review.md` must be complete; this gate directly precedes publish.
- `§ Definition of Done (DoD)` — every DoD item must pass before the PR is marked ready.
- `§ Sign-off Policy` — self-approval is prohibited; confirm all sign-offs were granted by the appropriate stakeholders before closing out.

> If `AGENTS.md` changes any of the above sections, update this block to reflect the affected sections.

> Quality-hooks usage policy (per-slice vs pre-PR gate, keep-going env, force-full): see AGENTS.md § Quality Hooks — Inner-Loop and Pre-PR Usage.

## Guardrails

1. Do not mark the PR ready while any task in `tasks.md` is unchecked.
2. Do not mark the PR ready while `hardening_review.md` or `pr_context.md`
   have unfilled sections.
3. Every deferred proposal MUST receive an explicit outcome (file-issue / reject /
   park). No proposal may be silently omitted. Present the triage table and wait for
   user confirmation before acting on any proposal.
4. Do not implement deferred proposals in this phase — triage and record them, then
   move on. A filed issue or a parked backlog entry is the action item.
5. For parked proposals, a trigger MUST be assigned. A proposal with no trigger is
   not parked — it is silently dropped, which violates guardrail 3.
6. The PR being marked ready is the same Draft PR opened in Step 2.
   No new PR is opened.
7. All commits go to the existing branch before marking ready.
8. `pr_context.md` headings must match the repository pull-request template.

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

3. TRIAGE DEFERRED PROPOSALS (required for every proposal):
   a. Collect all entries from "Proposals Only (Not Implemented)" in
      hardening_review.md and "Deferred Proposals" in pr_context.md.

   b. Present a triage table to the user and WAIT for confirmation before acting:
      | # | Proposal | Recommendation | Rationale |
      |---|---|---|---|
      | 1 | <brief title> | file-issue | <one line> |
      | 2 | <brief title> | park | on-scope: quality — low urgency, no blocker |
      | 3 | <brief title> | reject | cosmetic only, not worth tracking |
      The recommendation is a starting point — the user confirms or overrides each row.

   c. For each confirmed file-issue:
      Create a GitHub issue:
        gh issue create \
          --title "proposal(<slug>): <brief proposal title>" \
          --body "**Source:** PR #<number>, \`hardening_review.md\` / \`pr_context.md\`

        **Context:** <one-paragraph description>

        **Rationale for deferral:** <why it was not implemented in this work item>

        **Suggested approach:** <brief notes from the hardening review>"
      Record the issue URL in:
        - pr_context.md Deferred Proposals (inline after the proposal)
        - AGENTS.backlog.md (new entry: `- [ ] proposal(<slug>): <title> — <issue URL>`)

   d. For each confirmed reject:
      Record in pr_context.md as:
        "Rejected at PR closure — <user's rationale>"
      Record in AGENTS.backlog.md as a checked entry with rejection note:
        - [x] (rejected) proposal(<slug>): <title> — rejected: <rationale>

   e. For each confirmed park:
      Propose a trigger type and value to the user; wait for confirmation:

      | Trigger | Format | When to use |
      |---|---|---|
      | `after:` | `after: <slug-or-issue-ref>` | Blocked on a specific item completing |
      | `on-scope:` | `on-scope: <tag>` | Revisit when any work touches this scope area |
      | `triage:` | `triage: next-session` | No dependency; pick up at next backlog triage |

      For `on-scope:`: pick the tag from `## Scope Registry` in AGENTS.backlog.md.
        If no existing tag fits, propose adding a new row to the registry in this commit.
      For `after:`: position the backlog entry immediately after the blocking item.
      For `triage: next-session`: include a `stale-after: 2` counter. After 2 triage
        sessions without promotion the entry flips to `stale` status and requires an
        explicit promote-or-discard decision.

      Record in pr_context.md as:
        "Parked — trigger: <type>: <value> — <one-line rationale>"
      Record in AGENTS.backlog.md as:
        - [ ] (parked) proposal(<slug>): <title>
              trigger: <type>: <value>
              rationale: <one line>

4. Mark all tasks complete in tasks.md (P-001, P-002, P-003 last).

5. Run quality gates — all must pass:
   make quality-hooks-fast         # SDD check + docs drift + infra contract tests
   make quality-hardening-review   # hardening_review.md completeness

6. TRACEABILITY VERIFICATION — run the blueprint-sdd-traceability-keeper skill
   for this work item. Resolve any blocking gaps before committing.

7. Commit final artifacts (including any traceability.md fixes from step 6):
   git add specs/YYYY-MM-DD-<slug>/pr_context.md \
           specs/YYYY-MM-DD-<slug>/hardening_review.md \
           specs/YYYY-MM-DD-<slug>/tasks.md \
           AGENTS.backlog.md
   git commit -m "feat(<slug>): publish artifacts — pr_context, hardening_review, deferred issues filed"
   git push

STEP 9 — MARK PR READY

8. Update the PR description to reflect final state:
   - Replace the Open Questions section (should already be gone from Step 3).
   - Ensure the description summarises the full pr_context.md content.

9. Mark the Draft PR as ready:
   gh pr ready <number>

10. Post the review request comment:
    gh pr comment <number> --body "@codex review this PR"
```

## Deferred proposal lifecycle

Every proposal receives an explicit outcome at Step 8 — no proposal is silently dropped.

| Outcome | Recorded in | Re-evaluation trigger |
|---|---|---|
| **file-issue** | pr_context.md (URL) + AGENTS.backlog.md (link) | Backlog triage / next SDD cycle |
| **reject** | pr_context.md (rationale) + AGENTS.backlog.md (checked, closed) | None — consciously discarded |
| **park** | pr_context.md (trigger) + AGENTS.backlog.md (trigger field) | Event-driven — see trigger types |

**Park trigger types:**
- `after: <slug-or-issue-ref>` — proposal surfaces automatically when step07 runs
  for the blocking item. That step's intake-scan (step01) will list it.
- `on-scope: <tag>` — proposal surfaces whenever step01-intake scaffolds a new work
  item whose scope matches the tag. The author sees it at the moment of highest context.
- `triage: next-session` — reviewed at the next explicit backlog triage. Carries a
  `stale-after: 2` counter; flips to `stale` after 2 sessions without promotion,
  requiring a conscious promote-or-discard decision.

Re-evaluation is event-driven, not calendar-driven. Limbo is prevented by the trigger,
not by periodic reminders.

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
11. Traceability keeper result (gaps found / clean).

## References

- PR packaging checklist: `references/pr_packaging_checklist.md`
