---
name: blueprint-sdd-step02-resolve-questions
description: "Execute SDD Step 3 — scaffold if not already done, read PR comments from reviewers (PO, Architect, etc.), replace [NEEDS CLARIFICATION: ...] blocks in artifacts with resolved decisions, update the Open Questions table in the PR description, commit, and post a confirmation comment. Repeats until open question count reaches zero and SPEC_PRODUCT_READY is recorded. Can be invoked by any project stakeholder."
blueprint-version: 1.0.0
---

# Blueprint SDD Step 02 — Open Question Resolution Loop

## Step covered

- **Step 0** (auto) — Scaffold if not already done
- **Step 3** — Resolve open questions from PR comments, loop until count = 0

## When to Use

Invoke after the Draft PR is open (Step 2 complete) and reviewers have left
answers in PR comments or inline review comments. This skill bridges GitHub
reviewer feedback into the work-item artifacts without requiring reviewers
to have a local development environment or Claude Code.

The skill can be invoked multiple times — once per resolution round — until
all `[NEEDS CLARIFICATION: ...]` markers are resolved and `SPEC_PRODUCT_READY: true`
is recorded in `spec.md`.

## Actor

Any project stakeholder: **CPO / PO / CTO / Architect / Software Engineer**.
Reviewers interact exclusively via GitHub PR comments — no local tooling required.

## Governance Context

`AGENTS.md` is the canonical policy source for this skill. Sections that apply in this phase:

- `§ Clarification Marker Policy` — only fully resolved `[NEEDS CLARIFICATION: ...]` blocks may be removed; partial resolution leaves the block intact.
- `§ Sign-off Policy` — the exact deterministic phrase is required; plain-language approval is not sufficient; self-approval is prohibited.
- `§ SDD Readiness Gate (Mandatory Before Implementation)` — `SPEC_PRODUCT_READY` is a prerequisite for the full sign-off gate in the next step.

> If `AGENTS.md` changes any of the above sections, update this block to reflect the affected sections.

## Guardrails

1. If the spec directory is missing when the skill starts, run the scaffold first.
2. Read ALL PR comments and inline review comments before beginning any edits.
3. Replace each resolved `[NEEDS CLARIFICATION: ...]` block with the decision text
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

2. For each comment that answers a [NEEDS CLARIFICATION: ...] question:
   a. Identify the corresponding block in the relevant artifact.
   b. Replace the entire block with the chosen option text + rationale paragraph.
      Example:
        Before:
          > **[NEEDS CLARIFICATION: Which caching strategy to use?]**
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

4. make quality-sdd-check      # confirm [NEEDS CLARIFICATION: ...] count drops

5. Update the Open Questions table in the PR description:
   - Remove resolved rows.
   - Update the count in the heading: "## Open Questions (K remaining)".
   - If count reaches 0, remove the entire Open Questions section and sign-off
     instructions from the PR description.

6. TRACEABILITY VERIFICATION — run the blueprint-sdd-traceability-keeper skill
   for this work item. Resolve any blocking gaps.

7. Commit all updated artifacts (including any traceability.md fixes):
   git add specs/YYYY-MM-DD-<slug>/ [any other changed files]
   git commit -m "feat(<slug>): resolve N open questions — <brief summary>"
   git push

8. Post a confirmation PR comment:
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
9. Traceability keeper result (gaps found / clean).

## Useful Commands

```bash
gh pr view <number> --comments
gh pr comment <number> --body "..."
make quality-sdd-check
```

## References

- Resolution checklist: `references/resolution_checklist.md`


## Required Output Schema

The structured payload below is the resolution-round report the skill returns
to the orchestrator and carries on the `phase: resolve-questions` C7 lifecycle event.

```yaml jsonschema
$schema: "http://json-schema.org/draft-07/schema#"
title: BlueprintSddStep02ResolveQuestionsOutput
description: Structured resolution-round report produced at the end of SDD step 02.
type: object
additionalProperties: false
required:
  - ticket_id
  - scaffold_status
  - pr_comments_read
  - questions_resolved_this_round
  - questions_remaining
  - signoffs_recorded
  - sdd_check_marker_count_before
  - sdd_check_marker_count_after
  - confirmation_comment_posted
  - traceability_result
properties:
  ticket_id:
    type: string
  scaffold_status:
    type: string
    enum:
      - auto-run
      - already-existed
  pr_comments_read:
    type: integer
    minimum: 0
  questions_resolved_this_round:
    type: array
    items:
      type: object
      additionalProperties: false
      required:
        - id
        - decision_summary
      properties:
        id:
          type: string
        decision_summary:
          type: string
  questions_remaining:
    type: array
    items:
      type: object
      additionalProperties: false
      required:
        - id
        - description
      properties:
        id:
          type: string
        description:
          type: string
  signoffs_recorded:
    type: array
    items:
      type: string
      enum:
        - product
        - architecture
        - security
        - operations
  sdd_check_marker_count_before:
    type: integer
    minimum: 0
  sdd_check_marker_count_after:
    type: integer
    minimum: 0
  commit_sha:
    type: string
  confirmation_comment_posted:
    type: boolean
  traceability_result:
    type: string
    enum:
      - clean
      - gaps-found
  expert_verdicts:
    type: array
    description: >-
      Per-expert verdict array merged by the orchestrator from the step02
      panel invocations (ADR-issue-364 § 4 dispatches a dynamic expert
      panel at step02 driven by the § 4.2 contiguous content-bigram
      overlap algorithm with stopword filtering; substring / keyword /
      domain matching are forbidden). Each row is keyed by expert_slug
      per ADR-issue-364 § 6 and is carried on the C7
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

## C7 Extension Fields and Emission (step02-specific)

Step02 dispatches a dynamic expert panel (ADR-issue-364 § 4 / § 4.2). Every
step02 local-cli C7 event MUST carry `outcome_details.expert_verdicts[]` regardless
of whether dispatch was bigram-matched or floor-only. Use the complete emit
sequence below instead of the generic `## C7 Emission` block at the bottom of
this file (which is the fallback for steps without panel dispatch).

**Prerequisite — helper version:** the `--extension-json` flag was added to
`scripts/bin/sdd/c7_emit.py` in blueprint version `1.0.0` (issue #364). If
your consumer repo seeded an older copy of the helper, the flag will not be
recognised and the command will exit with an argparse error. Verify with
`uv run python3 scripts/bin/sdd/c7_emit.py emit --help | grep extension-json`.
If the flag is absent, update your seeded helper from the blueprint source
before running these commands, or fall back to the generic `## C7 Emission`
block below (which omits expert-verdict attribution from the C7 event, keeping
audit coverage degraded until the helper is upgraded).

**Bigram-matched dispatch:** author one row per dispatched expert into the payload,
then emit:

```sh
EXT_PAYLOAD="$(mktemp)"
cat > "$EXT_PAYLOAD" <<'JSON'
{
  "outcome_details": {
    "expert_verdicts": [
      {"expert_slug": "data-privacy", "verdict": "pass", "findings_count": 0}
    ]
  },
  "evidence_uri": "artifacts/c7/<work-item-slug>/resolve-questions-round-0.json"
}
JSON

uv run python3 scripts/bin/sdd/c7_emit.py emit \
  --ticket "$TICKET_ID" \
  --phase "resolve-questions" \
  --skill "$SKILL_BASENAME" \
  --owner-team "$OWNER_TEAM" \
  --slug "$WORK_ITEM_SLUG" \
  --extension-json "$EXT_PAYLOAD"

rm -f "$EXT_PAYLOAD"
```

**Floor case** (zero content-bigram matches → `product-pragmatist` dispatched as
floor-only per ADR-issue-364 § 4.2 step 6): `product-pragmatist` IS an expert
invocation and its verdict MUST appear so audit consumers can distinguish
floor-dispatch from no panel execution:

```sh
EXT_PAYLOAD_FLOOR="$(mktemp)"
cat > "$EXT_PAYLOAD_FLOOR" <<'JSON'
{
  "outcome_details": {
    "expert_verdicts": [
      {"expert_slug": "product-pragmatist", "verdict": "pass", "findings_count": 0}
    ]
  },
  "evidence_uri": "artifacts/c7/<work-item-slug>/resolve-questions-round-0.json"
}
JSON

uv run python3 scripts/bin/sdd/c7_emit.py emit \
  --ticket "$TICKET_ID" \
  --phase "resolve-questions" \
  --skill "$SKILL_BASENAME" \
  --owner-team "$OWNER_TEAM" \
  --slug "$WORK_ITEM_SLUG" \
  --extension-json "$EXT_PAYLOAD_FLOOR"

rm -f "$EXT_PAYLOAD_FLOOR"
```

Then stage and commit per the `## C7 Emission` block below.

## C7 Emission

At the end of this step, emit a C7 lifecycle event. Resolve variable values
from session context: `TICKET_ID` — the GitHub issue number; `SKILL_BASENAME`
— the `name:` value from this SKILL.md frontmatter; `OWNER_TEAM` — the GitHub
team slug owning this repository (e.g. `platform-team`); `WORK_ITEM_SLUG` —
the spec directory basename.

```sh
uv run python3 scripts/bin/sdd/c7_emit.py emit \
  --ticket "$TICKET_ID" \
  --phase "resolve-questions" \
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
