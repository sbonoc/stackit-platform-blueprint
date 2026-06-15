---
name: blueprint-sdd-step07-pr-packager
description: Execute SDD Steps 8 and 9 — fill pr_context.md and hardening_review.md, create GitHub issues for each deferred proposal, mark all tasks complete, pass all quality gates, mark the Draft PR as ready, and post the @codex review comment. Renamed and adjusted from blueprint-sdd-pr-packager to fit the single-PR lifecycle model.
blueprint-version: 1.0.0
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
   a. Collect proposals from two buckets — keep them separate in the triage table:
      - **pre-planned exclusions**: entries in `## Potential Deferred Proposals`
        in `spec.md` that were documented at step01. These were known scope boundaries
        from the start; they typically land as `park` or `reject` with minimal debate.
      - **newly-discovered proposals**: entries surfaced during implementation or
        hardening review that were not named at step01. These require full triage
        deliberation and are the primary input to the `hardening_review.md` Proposals
        section and the `pr_context.md` Deferred Proposals section.
      Also include any entries from "Proposals Only (Not Implemented)" in
      hardening_review.md and "Deferred Proposals" in pr_context.md that do not
      already appear in one of the two buckets above.

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

4. **ACR review** — for any spec that touches user-facing surfaces (UI components,
   web pages, or interactive flows), confirm `docs/platform/accessibility/acr.md`
   has been reviewed and that `Report date (last reviewed):` is updated to today's date.
   Run `make quality-a11y-acr-check` to verify the ACR is present, dated, and within
   the configured staleness window. Non-UI specs: skip this step.

5. Mark all tasks complete in tasks.md (P-001, P-002, P-003 last).

6. Run quality gates — all must pass:
   make quality-hooks-fast         # SDD check + docs drift + infra contract tests + ACR check
   make quality-hardening-review   # hardening_review.md completeness

7. TRACEABILITY VERIFICATION — run the blueprint-sdd-traceability-keeper skill
   for this work item. Resolve any blocking gaps before committing.

8. Commit final artifacts (including any traceability.md fixes from step 7):
   git add specs/YYYY-MM-DD-<slug>/pr_context.md \
           specs/YYYY-MM-DD-<slug>/hardening_review.md \
           specs/YYYY-MM-DD-<slug>/tasks.md \
           AGENTS.backlog.md
   git commit -m "feat(<slug>): publish artifacts — pr_context, hardening_review, deferred issues filed"
   git push

STEP 9 — MARK PR READY

9. Update the PR description to reflect final state:
   - Replace the Open Questions section (should already be gone from Step 3).
   - Ensure the description summarises the full pr_context.md content.

10. Mark the Draft PR as ready:
    gh pr ready <number>

11. Post the review request comments:
    gh pr comment <number> --body "@codex review this PR"
    gh pr comment <number> --body "@claude review this PR"
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


## Required Output Schema

The structured payload below is the PR-packager report the skill returns to
the orchestrator and carries on the `phase: pr-packager` C7 lifecycle event.

```yaml jsonschema
$schema: "http://json-schema.org/draft-07/schema#"
title: BlueprintSddStep07PrPackagerOutput
description: Structured PR-packager report produced at the end of SDD step 07.
type: object
additionalProperties: false
required:
  - ticket_id
  - pr_context_completeness
  - hardening_review_completeness
  - deferred_proposals_filed
  - backlog_entries_added
  - all_tasks_checked
  - hooks_result
  - hardening_review_result
  - pr_ready
  - traceability_result
properties:
  ticket_id:
    type: string
  pr_context_completeness:
    type: object
    additionalProperties: false
    required:
      - summary
      - requirement_coverage
      - key_reviewer_files
      - validation_evidence
      - risk_and_rollback
      - deferred_proposals
    properties:
      summary:
        type: string
        enum:
          - populated
          - missing
      requirement_coverage:
        type: string
        enum:
          - populated
          - missing
      key_reviewer_files:
        type: string
        enum:
          - populated
          - missing
      validation_evidence:
        type: string
        enum:
          - populated
          - missing
      risk_and_rollback:
        type: string
        enum:
          - populated
          - missing
      deferred_proposals:
        type: string
        enum:
          - populated
          - missing
  hardening_review_completeness:
    type: object
    additionalProperties: false
    required:
      - repository_wide_findings
      - observability_changes
      - architecture_compliance
      - proposals_only
    properties:
      repository_wide_findings:
        type: string
        enum:
          - populated
          - missing
      observability_changes:
        type: string
        enum:
          - populated
          - missing
      architecture_compliance:
        type: string
        enum:
          - populated
          - missing
      proposals_only:
        type: string
        enum:
          - populated
          - missing
  deferred_proposals_filed:
    type: array
    items:
      type: object
      additionalProperties: false
      required:
        - title
        - outcome
      properties:
        title:
          type: string
        outcome:
          type: string
          enum:
            - file-issue
            - park
            - reject
        issue_url:
          type: string
        trigger:
          type: string
        rationale:
          type: string
  backlog_entries_added:
    type: integer
    minimum: 0
  all_tasks_checked:
    type: boolean
  unchecked_task_ids:
    type: array
    items:
      type: string
  hooks_result:
    type: string
    enum:
      - pass
      - fail
  hardening_review_result:
    type: string
    enum:
      - pass
      - fail
  commit_sha:
    type: string
  pr_ready:
    type: boolean
  pr_url:
    type: string
  codex_review_comment_posted:
    type: boolean
  traceability_result:
    type: string
    enum:
      - clean
      - gaps-found
  expert_verdicts:
    type: array
    description: >-
      Per-expert verdict array merged by the orchestrator from the step07
      panel invocations (ADR-issue-364 § 4 dispatches a 4-expert panel at
      step07 in parallel-then-merge mode). Each row is keyed by
      expert_slug per ADR-issue-364 § 6 and is carried on the C7
      outcome_details.expert_verdicts[] field per FR-007.
    items:
      type: object
      additionalProperties: false
      required:
        - expert_slug
        - verdict
        - findings
      properties:
        expert_slug:
          type: string
        verdict:
          type: string
          enum:
            - pass
            - revise
            - block
        findings:
          type: array
          items:
            type: object
```

## C7 Emission

At the end of this step, emit a C7 lifecycle event. Resolve variable values
from session context: `TICKET_ID` — the GitHub issue number; `SKILL_BASENAME`
— the `name:` value from this SKILL.md frontmatter; `OWNER_TEAM` — the GitHub
team slug owning this repository (e.g. `platform-team`); `WORK_ITEM_SLUG` —
the spec directory basename.

```sh
uv run python3 scripts/bin/sdd/c7_emit.py emit \
  --ticket "$TICKET_ID" \
  --phase "pr-packager" \
  --skill "$SKILL_BASENAME" \
  --owner-team "$OWNER_TEAM" \
  --slug "$WORK_ITEM_SLUG"
```

Stage and commit the emitted JSONL — this commit is part of the authorized
skill workflow and must land immediately so the audit record is durable:

```sh
git add "artifacts/c7/$WORK_ITEM_SLUG.jsonl"
git diff --cached --quiet || {
  git commit -m "chore($WORK_ITEM_SLUG): emit C7 lifecycle event"
  git push
}
```

Set `BLUEPRINT_SDD_C7_EMIT=0` to suppress; exactly one `c7-emission-opted-out` event is written per work-item slug (subsequent opted-out steps write nothing — the guard above skips the commit in that case).
**The LLM MUST NOT write events directly — invoke the helper only.**
