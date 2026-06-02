---
name: blueprint-human-review-prep
description: Package the green branch and reviewer-persona findings into a structured payload the human merge reviewer can consume in one pass at the bounded-context human merge gate.
blueprint-version: 1.0.0
extensibility-tier: extensible
emits-phase: pr-packager
---

# Blueprint Human Review Prep

## When to Use

Invoked after the four reviewer personas have completed the `agent-pr-review`
phase and before the bounded-context human merge gate. The output is the
attention map the human merge reviewer uses to decide whether to approve
the PR.

## Actor

Invoked by the `doc-keeper` persona. Other personas MUST NOT invoke this
skill directly.

## Inputs

- The packaged PR body authored by `blueprint-sdd-step07-pr-packager`.
- The findings lists filed by each of the four reviewer personas.
- The hardening review file `hardening_review.md`.
- The work-item `traceability.md` and `graph.json`.

## Steps

1. Aggregate the reviewer-persona findings by severity and dimension.
2. Append the cross-context impact reporting payload from the
   `architecture-reviewer` persona to the structured output.
3. Surface any unresolved must-fix findings so the human merge reviewer
   can refuse merge until they are addressed or explicitly waived.
4. Return the structured payload described in `## Required Output Schema`
   below.

## Composition

This skill MUST NOT directive-invoke any other skill. The bounded-context
human merge gate is granted by an authorised human reviewer, not by any
agent.

## Required Output Schema

The orchestrator emits a `phase: pr-packager` C7 lifecycle event on skill
completion; the structured payload below is the `outcome.details` carried on
that event.

```yaml jsonschema
$schema: "http://json-schema.org/draft-07/schema#"
title: BlueprintHumanReviewPrep
description: >-
  Attention map for the human merge reviewer at the bounded-context human
  merge gate.
type: object
additionalProperties: false
required:
  - ticket_id
  - reviewer_findings
  - cross_context_impact
  - unresolved_must_fix
properties:
  ticket_id:
    type: string
  reviewer_findings:
    type: object
    additionalProperties: false
    required:
      - security
      - architecture
      - contract
      - test_coverage
    properties:
      security:
        type: array
        items:
          type: object
      architecture:
        type: array
        items:
          type: object
      contract:
        type: array
        items:
          type: object
      test_coverage:
        type: array
        items:
          type: object
  cross_context_impact:
    type: object
    additionalProperties: false
    required:
      - bounded_contexts_touched
      - downstream_consumers_impacted
      - contract_surface_deltas
      - rollback_risk
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
  unresolved_must_fix:
    type: array
    items:
      type: object
      additionalProperties: false
      required:
        - reviewer
        - finding_id
        - file
        - line
        - description
      properties:
        reviewer:
          type: string
        finding_id:
          type: string
        file:
          type: string
        line:
          type: integer
          minimum: 1
        description:
          type: string
```
