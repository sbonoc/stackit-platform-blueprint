---
name: blueprint-spec-review-prep
description: Package the spec.md, plan.md, and Spec Readiness Gate state into a structured payload the human spec-sign-off reviewer can consume in one pass.
blueprint-version: 1.0.0
extensibility-tier: extensible
emits-phase: spec-complete
---

# Blueprint Spec Review Prep

## When to Use

Invoked once the open-questions count is zero and the `Spec Readiness Gate`
in `spec.md` is awaiting the final sign-off pass. The output primes the
attention map for the four human sign-off roles (Product, Architecture,
Security, Operations) without itself granting any sign-off.

## Actor

Invoked by the orchestrator on behalf of the step03 expert
(`documentation-discipline` only, per the design-contracts § C3 dispatch
matrix for `step03-spec-complete` — a panel-of-1 sequential-lens run).
The expert-panel layer MUST NOT directive-invoke this skill; the
orchestrator's dispatch table in design-contracts § C3 is the binding
mechanism.

## Inputs

- The work-item `spec.md`, `plan.md`, `tasks.md`, `traceability.md`, and
  `graph.json`.
- The current `Spec Readiness Gate` field values.
- The list of open-question rows resolved during the resolve-questions step
  and the rationales captured for each resolution.

## Steps

1. Read the spec and current readiness-gate state.
2. Aggregate the resolved open-question rows into a single
   chronologically-ordered list with decision dates and deciders.
3. Map each canonical sign-off role to the spec sections most relevant to
   its judgement; this is an attention-routing map, NOT a sign-off
   recommendation.
4. Return the structured payload described in `## Required Output Schema`
   below.

## Composition

This skill MUST NOT directive-invoke any other skill. Sign-off granting is
strictly governed by the canonical phrases in
`AGENTS.md § Sign-off Phrases (Deterministic)` and MUST come from an
authorised human.

## Required Output Schema

The orchestrator emits a `phase: spec-complete` C7 lifecycle event on skill
completion; the structured payload below is the `outcome_details` carried on
that event.

```yaml jsonschema
$schema: "http://json-schema.org/draft-07/schema#"
title: BlueprintSpecReviewPrep
description: >-
  Attention-routing map and resolved-question history packaged for the
  human spec-sign-off reviewer.
type: object
additionalProperties: false
required:
  - ticket_id
  - readiness_gate
  - resolved_questions
  - attention_map
properties:
  ticket_id:
    type: string
  readiness_gate:
    type: object
    additionalProperties: false
    required:
      - spec_ready
      - spec_product_ready
      - open_questions_count
      - product_signoff
      - architecture_signoff
      - security_signoff
      - operations_signoff
    properties:
      spec_ready:
        type: boolean
      spec_product_ready:
        type: boolean
      open_questions_count:
        type: integer
        minimum: 0
      product_signoff:
        type: string
      architecture_signoff:
        type: string
      security_signoff:
        type: string
      operations_signoff:
        type: string
  resolved_questions:
    type: array
    items:
      type: object
      additionalProperties: false
      required:
        - id
        - question
        - resolution
        - decision_date
      properties:
        id:
          type: string
        question:
          type: string
        resolution:
          type: string
        decision_date:
          type: string
          description: ISO-8601 date.
        decided_by:
          type: string
  attention_map:
    type: object
    additionalProperties: false
    required:
      - product
      - architecture
      - security
      - operations
    properties:
      product:
        type: array
        items:
          type: string
      architecture:
        type: array
        items:
          type: string
      security:
        type: array
        items:
          type: string
      operations:
        type: array
        items:
          type: string
```
