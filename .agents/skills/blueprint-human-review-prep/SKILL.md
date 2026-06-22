---
name: blueprint-human-review-prep
description: Package the green branch and step08 expert-panel findings into a structured payload the human merge reviewer can consume in one pass at the bounded-context human merge gate.
blueprint-version: 1.0.0
extensibility-tier: extensible
emits-phase: pr-packager
---

# Blueprint Human Review Prep

## When to Use

Invoked after the step08 expert panel has completed the `agent-pr-review`
phase and before the bounded-context human merge gate. The output is the
attention map the human merge reviewer uses to decide whether to approve
the PR.

## Actor

Invoked by the orchestrator on behalf of the documentation-discipline
expert at the end of the step08 panel cycle. The expert-panel layer MUST
NOT directive-invoke this skill; the orchestrator's dispatch table is the
binding mechanism.

## Inputs

- The packaged PR body authored by `blueprint-sdd-step07-pr-packager`.
- The per-expert verdict array (`expert_verdicts[]`) merged from the step08
  panel invocations.
- The hardening review file `hardening_review.md`.
- The work-item `traceability.md` and `graph.json`.

## Steps

1. Aggregate the step08 panel findings by severity and dimension.
2. Append the cross-context impact reporting payload assembled by the
   step08 boundary-hawk expert to the structured output.
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
completion; the structured payload below is the `outcome_details` carried on
that event.

```yaml jsonschema
$schema: "http://json-schema.org/draft-07/schema#"
title: BlueprintHumanReviewPrep
description: >-
  Attention map for the human merge reviewer at the bounded-context human
  merge gate. Built from the step08 expert_verdicts[] array.
type: object
additionalProperties: false
required:
  - ticket_id
  - expert_verdicts
  - cross_context_impact
  - unresolved_must_fix
properties:
  ticket_id:
    type: string
  expert_verdicts:
    type: array
    description: >-
      Per-expert verdict and findings array merged from the step08 panel
      invocations, keyed by expert_slug per ADR-issue-364 § 6 (two-sub-enum
      form per the F-12 amendment 2026-06-19 — EXACTLY ONE OF
      `expert_slug_blueprint` OR `expert_slug_extension` per row).
    items:
      type: object
      additionalProperties: false
      required:
        - verdict
        - findings
      oneOf:
        - required: [expert_slug_blueprint]
        - required: [expert_slug_extension]
      properties:
        expert_slug_blueprint:
          type: string
          description: >-
            Blueprint-baseline expert persona slug (sealed enum from
            ADR-issue-364 § 9; amended only via the `#339` sign-off cycle).
            EXACTLY ONE OF this field OR `expert_slug_extension` MUST be
            populated per row (oneOf above). Legacy flat-`expert_slug`
            tolerance is OUT OF SCOPE of this per-invocation schema (no
            live producer emits the old form post-amendment); historical
            local-cli C7 events that carry flat `expert_slug` are handled
            at the Central Brain (#343) ingest layer via the
            `### after: epic-343-promote` legacy-payload normalization
            entry — not at this packager schema layer (per PR #372
            11th-review Codex P2-2 separation-of-concerns fix).
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
            Consumer-overlay extension expert persona slug (open string from
            the consumer overlay's allowlist; per design-contracts.md § C7
            F-12 amendment 2026-06-19). EXACTLY ONE OF this field OR
            `expert_slug_blueprint` MUST be populated per row.
        verdict:
          type: string
          enum:
            - pass
            - revise
            - block
        findings:
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
        - finding_id
        - file
        - line
        - description
      oneOf:
        - required: [expert_slug_blueprint]
        - required: [expert_slug_extension]
      properties:
        expert_slug_blueprint:
          type: string
          description: >-
            Blueprint-baseline expert persona slug (sealed enum from
            ADR-issue-364 § 9; amended only via the `#339` sign-off cycle)
            — provenance of the finding. EXACTLY ONE OF this field OR
            `expert_slug_extension` MUST be populated per row (oneOf above).
            Legacy flat-`expert_slug` tolerance is OUT OF SCOPE of this
            per-finding schema and is handled at the Central Brain (#343)
            ingest layer per the `### after: epic-343-promote`
            legacy-payload normalization entry (per PR #372 11th-review
            Codex P2-2 separation-of-concerns fix).
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
            Consumer-overlay extension expert persona slug (open string;
            per design-contracts.md § C7 F-12 amendment 2026-06-19) —
            provenance of the finding. EXACTLY ONE OF this field OR
            `expert_slug_blueprint` MUST be populated per row.
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
