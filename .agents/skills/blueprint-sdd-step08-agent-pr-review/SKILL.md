---
name: blueprint-sdd-step08-agent-pr-review
description: Produce a structured findings list against the work-item PR diff at SDD step 08; one invocation per reviewer persona (security, architecture, contract, test-coverage).
blueprint-version: 1.0.0
extensibility-tier: extensible
emits-phase: agent-pr-review
---

# Blueprint SDD Step 08 — Agent PR Review

## Steps covered

- **Step 8** — Agent PR review pass that produces the structured findings
  list the human merge reviewer reads at the bounded-context human merge gate.

## When to Use

Invoked after the `doc-keeper` persona has authored the PR body via
`blueprint-sdd-step07-pr-packager` and before the human merge gate. The
four reviewer personas (`security-reviewer`, `architecture-reviewer`,
`contract-reviewer`, `test-coverage-reviewer`) each invoke this skill
EXACTLY ONCE per PR review cycle.

## Actor

Invoked by one of the four reviewer personas. The reviewer-model-heterogeneity
ADR at
`docs/blueprint/architecture/decisions/ADR-issue-337-reviewer-model-heterogeneity.md`
requires that the reviewer persona run on a different model family than the
implementer persona that produced the change under review; the orchestrator
(Child B) enforces the model-rotation pick.

## Inputs

- The full work-item PR diff against the base branch.
- The reviewer persona's `## Review Dimensions` and (for
  `architecture-reviewer`) the `## Cross-Context Impact Reporting` template.
- The packaged PR body authored by the PR packager.
- The work-item `traceability.md` and `graph.json`.

## Steps

1. Read the PR diff and the reviewer persona's review-dimension set.
2. Generate findings, one entry per concrete observation, tagged with
   severity drawn from the enum `must-fix | warn | info`.
3. Anchor every finding to a concrete diff location (`file` + `line`).
4. Produce the cross-context impact reporting payload (architecture-reviewer
   only) per the template in the persona file.
5. Return the structured payload described in `## Required Output Schema`
   below.

## Composition

This skill MUST NOT directive-invoke any other skill. Each reviewer persona
invokes this skill independently and may subsequently invoke
`blueprint-pr-review-respond` per its own persona definition when follow-up
reviewer comments arrive on the open PR.

## Required Output Schema

The orchestrator emits a `phase: agent-pr-review` C7 lifecycle event on skill
completion; the structured payload below is the `outcome.details` carried on
that event.

```yaml jsonschema
$schema: "http://json-schema.org/draft-07/schema#"
title: BlueprintAgentPrReviewOutput
description: >-
  Structured findings list produced by one reviewer persona invocation
  during the SDD step08 agent PR review phase.
type: object
additionalProperties: false
required:
  - ticket_id
  - reviewer_persona
  - findings
properties:
  ticket_id:
    type: string
  reviewer_persona:
    type: string
    enum:
      - security-reviewer
      - architecture-reviewer
      - contract-reviewer
      - test-coverage-reviewer
  findings:
    type: array
    items:
      type: object
      additionalProperties: false
      required:
        - id
        - dimension
        - severity
        - file
        - line
        - description
      properties:
        id:
          type: string
        dimension:
          type: string
          description: One of the reviewer persona's ## Review Dimensions bullets.
        severity:
          type: string
          enum:
            - must-fix
            - warn
            - info
        file:
          type: string
        line:
          type: integer
          minimum: 1
        description:
          type: string
        remediation_suggestion:
          type: string
  cross_context_impact:
    type: object
    description: >-
      Populated only when reviewer_persona is `architecture-reviewer`.
    additionalProperties: false
    properties:
      bounded_contexts_touched:
        type: array
        items:
          type: string
      downstream_consumers_impacted:
        type: array
        items:
          type: string
      contract_surface_deltas:
        type: array
        items:
          type: string
      rollback_risk:
        type: string
```
