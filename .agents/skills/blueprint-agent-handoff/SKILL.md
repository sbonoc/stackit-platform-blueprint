---
name: blueprint-agent-handoff
description: Produce a structured handoff envelope so the orchestrator can route work from one SDD-step skill (and its dispatched expert) to the next without losing context.
blueprint-version: 1.0.0
extensibility-tier: extensible
emits-phase: implement
---

# Blueprint Agent Handoff

## When to Use

Invoked at slice boundaries during SDD step05 implementation (between
consecutive experts in the sequential-lens convergence) and at any explicit
cross-skill transition between SDD steps, to package the structured state
the next invocation needs in order to continue without re-deriving context.

## Actor

Invoked by an SDD-step skill running on behalf of one expert from the
dispatched panel. Other expert-panel members and downstream skills MUST NOT
invoke this skill on behalf of an unrelated invocation; skill composition is
the orchestrator's responsibility per
`ADR-issue-337-persona-skill-contract.md` clause 3 (as amended by
`ADR-issue-364-expert-persona-model.md`).

## Inputs

- The current run identifier and the work-item ticket id.
- The slice id (or other granular checkpoint identifier) being handed off.
- The next SDD-step skill the orchestrator MUST consider invoking next, plus
  any specific expert from that step's panel that the handoff is targeted
  at.
- Any structured outputs from skills the current run has invoked.

## Steps

1. Read the current run state.
2. Determine the next SDD-step skill the orchestrator should invoke, and the
   expert slug (if narrower than the full panel) that the handoff is
   directed at; the expert slug MUST be drawn from the roster under
   `.agents/personas/` (one of the 8 expert slugs locked by
   `ADR-issue-364-expert-persona-model.md`).
3. Package the structured handoff envelope described in
   `## Required Output Schema` below.
4. Return the envelope; the orchestrator is responsible for invoking the
   next SDD-step skill and dispatching the panel.

## Composition

This skill MUST NOT directive-invoke any other skill. The orchestrator is
the only component that may act on the handoff envelope, and the
orchestrator's dispatch table (design-contracts § C3) is the binding
mechanism for which expert is consulted next.

## Required Output Schema

The orchestrator emits a `phase: implement` C7 lifecycle event on skill
completion; the structured payload below is the `outcome.details` carried on
that event.

```yaml jsonschema
$schema: "http://json-schema.org/draft-07/schema#"
title: BlueprintAgentHandoffEnvelope
description: Structured cross-skill handoff envelope.
type: object
additionalProperties: false
required:
  - ticket_id
  - from_step
  - to_step
  - slice_id
  - summary
properties:
  ticket_id:
    type: string
  from_step:
    type: string
    description: SDD-step skill basename (e.g., blueprint-sdd-step05-implement) the handoff is leaving.
  to_step:
    type: string
    description: SDD-step skill basename the orchestrator is requested to invoke next.
  expert_slug:
    type: string
    description: >-
      Optional expert slug from .agents/personas/ this handoff is directed at,
      drawn from the 8-expert roster locked by ADR-issue-364. Omit when the
      handoff is to the full panel of the next step.
    enum:
      - product-pragmatist
      - boundary-hawk
      - security-paranoid
      - data-privacy
      - test-quality-sceptic
      - operability-sre
      - documentation-discipline
      - performance-cost-aware
  slice_id:
    type: string
    description: Slice or checkpoint identifier from plan.md.
  summary:
    type: string
    description: One-paragraph summary of state the next invocation needs.
  carried_outputs:
    type: array
    description: Structured outputs previously produced in this run.
    items:
      type: object
      additionalProperties: true
  blocked_on:
    type: array
    description: Optional list of explicit blockers the next invocation MUST resolve before proceeding.
    items:
      type: string
```
