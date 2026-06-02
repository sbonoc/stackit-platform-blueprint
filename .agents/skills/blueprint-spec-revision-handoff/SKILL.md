---
name: blueprint-spec-revision-handoff
description: Return a child ticket from the tech-lead persona to a fresh po-analyst persona invocation for spec revision when light decomposition uncovers a missing or ambiguous parent-spec section.
blueprint-version: 1.0.0
extensibility-tier: extensible
emits-phase: intake
---

# Blueprint Spec Revision Handoff

## When to Use

Invoked when `blueprint-ticket-decompose-light` produces a child ticket whose
parent_spec_grounding cannot be resolved to a concrete `spec.md` section, or
when an in-flight child spec discovers that the parent spec is missing a
required normative section.

## Actor

Invoked by the `tech-lead` persona. Other personas MUST NOT invoke this
skill directly.

## Inputs

- The parent ticket id and the child ticket id (when applicable).
- The path to the parent `spec.md` under `specs/`.
- The unresolved grounding citation that triggered the revision handoff.

## Steps

1. Read the parent spec at the cited section.
2. Identify the smallest revision the po-analyst persona MUST author to
   resolve the grounding gap.
3. Return the structured payload described in `## Required Output Schema`
   below. The orchestrator routes the payload to a fresh po-analyst
   persona invocation.

## Composition

This skill MUST NOT directive-invoke any other skill. The orchestrator
routes the revision request to the po-analyst persona per its own
persona definition.

## Required Output Schema

The orchestrator emits a `phase: intake` C7 lifecycle event on skill
completion; the structured payload below is the `outcome.details` carried on
that event.

```yaml jsonschema
$schema: "http://json-schema.org/draft-07/schema#"
title: BlueprintSpecRevisionHandoff
description: >-
  Payload requesting a po-analyst persona revision pass on a parent spec.
type: object
additionalProperties: false
required:
  - parent_ticket_id
  - parent_spec_path
  - unresolved_grounding
  - proposed_revision_summary
properties:
  parent_ticket_id:
    type: string
  child_ticket_id:
    type: string
    description: Identifier of the child ticket that surfaced the gap; omit if the gap was surfaced from triage alone.
  parent_spec_path:
    type: string
    description: Relative path to the parent spec.md under specs/.
  unresolved_grounding:
    type: string
    description: Verbatim grounding citation that could not be resolved.
  proposed_revision_summary:
    type: string
    description: One-paragraph description of the smallest revision the po-analyst MUST author.
  blocking:
    type: boolean
    description: True when the revision MUST land before any in-flight child ticket can resume.
```
