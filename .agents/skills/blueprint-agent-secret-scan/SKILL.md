---
name: blueprint-agent-secret-scan
description: Scan a work-item branch diff for credentials, API tokens, private-key material, and PII; produce a structured findings list for the devsecops-qa persona.
blueprint-version: 1.0.0
extensibility-tier: extensible
emits-phase: implement
---

# Blueprint Agent Secret Scan

## When to Use

This skill runs as part of the hardening-review pass after the implementer
persona reports all `plan.md` slices green. The devsecops-qa persona invokes
the skill and integrates the findings into `hardening_review.md`.

## Actor

Invoked by the `devsecops-qa` persona. Other personas MUST NOT invoke this
skill directly.

## Inputs

- The work-item branch diff against the base branch.
- The repository-wide secret-pattern baseline (the same baseline used by the
  test-suite scanners in `tests/blueprint/personas_skills/test_no_placeholders_no_secrets.py`).
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

This skill MUST NOT directive-invoke any other skill. The devsecops-qa
persona composes the secret-scan output with the other hardening-review
inputs in its own persona definition.

## Required Output Schema

The orchestrator emits a `phase: implement` C7 lifecycle event on skill
completion; the structured payload below is the `outcome.details` carried on
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
