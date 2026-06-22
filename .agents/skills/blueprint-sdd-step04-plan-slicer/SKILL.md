---
name: blueprint-sdd-step04-plan-slicer
description: Execute SDD Step 5 (optional) — refine the approved plan into dependency-ordered implementation slices with explicit owners, validation strategy per slice, and backlog synchronisation. Skip for straightforward work items where plan.md from Step 1 is sufficient.
blueprint-version: 1.0.0
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

> Quality-hooks usage policy (per-slice vs pre-PR gate, keep-going env, force-full): see AGENTS.md § Quality Hooks — Inner-Loop and Pre-PR Usage.

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
7. TRACEABILITY VERIFICATION — run the blueprint-sdd-traceability-keeper skill
   for this work item. Resolve any blocking gaps.

8. If plan.md was changed (or traceability.md was updated to fix gaps):
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
7. Traceability keeper result (gaps found / clean).

## Useful Commands

```bash
make quality-sdd-check
make quality-hooks-fast
```

## References

- Slice checklist: `references/plan_slice_checklist.md`


## Required Output Schema

The structured payload below is the plan-refinement report the skill returns
to the orchestrator and carries on the `phase: plan-slicer` C7 lifecycle event.

```yaml jsonschema
$schema: "http://json-schema.org/draft-07/schema#"
title: BlueprintSddStep04PlanSlicerOutput
description: Structured plan-refinement report produced at the end of SDD step 04.
type: object
additionalProperties: false
required:
  - ticket_id
  - refinement_needed
  - slices
  - backlog_updates_performed
  - traceability_result
properties:
  ticket_id:
    type: string
  refinement_needed:
    type: boolean
  refinement_rationale:
    type: string
  slices:
    type: array
    items:
      type: object
      additionalProperties: false
      required:
        - id
        - name
        - owner
        - depends_on
        - validation_strategy
      properties:
        id:
          type: string
        name:
          type: string
        owner:
          type: string
        depends_on:
          type: array
          items:
            type: string
        validation_strategy:
          type: string
  backlog_updates_performed:
    type: array
    items:
      type: string
  commit_sha:
    type: string
  critical_risks:
    type: array
    items:
      type: object
      additionalProperties: false
      required:
        - description
        - mitigation
      properties:
        description:
          type: string
        mitigation:
          type: string
  traceability_result:
    type: string
    enum:
      - clean
      - gaps-found
  expert_verdicts:
    type: array
    description: >-
      Per-expert verdict array merged by the orchestrator from the step04
      panel invocations (ADR-issue-364 § 4 dispatches a 4-expert panel at
      step04 in parallel-then-merge mode). Each row is keyed by
      expert_slug per ADR-issue-364 § 6 and is carried on the C7
      outcome_details.expert_verdicts[] field per FR-007.
    items:
      type: object
      additionalProperties: false
      required:
        - verdict
        - findings
      oneOf:
        - required: [expert_slug_blueprint]
        - required: [expert_slug_extension]
      properties:
        expert_slug_blueprint:
          type: string
          description: >-
            Blueprint-baseline expert persona slug (sealed enum from
            ADR-issue-364 § 9; amended only via the `#339` sign-off cycle).
            EXACTLY ONE OF this field OR `expert_slug_extension` MUST be
            populated per row (oneOf above). Legacy flat-`expert_slug`
            tolerance is OUT OF SCOPE of this per-invocation schema (no
            live producer emits the old form post-amendment); historical
            local-cli C7 events that carry flat `expert_slug` are handled
            at the Central Brain (#343) ingest layer via the
            `### after: epic-343-promote` legacy-payload normalization
            entry — not at this per-invocation schema layer (per PR #372
            11th-review Codex P2-2 separation-of-concerns fix).
          enum:
            - product-pragmatist
            - boundary-hawk
            - security-paranoid
            - data-privacy
            - test-quality-sceptic
            - operability-sre
            - documentation-discipline
            - performance-cost-aware
        expert_slug_extension:
          type: string
          description: >-
            Consumer-overlay extension expert persona slug (open string from
            the consumer overlay's allowlist; per design-contracts.md § C7
            F-12 amendment 2026-06-19). EXACTLY ONE OF this field OR
            `expert_slug_blueprint` MUST be populated per row.
        verdict:
          type: string
          enum:
            - pass
            - revise
            - block
        findings:
          type: array
          items:
            type: object
```

## C7 Emission

At the end of this step, emit a C7 lifecycle event. Resolve variable values
from session context: `TICKET_ID` — the GitHub issue number; `SKILL_BASENAME`
— the `name:` value from this SKILL.md frontmatter; `OWNER_TEAM` — the GitHub
team slug owning this repository (e.g. `platform-team`); `WORK_ITEM_SLUG` —
the spec directory basename.

**Autonomous factory path (orchestrator #361):** the orchestrator emits the
C7 event after merging all expert verdicts into `outcome_details.expert_verdicts[]`.
It uses the `--extension-json` flag to attach the compact per-expert summary
(one `ExpertVerdictSummary` row per dispatched expert, per ADR-issue-364 § 9)
and `outcome_details.routing_keys` (per design-contracts § C7). The
orchestrator MUST NOT emit the event before all verdicts are collected and
merged.

**Local-CLI path (human-assisted, `local-cli` emitter):** the operator runs
this step without a panel. The `--extension-json` flag is omitted; the emitted
event will not carry `outcome_details.expert_verdicts[]`. This is expected —
expert-panel attribution is absent from local-CLI step events. If the
operator ran expert consultations manually they MAY author the extension JSON
and pass it via `--extension-json`, but this is not required.

```sh
uv run python3 scripts/bin/sdd/c7_emit.py emit \
  --ticket "$TICKET_ID" \
  --phase "plan-slicer" \
  --skill "$SKILL_BASENAME" \
  --owner-team "$OWNER_TEAM" \
  --slug "$WORK_ITEM_SLUG"
```

Stage and commit the emitted JSONL — this commit is part of the authorized
skill workflow and must land immediately so the audit record is durable:

```sh
git add "artifacts/c7/$WORK_ITEM_SLUG.jsonl"
git diff --cached --quiet || {
  git commit -m "chore($WORK_ITEM_SLUG): emit C7 lifecycle event"
  git push
}
```

Set `BLUEPRINT_SDD_C7_EMIT=0` to suppress; exactly one `c7-emission-opted-out` event is written per work-item slug (subsequent opted-out steps write nothing — the guard above skips the commit in that case).
**The LLM MUST NOT write events directly — invoke the helper only.**
