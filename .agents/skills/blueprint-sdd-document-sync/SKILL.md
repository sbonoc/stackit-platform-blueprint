---
name: blueprint-sdd-document-sync
description: Execute the SDD Document phase with deterministic docs updates, template sync checks, and docs-site validation for blueprint and consumer tracks.
---

# Blueprint SDD Document Sync

## When to Use
Use this skill after implementation/verification to complete the `Document` phase before review/merge.

## Guardrails
1. Update documentation for every behavior or operational contract change.
2. Keep blueprint docs and bootstrap template mirrors synchronized.
3. Run docs build/smoke checks before declaring done.
4. Keep diagrams and command references aligned with implementation.

## Workflow
1. Identify changed behavior and affected audiences (maintainer, consumer, operator).
2. Update relevant docs (`docs/blueprint/**`, `docs/platform/**`).
3. Sync generated docs artifacts and template mirrors.
4. Validate docs build and smoke checks.
5. Record evidence paths in work-item traceability.

## Canonical Commands
```bash
make quality-docs-sync-all
make quality-docs-check-changed
make docs-build
make docs-smoke
```

## Required Report Format
Return:
1. Docs paths updated.
2. Sync/check/build/smoke command results.
3. Any remaining docs drift or TODO blockers.
4. Final doc-phase readiness statement.

## References
- Document phase checklist: `references/document_phase_checklist.md`
