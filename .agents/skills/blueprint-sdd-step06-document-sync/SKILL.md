---
name: blueprint-sdd-step06-document-sync
description: Execute SDD Step 7 — update blueprint and consumer docs for changed behavior, sync bootstrap template mirrors, update skill runbooks, and validate docs build/smoke checks. Renamed from blueprint-sdd-document-sync.
blueprint-version: 1.0.0
---

# Blueprint SDD Step 06 — Document + Operate

## Step covered

- **Step 7** — Document + Operate

## When to Use

Invoke after implementation is complete and the full test suite passes
(Step 6 complete). Complete all documentation and operational content before
moving to Step 8 (Publish).

## Actor

Software Engineer (invokes agent).

## Governance Context

`AGENTS.md` is the canonical policy source for this skill. Sections that apply in this phase:

- `§ Hardening Review Gate` — operational runbooks and alerting declarations are required inputs for the hardening review that follows; document them here.
- `§ Repository Hygiene` — docs ownership boundaries (blueprint vs. consumer) and bootstrap template mirror sync policy.
- `§ Naming and Operational Conventions` — Make target naming, doc path ownership, and command-reference alignment.

> If `AGENTS.md` changes any of the above sections, update this block to reflect the affected sections.

## Guardrails

1. Update documentation for every behavior or operational contract change.
2. Keep blueprint docs and bootstrap template mirrors synchronized.
3. Run docs build and smoke checks before declaring this step done.
4. Keep diagrams and command references aligned with implementation.
5. Update skill runbooks (`.agents/skills/*/SKILL.md`) when operator-facing
   guidance changes.
6. All commits go to the existing Draft PR branch — no new PR is opened.

## Workflow

```
DOCUMENT
1. Identify changed behavior and affected audiences
   (blueprint maintainer, generated-consumer operator, end user).
2. Update relevant docs:
   - docs/blueprint/** (blueprint maintainer docs)
   - docs/platform/** (generated-consumer docs)
   - docs/blueprint/architecture/decisions/ADR-<slug>.md (if any changes)
3. Update Mermaid diagrams where the implementation changes flow or state.
4. Sync docs to bootstrap template mirrors:
   uv run python3 scripts/lib/docs/sync_blueprint_template_docs.py
5. make quality-docs-check-changed     # must pass

OPERATE
6. Add or update:
   - Runbooks (diagnostics steps, rollback procedure).
   - Alerting ownership declarations.
   - Skill runbooks in .agents/skills/*/SKILL.md (if operator guidance changed).

TRACEABILITY
7. TRACEABILITY VERIFICATION — run the blueprint-sdd-traceability-keeper skill
   for this work item. Resolve any blocking gaps.

COMMIT
8. git add docs/ scripts/templates/ .agents/skills/ [other changed files]
   Include any traceability.md fixes from the previous step.
   git commit -m "docs(<slug>): document behavior changes and sync templates"
   git push
```

## Canonical Commands

```bash
make quality-docs-sync-all
make quality-docs-check-changed
make docs-build
make docs-smoke
uv run python3 scripts/lib/docs/sync_blueprint_template_docs.py
```

## Required Report Format

Return:

1. Docs paths updated (list).
2. Bootstrap template sync result.
3. `quality-docs-check-changed` result.
4. Runbook / operational guidance updates (if any).
5. Skill runbook updates (if any).
6. Commit SHA pushed.
7. Traceability keeper result (gaps found / clean).

## References

- Document phase checklist: `references/document_phase_checklist.md`


## Required Output Schema

The structured payload below is the document-sync report the skill returns to
the orchestrator and carries on the `phase: document-sync` C7 lifecycle event.

```yaml jsonschema
$schema: "http://json-schema.org/draft-07/schema#"
title: BlueprintSddStep06DocumentSyncOutput
description: Structured document-sync report produced at the end of SDD step 06.
type: object
additionalProperties: false
required:
  - ticket_id
  - docs_paths_updated
  - bootstrap_template_sync_result
  - docs_check_result
  - traceability_result
properties:
  ticket_id:
    type: string
  docs_paths_updated:
    type: array
    items:
      type: string
  bootstrap_template_sync_result:
    type: string
    enum:
      - pass
      - fail
      - skipped
  docs_check_result:
    type: string
    enum:
      - pass
      - fail
  runbook_updates:
    type: array
    items:
      type: string
  skill_runbook_updates:
    type: array
    items:
      type: string
  commit_sha:
    type: string
  traceability_result:
    type: string
    enum:
      - clean
      - gaps-found
  expert_verdicts:
    type: array
    description: >-
      Per-expert verdict array merged by the orchestrator from the step06
      panel invocations (ADR-issue-364 § 4 dispatches a 3-expert panel at
      step06 in parallel-then-merge mode). Each row is keyed by
      expert_slug per ADR-issue-364 § 6 and is carried on the C7
      outcome_details.expert_verdicts[] field per FR-007.
    items:
      type: object
      additionalProperties: false
      required:
        - expert_slug
        - verdict
        - findings
      properties:
        expert_slug:
          type: string
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

```sh
uv run python3 scripts/bin/sdd/c7_emit.py emit \
  --ticket "$TICKET_ID" \
  --phase "document-sync" \
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
