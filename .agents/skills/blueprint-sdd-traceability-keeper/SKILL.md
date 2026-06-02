---
name: blueprint-sdd-traceability-keeper
description: Maintain and verify traceability from requirements to specs, implementation, tests, and docs with drift detection and explicit gap reporting.
blueprint-version: 1.0.0
---

# Blueprint SDD Traceability Keeper

## When to Use
Use this skill during planning, implementation, and pre-merge hardening to ensure no requirement loses coverage.

## Governance Context

`AGENTS.md` is the canonical policy source for this skill. Sections that apply:

- `§ SDD Artifact Contract` — `traceability.md` is a required artifact; every REQ/NFR/AC must have explicit links to design, implementation, test, and doc evidence.
- `§ Cross-Cutting Guardrails (Must Be Captured in Discover + Specify)` — traceability verification confirms that observability, security, and API-contract-first guardrails declared in `spec.md` are actually covered by implementation and test evidence.
- `§ Hardening Review Gate` — complete traceability is a precondition for the hardening review; gaps block the Publish gate.
- `§ Testing and Quality Ratios` — verifying that automated tests exist for every requirement supports the 100% business-critical coverage mandate.

> If `AGENTS.md` changes any of the above sections, update this block to reflect the affected sections.

## Guardrails
1. Every `REQ-###` must map to at least one spec statement.
2. Every implemented requirement must map to at least one automated test.
3. Every changed behavior must map to docs updates when user-facing or operationally relevant.
4. Report unmapped items as blocking gaps.

## Workflow
1. Read `traceability.md` for each active work item.
2. Verify links across:
   - `REQ-###` -> `spec.md`
   - `spec.md` -> code path(s)
   - code path(s) -> test assertion(s)
   - behavior change -> docs path(s)
3. Flag orphan requirements, orphan tests, and undocumented behavior changes.
4. Update traceability tables and evidence links.
5. Re-run SDD governance checks.

## Useful Commands
```bash
make quality-sdd-check
make quality-sdd-check-all
```

## Required Report Format
Return:
1. Work items inspected.
2. Coverage summary (`REQ`, code, tests, docs).
3. Blocking traceability gaps.
4. Drift fixes applied.
5. Residual risks.

## References
- Traceability matrix template: `references/traceability_matrix_template.md`

## Required Output Schema

The structured payload below is the traceability report the skill returns to
the calling SDD-step skill or to the orchestrator.

```yaml jsonschema
$schema: "http://json-schema.org/draft-07/schema#"
title: BlueprintSddTraceabilityKeeperOutput
description: Structured traceability report produced by the keeper skill.
type: object
additionalProperties: false
required:
  - work_items_inspected
  - coverage_summary
  - blocking_gaps
properties:
  work_items_inspected:
    type: array
    items:
      type: string
  coverage_summary:
    type: object
    additionalProperties: false
    required:
      - req_count
      - code_link_count
      - test_link_count
      - docs_link_count
    properties:
      req_count:
        type: integer
        minimum: 0
      code_link_count:
        type: integer
        minimum: 0
      test_link_count:
        type: integer
        minimum: 0
      docs_link_count:
        type: integer
        minimum: 0
  blocking_gaps:
    type: array
    items:
      type: object
      additionalProperties: false
      required:
        - kind
        - subject
        - description
      properties:
        kind:
          type: string
          enum:
            - orphan-requirement
            - orphan-test
            - undocumented-behavior
            - missing-spec-link
            - missing-code-link
        subject:
          type: string
        description:
          type: string
  drift_fixes_applied:
    type: array
    items:
      type: string
  residual_risks:
    type: array
    items:
      type: string
```
