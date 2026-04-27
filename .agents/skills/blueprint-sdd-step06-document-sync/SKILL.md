---
name: blueprint-sdd-step06-document-sync
description: Execute SDD Step 7 — update blueprint and consumer docs for changed behavior, sync bootstrap template mirrors, update skill runbooks, and validate docs build/smoke checks. Renamed from blueprint-sdd-document-sync.
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
   python3 scripts/lib/docs/sync_blueprint_template_docs.py
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
python3 scripts/lib/docs/sync_blueprint_template_docs.py
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
