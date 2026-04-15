---
name: blueprint-sdd-intake-decompose
description: Transform a high-level MVP/business requirements document into independent Spec-Driven Development work items with stable requirement IDs, bounded-context decomposition, scaffolded spec folders, and an explicit readiness/clarification gate.
---

# Blueprint SDD Intake And Decompose

## When to Use
Use this skill when requirements arrive as one large document (for example jobs-to-be-done, MVP scope, or initiative brief) and must be split into independent SDD work items.

## Guardrails
1. Treat consumer `AGENTS.md` as the lifecycle/governance source.
2. During `Discover`, `High-Level Architecture`, `Specify`, and `Plan`, do not replace missing requirements with assumptions.
3. Keep each new work item at `SPEC_READY=false` until all blockers are resolved.
4. Mark unresolved inputs as `BLOCKED_MISSING_INPUTS`.
5. Use deterministic requirement IDs (`REQ-###`) and preserve source wording.

## Workflow
1. Confirm input sources and scope boundaries.
2. Extract atomic requirements and assign stable IDs (`REQ-###`).
3. Group requirements by bounded context and dependency direction.
4. Propose one spec slug per independent group.
5. Scaffold each work item:
```bash
make spec-scaffold SPEC_SLUG=<bounded-context-slug> SPEC_TRACK=consumer
```
6. Populate each `spec.md` with:
   - mapped `REQ-###`
   - applicable `SDD-C-###` control IDs
   - `SPEC_READY=false` until resolved
7. Produce a master mapping table (`REQ -> spec slug`) and explicit unresolved questions list.

## Required Report Format
Return:
1. Input document(s) analyzed.
2. Total `REQ-###` extracted.
3. Proposed independent spec folders (ordered by dependency).
4. `REQ -> spec` matrix.
5. Open blockers (`BLOCKED_MISSING_INPUTS`) per spec.
6. Suggested next step (`clarification gate` or `plan slicing`).

## References
- Intake checklist: `references/intake_checklist.md`
