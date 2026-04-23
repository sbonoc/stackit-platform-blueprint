---
name: blueprint-sdd-po-spec
description: Guide the Product Owner through the spec intake phase and direct the coding agent to draft the technical ADR layer with Mermaid diagrams, producing a spec intake PR with Product sign-off only.
---

# Blueprint SDD PO Spec Intake

## When to Use
Use this skill when a Product Owner is starting a new SDD work item and wants to:
1. Write `spec.md` (product context: FRs, NFRs, ACs, objective, contract changes).
2. Write the ADR Product Context Layer (business objective, decision drivers).
3. Have the coding agent draft the ADR Technical Decision Layer (options, analysis,
   recommended option, Mermaid diagrams).
4. Open a spec intake PR gated by the Product sign-off only (`SPEC_PRODUCT_READY=true`).

## Two-Actor Model

### Product Owner writes
- `spec.md`: Objective, Normative Requirements (FRs/NFRs), Normative Option Decision
  (business-framed alternatives), Contract Changes, Normative Acceptance Criteria.
  Sets `SPEC_PRODUCT_READY: true`, `Product sign-off: approved`.
- ADR `## Product Context Layer`: Business Objective and Requirement Summary,
  Decision Drivers. Sets `ADR product context sign-off: approved`.

### Coding Agent generates
- ADR `## Technical Decision Layer`: Options enumerated from codebase analysis,
  pros/cons in this repo's context, recommended option (labeled as agent draft),
  consequences, Mermaid diagrams with type chosen per work item nature.
- Agent MUST NOT self-approve any sign-off field.
- Agent MUST label the Technical Decision Layer with the block quote draft notice.
- Agent does NOT generate `plan.md`, `tasks.md`, or `architecture.md` in this phase.

## Diagram Selection Heuristics
The agent selects the Mermaid diagram type(s) that best illuminate the work item:
- **Sequence diagram** → HTTP request flows across services or components
- **ER diagram** → data models and entity relationships
- **User Journey** → user-facing business flows and step sequences
- **Flowchart** → data flows, decision branches, script control flow
- **State diagram** → lifecycle state machines (orders, sessions, jobs)
- **C4 / class diagram** → component or module structure

Use multiple diagrams when the work item spans multiple concerns. Add a one-sentence
caption per diagram explaining what it shows and why this type was chosen.
If no diagram adds clarity, state: "No diagram required — [one-line rationale]."

The PO's ADR product context sign-off covers: "the problem statement, decision
drivers, and option list accurately reflect the product need." It does NOT cover
the technical analysis or selected option.

## Guardrails
1. Agent MUST NOT self-approve `Product sign-off`, `Architecture sign-off`,
   `Security sign-off`, `Operations sign-off`, `ADR product context sign-off`,
   or `ADR technical decision sign-off`.
2. Agent MUST label the Technical Decision Layer with the block quote notice.
   The notice is removed only when the architect gives `ADR technical decision sign-off`.
3. Agent MUST NOT generate `plan.md`, `tasks.md`, or `architecture.md` in this phase.
4. Keep `SPEC_READY: false` — only `SPEC_PRODUCT_READY: true` is set in this phase.
5. Run `make quality-sdd-check` before opening the spec intake PR.
6. Spec intake PR requires: `spec.md` (`SPEC_PRODUCT_READY: true`, `Product sign-off: approved`)
   + ADR file (`Status: draft`, `ADR path` set in spec.md, `ADR product context sign-off` given).

## Workflow

```
1. make spec-scaffold SPEC_SLUG=<slug>
2. PO: write spec.md — objective, FRs, NFRs, ACs, contract changes
3. PO: write ADR ## Product Context Layer — business objective, decision drivers
4. Agent: analyze spec + codebase
5. Agent: generate ADR ## Technical Decision Layer + Mermaid diagram(s)
6. PO: review agent output, correct misrepresentations
7. PO: give ADR product context sign-off in ADR metadata
8. PO: set SPEC_PRODUCT_READY: true, Product sign-off: approved, ADR status: draft
9. make quality-sdd-check   # must pass before PR
10. Open spec intake PR
```

## Spec Completion (Next Phase — Not PO-Owned)
After the spec intake PR merges, a CTO or architect-owned PR adds:
- `architecture.md`, `plan.md`, `tasks.md`, `traceability.md`, `graph.json`
- All remaining sign-offs (`Architecture`, `Security`, `Operations`)
- `ADR technical decision sign-off` (architect validates or overrides agent recommendation)
- `SPEC_READY: true`

## Useful Commands
```bash
make spec-scaffold SPEC_SLUG=<slug>
make quality-sdd-check
```

## Required Report Format
Return:
1. `spec.md` completeness summary (FRs, NFRs, ACs populated).
2. ADR Product Context Layer completeness.
3. ADR Technical Decision Layer generated: options enumerated, recommended option, diagrams.
4. Diagram type(s) chosen and rationale.
5. `quality-sdd-check` result.
6. Spec intake PR readiness statement.

## References
- PO spec intake checklist: `references/po_spec_intake_checklist.md`
