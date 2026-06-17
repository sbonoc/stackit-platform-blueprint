---
id: pr-context-2026-06-17-issue-363
artifact_kind: spec
work_item_slug: 2026-06-17-issue-363-broken-adr-links-consumer-docs
owner_team: "@sbonoc/factory-governance"
schema_version: 1.0.0
---

# PR Context — issue #363: broken local ADR links in consumer factory governance docs

## Summary

- Work item: issue #363 — broken local ADR links in consumer factory governance docs
- Objective: remove 29 broken `[text](../architecture/decisions/ADR-*.md)` hyperlinks from four consumer-shipped factory governance docs so `make quality-docs-lint` passes in consumer repos upgraded to blueprint v1.12.0+.
- Scope boundaries: docs-only; no runtime, no schema, no API. Link text preserved; bootstrap template mirror updated in same commit.

## Requirement Coverage

| Requirement | Implementation path | Test evidence |
|---|---|---|
| FR-001 (remove 29 broken hyperlinks, preserve text) | Edit four source docs | AC-001 grep + AC-002 lint |
| FR-002 (sync bootstrap template mirror) | `sync_blueprint_template_docs.py` | AC-003 --check |

Acceptance criteria: AC-001, AC-002, AC-003, AC-004.

## Key Reviewer Files

- Primary files to review first: `docs/blueprint/autonomous-factory/instrumentation-plan.md` (11 links — largest changeset)
- `docs/blueprint/autonomous-factory/design-contracts.md` (4 links)
- `docs/blueprint/autonomous-factory/pre-factory-baselines.md` (4 links)
- `docs/blueprint/autonomous-factory/triage-decomposition-data-feed.md` (7 links, 3 inside table cells)
- `scripts/templates/blueprint/bootstrap/docs/blueprint/autonomous-factory/` — bootstrap template mirror (4 files)

## Validation Evidence

_Filled at step05 after edits land._

## Risk and Rollback

- Main risks: none — docs-only, no runtime path affected.
- Rollback strategy: `git revert <sha>`. No data migration. Consumer repos inherit fix on next `make blueprint-upgrade-consumer`.

## Deferred Proposals

- lint guard to prevent future broken-link regressions (new `lint_docs.py` check rejecting `../architecture/decisions/ADR-*.md` links inside consumer-shipped docs): deferred — no current requester, low urgency.
