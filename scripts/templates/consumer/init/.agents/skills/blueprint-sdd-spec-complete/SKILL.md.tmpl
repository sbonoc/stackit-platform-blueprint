---
name: blueprint-sdd-spec-complete
description: Guide the Architect or CTO through the spec completion phase — review and finalise the agent-drafted ADR, write architecture.md, complete plan.md and tasks.md, give technical sign-offs, and flip SPEC_READY=true to unlock implementation.
---

# Blueprint SDD Spec Complete

## When to Use
Use this skill after the spec intake PR has merged (`SPEC_PRODUCT_READY=true`,
`Product sign-off` approved, ADR draft present). This skill owns the transition from
intake phase to implementation-ready (`SPEC_READY=true`).

## Actor
Architect or CTO. This is the technical counterpart to `/blueprint-sdd-po-spec`.

## What This Phase Produces
- ADR Technical Decision Layer validated and finalised (agent draft notice removed).
- `architecture.md` written with bounded-context decisions and integration edges.
- `plan.md` written with concrete delivery slices, validation strategy, and app
  onboarding contract.
- `tasks.md` written with gate checks, implementation tasks, test automation, and
  publish tasks.
- All required sign-offs approved: `Architecture`, `Security`, `Operations`.
- `ADR technical decision sign-off` given — confirms or overrides agent recommendation.
- `ADR status` set to `approved` in the ADR file and in spec.md.
- `SPEC_READY: true` set.
- `make quality-sdd-check` passes without violations.

## Workflow

```
1. Checkout the spec branch from the merged intake PR.
2. Review ADR Technical Decision Layer:
   a. Validate or override the recommended option — document rationale if overriding.
   b. Validate Mermaid diagrams — correct type, accurate component names.
   c. Remove the agent draft block quote notice.
   d. Set ADR metadata: ADR technical decision sign-off: approved
   e. Set ADR Status: approved
3. Write architecture.md:
   - Bounded-context decisions, module boundaries, integration edges.
   - Technology-specific architecture shape.
   - Reference the ADR for the option decision rationale.
4. Write plan.md:
   - Concrete delivery slices (not placeholder names).
   - Validation strategy per slice (lowest valid test layer first).
   - App onboarding contract (full explicit make-target list or no-impact statement).
   - Risk and mitigation per slice.
5. Write tasks.md:
   - Gate checks G-001–G-005 filled in.
   - Implementation tasks T-001–T-NNN mapped to delivery slices.
   - Test automation tasks T-1NN.
   - Validation tasks T-2NN.
   - Publish tasks P-001, P-002, P-003.
6. Coordinate remaining sign-offs:
   - Security sign-off: approved (self or delegate)
   - Operations sign-off: approved (self or delegate)
7. Update spec.md:
   - Architecture sign-off: approved
   - Security sign-off: approved
   - Operations sign-off: approved
   - ADR status: approved
   - SPEC_READY: true
8. make quality-sdd-check   # must pass before PR
9. Open spec completion PR.
```

## ADR Review Decision Points
When reviewing the agent's recommended option, apply one of:
- **Confirm**: remove draft notice, keep recommended option, sign off.
- **Adjust**: correct option analysis or consequences, keep option, document adjustment
  rationale alongside the sign-off.
- **Override**: select a different option, document the override rationale, sign off.

Never silently accept the agent draft — the sign-off is the evidence of deliberate review.

## Guardrails
1. MUST NOT set `SPEC_READY: true` while any required sign-off field is not approved.
2. MUST NOT leave the agent draft block quote notice in the ADR after signing off.
3. `plan.md` MUST list the full explicit make-target list for app onboarding contract
   (or explicit `no-impact` declaration) — `quality-sdd-check` enforces this.
4. `tasks.md` MUST have P-001, P-002, P-003 marked `[ ]` (not pre-checked) — they
   are checked as the work progresses.
5. Run `make quality-sdd-check` before opening the spec completion PR.
6. If the agent's recommended option is technically unsound, override and document —
   do not accept a wrong recommendation to avoid friction.

## Useful Commands
```bash
make quality-sdd-check
make quality-sdd-check-all
```

## Required Report Format
Return:
1. ADR review decision (confirm / adjust / override) with rationale.
2. Mermaid diagram validation result — type correct, components accurate.
3. `architecture.md` completeness summary.
4. `plan.md` delivery slices listed.
5. `tasks.md` gate checks listed.
6. Sign-off status for all four roles.
7. `make quality-sdd-check` result.
8. Spec completion PR readiness statement.

## References
- Spec completion checklist: `references/spec_complete_checklist.md`
