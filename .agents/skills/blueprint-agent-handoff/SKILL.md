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

Invoked by the orchestrator to checkpoint the current expert run and hand
off execution to the next SDD-step skill or expert. The expert-panel layer
and other skills MUST NOT directive-invoke this skill; skill composition is
the orchestrator's responsibility exclusively per
`ADR-issue-337-persona-skill-contract.md` clause 3 (as amended by
`ADR-issue-364-expert-persona-model.md`). The orchestrator acts on the
returned handoff envelope to determine the next dispatch target.

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
completion; the structured payload below is the `outcome_details` carried on
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
# Mutual exclusion between the two optional slug sub-enums enforced at the
# schema level (per PR #372 13th-review Codex P2-2). A handoff envelope MAY
# populate AT MOST ONE of `expert_slug_blueprint` OR `expert_slug_extension`;
# populating BOTH is a contract violation rejected by JSON Schema validation
# before the orchestrator's pre-dispatch checks run, eliminating the
# ambiguous-target failure mode where the orchestrator would have to choose
# silently between two named expert targets.
not:
  required: [expert_slug_blueprint, expert_slug_extension]
properties:
  ticket_id:
    type: string
  from_step:
    type: string
    description: SDD-step skill basename (e.g., blueprint-sdd-step05-implement) the handoff is leaving.
  to_step:
    type: string
    description: SDD-step skill basename the orchestrator is requested to invoke next.
  expert_slug_blueprint:
    type: string
    description: >-
      Optional blueprint-baseline expert slug this handoff is directed at,
      from the sealed enum below (per ADR-issue-364 § 9; amended only via
      the `#339` sign-off cycle). Mutually exclusive with `expert_slug_extension`
      (a handoff MAY populate AT MOST ONE of the two; populating both is a
      contract violation enforced by the orchestrator's pre-dispatch validation).
      Omit BOTH when the handoff is to the full panel of the next step.
      Migrated 2026-06-20 per PR #372 11th-review Claude finding #2 (the
      pre-migration single `expert_slug` field with a closed 8-item enum
      blocked handoffs targeting either the 9th blueprint slug
      `usability-pragmatist` from `#361.5` or any consumer-overlay
      extension expert).
    enum:
      - product-pragmatist
      - boundary-hawk
      - security-paranoid
      - data-privacy
      - test-quality-sceptic
      - operability-sre
      - documentation-discipline
      - performance-cost-aware
  expert_slug_extension:
    type: string
    description: >-
      Optional consumer-overlay extension expert slug this handoff is
      directed at (open string from the consumer overlay's allowlist; per
      design-contracts.md § C7 F-12 amendment 2026-06-19). Mutually
      exclusive with `expert_slug_blueprint` (see above). Omit BOTH when
      the handoff is to the full panel of the next step.
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
