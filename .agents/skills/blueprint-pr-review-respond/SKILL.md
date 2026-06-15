---
name: blueprint-pr-review-respond
description: React to follow-up reviewer comments on an open Draft PR; classify each comment, propose a remediation action, and produce a response action envelope.
blueprint-version: 1.0.0
extensibility-tier: extensible
emits-phase: agent-pr-review
---

# Blueprint PR Review Respond

## When to Use

Invoked when a reviewer comment lands on an open Draft PR after the initial
`blueprint-sdd-step08-agent-pr-review` pass. The skill classifies the
comment, proposes a remediation action, and returns a response envelope the
orchestrator can post as a PR reply on behalf of the responding expert.

## Actor

Invoked by the orchestrator on behalf of the same step08 expert that filed
the original finding (drawn from the 8-expert roster locked by
`ADR-issue-364-expert-persona-model.md`). The expert-panel layer MUST NOT
directive-invoke this skill; the orchestrator's dispatch table is the
binding mechanism.

## Inputs

- The reviewer comment text and its PR-thread anchor (file path + line).
- The original findings list the step08 expert filed on this PR.
- The `expert_slug` the response is being authored under.
- The current head commit SHA on the PR branch.

## Steps

1. Read the reviewer comment and locate the matching original finding
   (when one exists).
2. Classify the comment into one of `accept-fix | accept-with-rationale |
   pushback | request-clarification`.
3. Propose a concrete remediation action when the classification is
   `accept-fix`: which file to edit, what change to make, and which test
   would prove the fix.
4. Return the structured payload described in `## Required Output Schema`
   below.

## Composition

This skill MUST NOT directive-invoke any other skill. The orchestrator
composes follow-up actions (e.g., re-dispatching the step05 panel for a
revise pass) per the dispatch rules in
`ADR-issue-337-persona-skill-contract.md` clause 3 (as amended by
`ADR-issue-364-expert-persona-model.md`).

## Required Output Schema

The orchestrator emits a `phase: agent-pr-review` C7 lifecycle event on skill
completion; the structured payload below is the `outcome_details` carried on
that event.

```yaml jsonschema
$schema: "http://json-schema.org/draft-07/schema#"
title: BlueprintPrReviewRespondOutput
description: Response envelope reacting to one follow-up reviewer comment.
type: object
additionalProperties: false
required:
  - ticket_id
  - comment_anchor
  - classification
  - response_text
properties:
  ticket_id:
    type: string
  comment_anchor:
    type: object
    additionalProperties: false
    required:
      - file
      - line
    properties:
      file:
        type: string
      line:
        type: integer
        minimum: 1
      pr_comment_id:
        type: string
  related_finding_id:
    type: string
    description: Identifier of the original finding this comment relates to; omit when the comment is unrelated to a prior finding.
  classification:
    type: string
    enum:
      - accept-fix
      - accept-with-rationale
      - pushback
      - request-clarification
  response_text:
    type: string
    description: The PR reply text the persona will post.
  proposed_remediation:
    type: object
    description: Populated only when classification is `accept-fix`.
    additionalProperties: false
    properties:
      file:
        type: string
      change_summary:
        type: string
      validating_test_path:
        type: string
```
