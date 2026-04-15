---
name: blueprint-sdd-clarification-gate
description: Run a deterministic clarification gate over draft SDD specs, block ambiguous normative language, and emit a prioritized list of required clarifications before implementation.
---

# Blueprint SDD Clarification Gate

## When to Use
Use this skill after initial `Discover`/`Specify` drafting and before plan finalization or implementation approval.

## Guardrails
1. Treat ambiguity as blocking.
2. Do not invent missing business/non-functional requirements.
3. Keep `SPEC_READY=false` while blockers exist.
4. Require explicit status `BLOCKED_MISSING_INPUTS` when clarification is pending.
5. Enforce normative wording policy from `AGENTS.md`.

## Workflow
1. Inspect candidate specs under `specs/<YYYY-MM-DD>-*/spec.md`.
2. Check readiness fields and unresolved counters.
3. Scan normative sections for forbidden ambiguity markers.
4. Validate required sign-off sections are present and explicit.
5. Produce blocking clarification questions grouped by category.
6. Update each spec readiness state:
   - blockers present -> `SPEC_READY=false`
   - zero blockers + explicit approvals -> eligible for `SPEC_READY=true`

## Useful Commands
```bash
make quality-sdd-check
rg -n "should|may|could|might|either|and/or|as needed|approximately|etc\." specs/*/spec.md
```

## Required Report Format
Return:
1. Specs inspected.
2. Blocking issues per spec.
3. Clarification questions (Product/Architecture/Security/Operations).
4. Readiness outcome per spec (`SPEC_READY=false|true`).
5. Next action owner and sequence.

## References
- Clarification categories: `references/clarification_categories.md`
