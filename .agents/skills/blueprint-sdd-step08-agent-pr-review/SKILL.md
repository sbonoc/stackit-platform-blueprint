---
name: blueprint-sdd-step08-agent-pr-review
description: Produce a structured findings list against the work-item PR diff at SDD step 08; one invocation per expert from the dispatched expert panel, returning a per-expert verdict array aligned with C7 outcome.details.expert_verdicts[].
blueprint-version: 1.0.0
extensibility-tier: extensible
emits-phase: agent-pr-review
---

# Blueprint SDD Step 08 — Agent PR Review

## Steps covered

- **Step 8** — Agent PR review pass that produces the structured findings
  list the human merge reviewer reads at the bounded-context human merge gate.

## When to Use

Invoked after the PR body has been authored by
`blueprint-sdd-step07-pr-packager` and before the human merge gate. The
orchestrator dispatches the full 8-expert panel for step08 per the SDD-step ×
expert matrix in `docs/blueprint/autonomous-factory/design-contracts.md` § C3
(structured-disagreement convergence mode). Each invocation reviews the PR
under exactly one expert lens and contributes one verdict to the panel array.

## Actor

Invoked once per expert in the panel dispatched for step08. The orchestrator
is the binding mechanism for which experts are consulted; the
expert-panel layer MUST NOT directive-invoke this skill. The
reviewer-model-heterogeneity ADR at
`docs/blueprint/architecture/decisions/ADR-issue-337-reviewer-model-heterogeneity.md`
requires that the reviewing experts run on a different model family than the
expert who produced the step05 output under review; the orchestrator (Child B)
enforces the model-rotation pick when assembling the panel for step08.

## Inputs

- The full work-item PR diff against the base branch.
- The single `expert_slug` this invocation is reviewing under (drawn from the
  step08 panel-input parameter the orchestrator supplies).
- The packaged PR body authored by the PR packager.
- The work-item `traceability.md` and `graph.json`.
- The expert's `## Worldview`, `## Default Heuristics`, `## Push-back Triggers`,
  `## What I Notice That Others Miss`, and `## Quality Bar` sections loaded
  from `.agents/personas/<expert_slug>/PERSONA.md`.

## Workflow

1. Read the PR diff and the expert's loaded persona sections.
2. Generate findings, one entry per concrete observation, tagged with
   severity drawn from the enum `must-fix | warn | info`.
3. Anchor every finding to a concrete diff location (`file` + `line`).
4. Compute a single per-expert verdict drawn from the enum `pass | revise |
   block`, following the verdict priority rule defined in
   `ADR-issue-364-expert-persona-model.md` § 6 (block > revise > pass).
5. Return the structured payload described in `## Required Output Schema`
   below; the orchestrator merges per-expert payloads into the
   structured-disagreement convergence output for step08.

## Guardrails

This skill MUST NOT directive-invoke any other skill (FR-016 composition
ban). Each expert invocation is independent; the orchestrator merges the
per-expert verdict arrays into the C7 `outcome.details.expert_verdicts[]`
field per `ADR-issue-337-c7-emission-mechanism.md` (amended by
`ADR-issue-364-expert-persona-model.md` § 9) and per design-contracts § C7.

## Required Report Format

Return:

1. The `expert_slug` this invocation was dispatched under.
2. Findings count grouped by severity (`must-fix`, `warn`, `info`).
3. For each finding: id, dimension (drawn from the expert's `## Push-back
   Triggers` set), severity, `file:line`, description, and optional
   remediation suggestion.
4. The single per-expert verdict (`pass | revise | block`) computed by the
   verdict priority rule.
5. Confirmation that every finding is anchored to a concrete diff location.

## Required Output Schema

The orchestrator emits a `phase: agent-pr-review` C7 lifecycle event after
merging the per-expert payloads from all dispatched experts; the structured
payload below is one row in the merged `outcome.details.expert_verdicts[]`
array carried on that event.

```yaml jsonschema
$schema: "http://json-schema.org/draft-07/schema#"
title: BlueprintAgentPrReviewOutput
description: >-
  Structured per-expert verdict and findings list produced by one expert-panel
  invocation during the SDD step08 agent PR review phase. The orchestrator
  merges these into the panel-level expert_verdicts[] array carried on the
  C7 agent-pr-review event.
type: object
additionalProperties: false
required:
  - ticket_id
  - expert_slug
  - verdict
  - findings
properties:
  ticket_id:
    type: string
  expert_slug:
    type: string
    description: >-
      Basename of the expert persona file under .agents/personas/, drawn from
      the 8-expert roster locked by ADR-issue-364-expert-persona-model.md.
    enum:
      - product-pragmatist
      - boundary-hawk
      - security-paranoid
      - data-privacy
      - test-quality-sceptic
      - operability-sre
      - documentation-discipline
      - performance-cost-aware
  verdict:
    type: string
    description: >-
      Single per-expert verdict computed by the priority rule defined in
      ADR-issue-364-expert-persona-model.md § 6 (block > revise > pass).
    enum:
      - pass
      - revise
      - block
  findings:
    type: array
    description: >-
      Per-finding list (may be empty when verdict is pass). Each finding is
      anchored to a concrete diff location and tagged with severity.
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
          description: >-
            One of the expert's ## Push-back Triggers bullets, used as the
            finding's classification dimension.
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
```

The orchestrator MUST aggregate one such payload per dispatched expert into
the `expert_verdicts` array on the panel-level C7 event payload:

```yaml
outcome:
  details:
    expert_verdicts:
      - { expert_slug: ..., verdict: ..., findings: [...] }
      - { expert_slug: ..., verdict: ..., findings: [...] }
```

per design-contracts § C7 and FR-007 of `ADR-issue-364-expert-persona-model.md`.
