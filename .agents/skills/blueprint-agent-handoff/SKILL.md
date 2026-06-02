---
name: blueprint-agent-handoff
description: Produce a structured handoff envelope so the orchestrator can route work from one persona to the next without losing context.
blueprint-version: 1.0.0
extensibility-tier: extensible
emits-phase: implement
---

# Blueprint Agent Handoff

## When to Use

Invoked at slice boundaries during SDD step05 implementation, and at any
explicit cross-persona transition, to package the structured state the next
persona needs in order to continue without re-deriving context.

## Actor

Invoked by the `implementer` persona between slices and by any persona that
needs to hand off mid-cycle. Other personas MUST NOT invoke this skill on
behalf of an unrelated persona; skill composition is a persona-layer
responsibility per `ADR-issue-337-persona-skill-contract.md` clause 3.

## Inputs

- The current persona's run identifier and the work-item ticket id.
- The slice id (or other granular checkpoint identifier) being handed off.
- The next-persona name the orchestrator MUST consider invoking next.
- Any structured outputs from skills the current persona has invoked in
  this run.

## Steps

1. Read the current persona's run state.
2. Determine the next persona to consider invoking, drawn from the
   persona roster under `.agents/personas/`.
3. Package the structured handoff envelope described in
   `## Required Output Schema` below.
4. Return the envelope; the orchestrator is responsible for invoking the
   next persona.

## Composition

This skill MUST NOT directive-invoke any other skill. The orchestrator is
the only component that may act on the handoff envelope.

## Required Output Schema

The orchestrator emits a `phase: implement` C7 lifecycle event on skill
completion; the structured payload below is the `outcome.details` carried on
that event.

```yaml jsonschema
$schema: "http://json-schema.org/draft-07/schema#"
title: BlueprintAgentHandoffEnvelope
description: Structured cross-persona handoff envelope.
type: object
additionalProperties: false
required:
  - ticket_id
  - from_persona
  - to_persona
  - slice_id
  - summary
properties:
  ticket_id:
    type: string
  from_persona:
    type: string
    description: Persona name (basename without `.md`) under `.agents/personas/`.
  to_persona:
    type: string
    description: Persona name the orchestrator is requested to invoke next.
  slice_id:
    type: string
    description: Slice or checkpoint identifier from plan.md.
  summary:
    type: string
    description: One-paragraph summary of state the next persona needs.
  carried_outputs:
    type: array
    description: Structured outputs previously produced in this run.
    items:
      type: object
      additionalProperties: true
  blocked_on:
    type: array
    description: Optional list of explicit blockers the next persona MUST resolve before proceeding.
    items:
      type: string
```
