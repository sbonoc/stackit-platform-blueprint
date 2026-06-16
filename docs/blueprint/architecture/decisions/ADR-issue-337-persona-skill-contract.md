# ADR: Persona / Skill Contract

**Status:** approved
**Date:** 2026-05-29
**Issue:** #337
**Spec:** `specs/2026-05-28-issue-337-factory-phase-0-foundations/` (FR-002)
**Meta-ADR:** [`ADR-issue-337-factory-phase-0-foundations.md`](ADR-issue-337-factory-phase-0-foundations.md)
**Extensibility classification (#339 C8 FR-017):** `sealed`.
**Amended-by:** [`ADR-issue-364-expert-persona-model.md`](ADR-issue-364-expert-persona-model.md) — the persona-as-actor framing in this ADR is replaced by the three-layer model (SDD step / skill / expert persona); SDD steps are the sealed actor of record, skills are procedural verbs bound to steps by the dispatch matrix, and `PERSONA.md` files are standing review lenses dispatched onto step boundaries (no 1:1 persona↔skill coupling). The SoD invariant (no AI persona maps 1:1 to a human canonical sign-off role) is preserved; ADR-issue-364 strengthens it by making the expert-panel layer compositional rather than identity-based.

## Context

The blueprint already ships skill runbooks under `.agents/skills/<name>/SKILL.md` (executable verbs) and is about to ship personas under `.agents/personas/` (actors with judgment, owned by #333). Without an explicit contract pinning the relationship between the two — and pinning that no AI persona may map 1:1 to a human canonical sign-off role — the factory could silently introduce an "AI architect" or "AI security reviewer" persona that approves its own work, breaking the multi-author SoD rule from `AGENTS.md § Sign-off Policy` and #339 NFR-SEC-001.

## Decision Drivers

- Keep the cognitive split clear: skills are runbooks (deterministic-ish verbs), personas are actors that exercise judgment.
- Prevent persona-on-persona invocation chains that would obscure attribution in the #339 Contract C7 lifecycle event stream (`persona` field).
- Hard-block any factory pattern that would shift human sign-off authority onto AI.
- Keep the contract small enough to enforce mechanically — every clause MUST be checkable by a reviewer in seconds without parsing runtime logs.

## Decision

The persona / skill contract is:

1. **Skills are verbs.** Each skill is a runbook — a sequence of well-defined steps with explicit inputs, guardrails, and exit criteria. Skills live at `.agents/skills/<name>/SKILL.md`.
2. **Personas are nouns.** Each persona is an actor with judgment — a profile that selects skills, weighs trade-offs, and writes artefacts. Personas live at `.agents/personas/<name>.md` (blueprint-namespace) or `.agents/personas/consumer/<name>.md` (consumer-namespace per #339 FR-018).
3. **Personas invoke skills; skills do not invoke other skills.** Cross-skill composition is a persona responsibility. A skill runbook MUST NOT contain a directive that triggers another skill — composition happens at the persona layer, where it is attributable in the C7 event stream.
4. **No AI persona maps 1:1 to a human canonical sign-off role.** The four canonical sign-off phrases (`SPEC_PRODUCT_READY: approved`, `ARCHITECTURE_SIGNOFF: approved`, `SECURITY_SIGNOFF: approved`, `OPERATIONS_SIGNOFF: approved`) MUST be granted by humans only, per `AGENTS.md § Sign-off Policy`. No persona file may carry a name, role description, or activation trigger that implies sign-off authority for Product / Architecture / Security / Operations.

## Options Considered

### Option A — Skills-as-verbs, personas-as-nouns, no 1:1 AI ↔ sign-off mapping (chosen)

The split above.

**Pros:** clean attribution in C7 events (each event names a persona that exercised judgment); no silent skill-on-skill chains; sign-off authority remains anchored to humans; consumer extensions inherit the same shape.

**Cons:** persona authors must write explicit composition code rather than chaining skills. Mitigation: composition is small and inspectable; the cost is trivial.

### Option B — Skills can invoke other skills (rejected)

Allow `.agents/skills/foo/SKILL.md` to directive-invoke `.agents/skills/bar/SKILL.md`.

**Rejected:** breaks C7 attribution (the lifecycle event for `bar` would carry the calling skill's persona, not bar's own judgment source); turns the skill layer into ad-hoc programming language; reviewers cannot quickly see all skills a persona will trigger.

### Option C — Allow AI personas with sign-off authority (rejected)

Define an `architect-ai` persona that grants `ARCHITECTURE_SIGNOFF: approved`.

**Rejected:** directly violates `AGENTS.md § Sign-off Policy` (code assistants MUST NOT self-approve); removes the human-attestation guarantee from the SoD model; would invalidate every downstream compliance argument that rests on multi-author human review.

## Consequences

- Phase 1 ticket #333 (Personas + Skills) authors persona files under `.agents/personas/<name>.md` and cites this ADR for the persona/skill split.
- `.agents/personas/consumer/.gitkeep` (FR-018) is in place so the namespaced consumer-extension convention is discoverable from day one.
- The factory's lifecycle event stream (#339 C7 `persona` field) cleanly identifies which actor produced each transition; chain-of-judgment is auditable.
- No persona file authored after this ADR may carry a sign-off-role name — review of #333's persona PRs MUST reject any persona that does.
- Consumer instances inherit this contract identically (`sealed`); shadowing this rule is not a permitted extension under #339 C8.

## References

- Spec: `specs/2026-05-28-issue-337-factory-phase-0-foundations/spec.md` § FR-002
- Meta-ADR: [`ADR-issue-337-factory-phase-0-foundations.md`](ADR-issue-337-factory-phase-0-foundations.md)
- `AGENTS.md § Sign-off Policy` and § Sign-off Phrases (Deterministic)
- Design contracts: `docs/blueprint/autonomous-factory/design-contracts.md` § Contract C3 (OpenHands ↔ persona mapping), § Contract C5 (Factory Bot Identity + SoD Detection)
- Phase 1 implementer: #333 (Personas + Skills)
