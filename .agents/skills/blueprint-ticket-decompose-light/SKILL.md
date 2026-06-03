---
name: blueprint-ticket-decompose-light
description: Decompose a large-decomposable ticket into bounded-context child tickets per the Phase 0 light-decomposition policy ADR, capping fan-out at the policy maximum.
blueprint-version: 1.0.0
extensibility-tier: extensible
emits-phase: intake
---

# Blueprint Ticket Decompose Light

## When to Use

This skill runs immediately after `blueprint-ticket-triage-size` when the
triage classification is `large-decomposable`. It produces the child ticket
envelopes the orchestrator will hand off to fresh `blueprint-sdd-step01-intake`
invocations for child-spec authoring.

## Actor

Invoked by the orchestrator on behalf of the step01 expert panel only when
triage returned `classification: large-decomposable`. The expert-panel
layer MUST NOT directive-invoke this skill; the orchestrator's dispatch
table in design-contracts § C3 is the binding mechanism.

## Inputs

- The parent ticket identifier and body.
- The triage-size output for the parent ticket.
- The Phase 0 light-decomposition policy ADR at
  `docs/blueprint/architecture/decisions/ADR-issue-337-light-decomposition-policy.md`.
- The bounded-context catalogue.

## Steps

1. Read the parent ticket and the triage output.
2. Apply the decomposition heuristic defined in
   `ADR-issue-337-light-decomposition-policy.md` to enumerate child ticket
   candidates, one per bounded-context boundary.
3. Cap the number of child envelopes at the maximum fan-out value pinned
   by the policy ADR. If the natural fan-out exceeds the cap, return the
   first N candidates and flag the excess in the rationale field.
4. Return the structured output described in `## Required Output Schema`
   below.

## Composition

This skill MUST NOT directive-invoke any other skill. The orchestrator
subsequently hands each child envelope to a fresh
`blueprint-sdd-step01-intake` invocation per the dispatch rules in
design-contracts § C3.

## Required Output Schema

The orchestrator emits exactly ONE `phase: intake` C7 lifecycle event after
the step01 panel's full intake phase is complete — that is, after BOTH
`blueprint-ticket-triage-size` AND this skill have returned. This skill does
NOT trigger a separate emission; its output is included alongside the
triage-size output in the `outcome.details` of that single event.

```yaml jsonschema
$schema: "http://json-schema.org/draft-07/schema#"
title: BlueprintTicketDecomposeLightOutput
description: >-
  Child ticket envelopes derived from a large-decomposable parent ticket.
type: object
additionalProperties: false
required:
  - parent_ticket_id
  - children
  - rationale
properties:
  parent_ticket_id:
    type: string
    description: GitHub issue identifier of the parent ticket being decomposed.
  children:
    type: array
    minItems: 1
    items:
      type: object
      additionalProperties: false
      required:
        - title
        - bounded_context
        - parent_spec_grounding
      properties:
        title:
          type: string
          description: Concise title for the child ticket.
        bounded_context:
          type: string
          description: Bounded-context name the child ticket is scoped to.
        parent_spec_grounding:
          type: string
          description: >-
            Reference into the parent spec.md section that grounds this child
            ticket; child tickets MUST cite parent grounding.
        boundary_type:
          type: string
          enum:
            - capability-extension
            - cross-context-contract
            - operational-surface
            - documentation-surface
  rationale:
    type: string
    description: Justification for the chosen decomposition; cites the fan-out cap if reached.
  fan_out_cap_reached:
    type: boolean
    description: >-
      True when the natural fan-out exceeded the policy cap; the excess MUST
      be enumerated in rationale so the orchestrator can decide whether to
      file follow-up tickets.
```
