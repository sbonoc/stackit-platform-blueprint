---
name: blueprint-sdd-step04-plan-slicer
description: Execute SDD Step 5 (optional) — refine the approved plan into dependency-ordered implementation slices with explicit owners, validation strategy per slice, and backlog synchronisation. Skip for straightforward work items where plan.md from Step 1 is sufficient.
---

# Blueprint SDD Step 04 — Plan Slicer (Optional)

## Step covered

- **Step 5** — Refine implementation plan (optional)

## When to Use

Invoke after `SPEC_READY: true` (Step 4 complete) when the work item is
complex enough that the plan from Step 1 needs refinement into a
dependency-ordered, owner-assigned execution sequence before any code is
written.

**Skip this step** for straightforward work items where `plan.md` from
Step 1 is already clear and actionable — proceed directly to Step 6.

## Actor

Software Engineer (invokes agent).

## Governance Context

`AGENTS.md` is the canonical policy source for this skill. Sections that apply in this phase:

- `§ SDD Artifact Contract` — `plan.md` and `tasks.md` must remain aligned with all artifact path constraints.
- `§ Cross-Cutting Guardrails (Must Be Captured in Discover + Specify)` — app-onboarding Make-target contract and managed-service-first policy must be reflected in plan slices when applicable.
- `§ Definition of Done (DoD)` — each slice must map to SDD artifacts, validation evidence, and a clear owner.

> If `AGENTS.md` changes any of the above sections, update this block to reflect the affected sections.

## Guardrails

1. Slice by bounded context and dependency direction — not by random files.
2. Keep each slice independently verifiable.
3. Preserve ownership boundaries from `blueprint/contract.yaml`.
4. Keep traceability from `REQ-###` to tasks explicit.
5. All commits go to the existing Draft PR branch — no new PR is opened.
6. Update backlog links/status together with plan updates.

## Workflow

```
1. Load the approved spec (SPEC_READY=true) and current plan.md.
2. Derive execution slices with clear inputs/outputs.
3. Assign owner per slice and identify dependency edges.
4. Define validation per slice (lowest valid test layer first).
5. Update plan.md and tasks.md.
6. Synchronize AGENTS.backlog.md with links to the plan/tasks sections.
7. If plan.md was changed:
   git add specs/YYYY-MM-DD-<slug>/plan.md specs/YYYY-MM-DD-<slug>/tasks.md
   git commit -m "feat(<slug>): refine plan into execution slices"
   git push
```

## Required Report Format

Return:

1. Whether refinement was needed (yes/no) and why.
2. Slice list (ordered), with owner and dependency map per slice.
3. Validation strategy per slice.
4. Backlog updates performed.
5. Commit SHA pushed (or "skipped — no changes").
6. Critical risks and mitigations.

## Useful Commands

```bash
make quality-sdd-check
make quality-hooks-fast
```

## References

- Slice checklist: `references/plan_slice_checklist.md`
