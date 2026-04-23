# PO Spec Intake Checklist

## spec.md completeness
- [ ] Objective section: business outcome and success metric populated.
- [ ] Normative Requirements: at least one FR and one NFR per category (SEC, OBS, REL, OPS).
- [ ] All FRs/NFRs use normative keywords (MUST, MUST NOT, SHALL, EXACTLY ONE OF).
- [ ] No forbidden ambiguous terms (should, may, could, might, either, and/or, as needed, approximately, etc.) in normative sections.
- [ ] Normative Option Decision: at least one option framed from a product perspective.
- [ ] Contract Changes: all sections filled or explicitly marked as none.
- [ ] Normative Acceptance Criteria: at least two ACs, each objectively testable.
- [ ] Open clarification markers removed or resolved.
- [ ] `SPEC_PRODUCT_READY: true` set.
- [ ] `Product sign-off: <PO identity>` set.
- [ ] `ADR path` set to the draft ADR file path.
- [ ] `ADR status: draft` set.

## ADR Product Context Layer completeness
- [ ] Business Objective and Requirement Summary populated.
- [ ] Decision Drivers populated (at least two drivers).
- [ ] `ADR product context sign-off: <PO identity>` set in ADR metadata.

## ADR Technical Decision Layer (agent-generated)
- [ ] Agent draft block quote notice present at top of Technical Decision Layer.
- [ ] At least two options enumerated with pros/cons grounded in codebase context.
- [ ] Recommended option labeled as agent recommendation.
- [ ] At least one Mermaid diagram with caption explaining type choice.
- [ ] `ADR technical decision sign-off: pending` (not yet given — awaits architect review).

## Gate check
- [ ] `make quality-sdd-check` passes without violations.
