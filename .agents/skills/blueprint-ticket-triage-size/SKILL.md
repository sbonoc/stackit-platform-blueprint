---
name: blueprint-ticket-triage-size
description: Classify an incoming ticket into small | medium | large-decomposable | escalate per the Phase 0 triage-size threshold ADR, and emit the bounded-context candidates the ticket touches.
blueprint-version: 1.0.0
extensibility-tier: extensible
emits-phase: intake
---

# Blueprint Ticket Triage Size

## When to Use

This skill runs first on every accepted ticket, before any other persona-side
work begins. The orchestrator (issue #333, Child B) wraps the skill invocation
and emits the resulting `phase: intake` C7 event.

## Actor

Invoked by the `tech-lead` persona once per ticket. Other personas MUST NOT
invoke this skill directly; skill composition is a persona-layer
responsibility per `ADR-issue-337-persona-skill-contract.md` clause 3.

## Inputs

- Ticket identifier (GitHub issue number) and full body.
- Repository policy surface (`AGENTS.md`, `blueprint/contract.yaml`,
  the Phase 0 threshold ADR at
  `docs/blueprint/architecture/decisions/ADR-issue-337-triage-size-threshold.md`).
- The bounded-context catalogue referenced from the parameterized
  C5 / C6 overlays in `docs/blueprint/autonomous-factory/design-contracts.md`.

## Steps

1. Read the ticket body, labels, and any linked tickets.
2. Apply the size threshold defined in
   `ADR-issue-337-triage-size-threshold.md` to produce a single
   classification value drawn from the enum
   `small | medium | large-decomposable | escalate`.
3. Identify the bounded-context candidates the ticket touches, drawn from
   the bounded-context catalogue.
4. Return the structured output described in `## Required Output Schema`
   below. When classification is NOT `large-decomposable`, the orchestrator
   emits the `phase: intake` C7 event immediately on this skill's return.
   When classification IS `large-decomposable`, emission is deferred until
   `blueprint-ticket-decompose-light` also returns so the two outputs are
   combined into a single `phase: intake` event per the sealed one-event-per-
   phase-boundary rule (ADR-issue-337-c7-emission-mechanism.md).

## Composition

This skill MUST NOT directive-invoke any other skill. When the classification
is `large-decomposable`, the persona that invoked this skill (the `tech-lead`
persona) will subsequently invoke `blueprint-ticket-decompose-light` per its
own persona definition. The two skills are composed at the persona layer,
not inside any skill runbook.

## Required Output Schema

The orchestrator emits a `phase: intake` C7 lifecycle event after the
tech-lead persona's full intake phase is complete. When classification is
NOT `large-decomposable`, this skill's output is the sole `outcome.details`
payload. When `large-decomposable`, the output is combined with the
`blueprint-ticket-decompose-light` output into the single event emitted
after both skills return.

```yaml jsonschema
$schema: "http://json-schema.org/draft-07/schema#"
title: BlueprintTicketTriageSizeOutput
description: >-
  Triage classification + bounded-context candidates for an accepted ticket.
type: object
additionalProperties: false
required:
  - ticket_id
  - classification
  - bounded_context_candidates
  - rationale
properties:
  ticket_id:
    type: string
    description: GitHub issue identifier of the triaged ticket.
  classification:
    type: string
    enum:
      - small
      - medium
      - large-decomposable
      - escalate
  bounded_context_candidates:
    type: array
    items:
      type: string
    description: >-
      Names of the bounded contexts the ticket touches, drawn from the
      bounded-context catalogue.
  rationale:
    type: string
    description: Single-paragraph justification for the chosen classification.
  next_persona_hint:
    type: string
    description: >-
      Optional non-binding hint identifying the next persona the orchestrator
      MAY invoke. The orchestrator is authoritative; this field is advisory.
```
