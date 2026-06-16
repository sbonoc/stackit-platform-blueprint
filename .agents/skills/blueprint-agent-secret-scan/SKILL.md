---
name: blueprint-agent-secret-scan
description: Scan a work-item branch diff for credentials, API tokens, private-key material, and PII; produce a structured findings list consumed by the security-paranoid and data-privacy experts during the hardening-review pass.
blueprint-version: 1.0.0
extensibility-tier: extensible
emits-phase: implement
---

# Blueprint Agent Secret Scan

## When to Use

This skill runs as part of the hardening-review pass that the orchestrator
schedules after step05 reports all `plan.md` slices green. The orchestrator
invokes the skill on behalf of the security-paranoid and data-privacy
experts (panel for the hardening-review pass per design-contracts § C3) and
integrates the findings into `hardening_review.md`.

## Actor

Invoked by the orchestrator on behalf of the hardening-review expert panel
(security-paranoid + data-privacy). The expert-panel layer MUST NOT
directive-invoke this skill; the orchestrator's dispatch table is the
binding mechanism per
`ADR-issue-337-persona-skill-contract.md` (as amended by
`ADR-issue-364-expert-persona-model.md`).

## Inputs

- The work-item branch diff against the base branch.
- The repository-wide secret-pattern baseline sourced from:
  - `blueprint/contract.yaml` § `spec.normative_language.unresolved_marker_tokens` —
    the canonical list of unresolved-work-marker tokens (e.g. `TBD`, `TBC`).
  - `scripts/bin/quality/check_sdd_assets.py` — the normative placeholder and
    secret-pattern definitions (angle-bracket placeholders, SDD unresolved-work
    markers, and the baseline credential patterns) used by `make quality-sdd-check`.
  - OWASP / regex patterns for secret material: AWS access keys (`AKIA[A-Z0-9]{16}`),
    PEM private-key armor (`-----BEGIN.*PRIVATE KEY-----`), GitHub bearer tokens
    (`ghp_[A-Za-z0-9]{36}`), Slack tokens (`xoxb-`).
- The PII detection heuristics declared in the spec NFR-SEC block.

## Steps

1. Enumerate every added or modified file in the work-item branch diff.
2. Apply the secret-pattern baseline (AWS access keys, PEM private-key
   armor, GitHub bearer tokens, Slack tokens) and the PII heuristics
   against each file's added lines.
3. Apply the angle-bracket placeholder and SDD unresolved-work-marker
   token scans against new persona / skill / spec markdown files
   per FR-008 of issue #360.
4. Return the structured output described in `## Required Output Schema`
   below. Severity is one of `must-fix | warn | info`.

## Composition

This skill MUST NOT directive-invoke any other skill. The orchestrator
composes the secret-scan output with the other hardening-review inputs
when assembling the hardening-review panel result.

## Required Output Schema

The orchestrator emits a `phase: implement` C7 lifecycle event on skill
completion; the structured payload below is the `outcome_details` carried on
that event.

```yaml jsonschema
$schema: "http://json-schema.org/draft-07/schema#"
title: BlueprintAgentSecretScanOutput
description: >-
  Findings list from the secret + PII + placeholder scan over the work-item
  branch diff.
type: object
additionalProperties: false
required:
  - ticket_id
  - findings
  - files_scanned
properties:
  ticket_id:
    type: string
    description: GitHub issue identifier of the work item being scanned.
  files_scanned:
    type: integer
    minimum: 0
  findings:
    type: array
    items:
      type: object
      additionalProperties: false
      required:
        - kind
        - severity
        - file
        - line
        - description
      properties:
        kind:
          type: string
          enum:
            - secret-material
            - pii
            - placeholder
            - unresolved-marker
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
  clean:
    type: boolean
    description: True when no must-fix findings remain.
```
