---
name: blueprint-sdd-step02-resolve-questions
description: Execute SDD Step 3 — scaffold if not already done, read PR comments from reviewers (PO, Architect, etc.), replace [NEEDS CLARIFICATION] blocks in artifacts with resolved decisions, update the Open Questions table in the PR description, commit, and post a confirmation comment. Repeats until open question count reaches zero and SPEC_PRODUCT_READY is recorded. Can be invoked by any project stakeholder.
---

# Blueprint SDD Step 03 — Open Question Resolution Loop

## Step covered

- **Step 0** (auto) — Scaffold if not already done
- **Step 3** — Resolve open questions from PR comments, loop until count = 0

## When to Use

Invoke after the Draft PR is open (Step 2 complete) and reviewers have left
answers in PR comments or inline review comments. This skill bridges GitHub
reviewer feedback into the work-item artifacts without requiring reviewers
to have a local development environment or Claude Code.

The skill can be invoked multiple times — once per resolution round — until
all `[NEEDS CLARIFICATION]` markers are resolved and `SPEC_PRODUCT_READY: true`
is recorded in `spec.md`.

## Actor

Any project stakeholder: **CPO / PO / CTO / Architect / Software Engineer**.
Reviewers interact exclusively via GitHub PR comments — no local tooling required.

## Guardrails

1. If the spec directory is missing when the skill starts, run the scaffold first.
2. Read ALL PR comments and inline review comments before beginning any edits.
3. Replace each resolved `[NEEDS CLARIFICATION]` block with the decision text
   and its rationale. Do not leave partial blocks.
4. Record `SPEC_PRODUCT_READY: approved` and `Product sign-off: approved` in
   `spec.md` when the deterministic sign-off phrase is present in a PR comment.
5. Do not self-approve any sign-off field — only record what reviewers explicitly stated.
6. Do not alter unresolved questions — only remove blocks that have a reviewer answer.
7. Run `make quality-sdd-check` after each round to confirm the marker count drops.
8. All commits go to the same branch — the same Draft PR auto-updates.

## Workflow

```
0. AUTO-SCAFFOLD (if not already done)
   Check whether the spec directory exists:
     ls specs/*-<slug>/ 2>/dev/null
   If the directory does not exist, run:
     make spec-scaffold SPEC_SLUG=<slug>
   If the directory already exists, skip this step.

1. Read all PR comments and inline review comments:
   gh pr view <number> --comments
   gh api repos/<owner>/<repo>/pulls/<number>/comments   # inline comments

2. For each comment that answers a [NEEDS CLARIFICATION] question:
   a. Identify the corresponding block in the relevant artifact.
   b. Replace the entire block with the chosen option text + rationale paragraph.
      Example:
        Before:
          > **[NEEDS CLARIFICATION]** Which caching strategy to use?
          > **Options:**
          > - **A)** In-process cache — low latency (agent recommendation)
          > - **B)** Redis — shared across replicas
          > **Agent recommendation:** Option A because ...
        After:
          Cache strategy: Redis (Option B) — required because the service
          runs as multiple replicas and in-process caches would be inconsistent.
          Decision by PO comment 2026-04-24.
   c. Mark the question as resolved in the Open Questions tracking list.

3. If a comment contains the phrase `SPEC_PRODUCT_READY: approved`:
   a. Set `SPEC_PRODUCT_READY: true` in spec.md frontmatter.
   b. Set `Product sign-off: approved` in the Sign-offs section of spec.md.

4. make quality-sdd-check      # confirm [NEEDS CLARIFICATION] count drops

5. Update the Open Questions table in the PR description:
   - Remove resolved rows.
   - Update the count in the heading: "## Open Questions (K remaining)".
   - If count reaches 0, remove the entire Open Questions section and sign-off
     instructions from the PR description.

6. Commit all updated artifacts:
   git add specs/YYYY-MM-DD-<slug>/ [any other changed files]
   git commit -m "feat(<slug>): resolve N open questions — <brief summary>"
   git push

7. Post a confirmation PR comment:
   gh pr comment <number> --body \
     "Resolved N open questions. Updated: \`spec.md\`, \`architecture.md\`.
      Commit <sha>. Remaining open: K."
```

## Sign-off phrase (deterministic)

The following exact phrase in any PR comment triggers Product sign-off recording:

```
SPEC_PRODUCT_READY: approved
```

No other format is recognized — plain-language variations are not sufficient.
If a reviewer expresses approval without using this phrase, post a follow-up
comment asking them to leave a comment with the exact phrase.

## Required Report Format

Return:

1. Scaffold status (auto-run or already existed).
2. PR comments read (count).
3. Questions resolved this round (list with brief decision summary each).
4. Questions remaining (count + brief description each).
5. Sign-offs recorded (if any) and in which field.
6. `make quality-sdd-check` result (marker count before → after).
7. Commit SHA pushed.
8. Confirmation PR comment posted (yes/no).

## Useful Commands

```bash
gh pr view <number> --comments
gh pr comment <number> --body "..."
make quality-sdd-check
```

## References

- Resolution checklist: `references/resolution_checklist.md`
