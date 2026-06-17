---
id: pr-context-2026-06-17-issue-363
artifact_kind: spec
work_item_slug: 2026-06-17-issue-363-broken-adr-links-consumer-docs
owner_team: "@sbonoc/factory-governance"
schema_version: 1.0.0
---

# PR Context — issue #363: broken local ADR links in consumer factory governance docs

## Summary

Removes 32 occurrences of local `../architecture/decisions/ADR-*.md` path references from four consumer-shipped factory governance docs. 29 were `[text](url)` hyperlinks (broken in consumer repos because ADR files are pruned on init); 3 were backtick paths in `design-contracts.md` body text (caught by the AC-001 grep assertion). All link text and backtick identifiers are preserved — only the hyperlink syntax is removed. Bootstrap template mirror updated in the same commit. Also adds a `lint_docs.py` regression guard (new check + 2 tests) so the same class of link cannot be re-introduced without a lint failure.

## Requirement Coverage

| Requirement | Implementation path | Test evidence |
|---|---|---|
| FR-001 — remove broken hyperlinks, preserve text | Edit 4 source docs: `design-contracts.md`, `instrumentation-plan.md`, `pre-factory-baselines.md`, `triage-decomposition-data-feed.md` | AC-001: `grep` returns zero matches; AC-002: `make quality-docs-lint` passes |
| FR-002 — sync bootstrap template mirror | `uv run python3 scripts/lib/docs/sync_blueprint_template_docs.py` | AC-003: `--check` exits 0 |
| AC-004 — `make quality-sdd-check` passes | no code change required | AC-004: exits 0 |
| Regression guard (implemented in-PR) | `lint_docs.py` new check + `tests/docs/test_docs_lint.py` 2 new tests | `test_consumer_pruned_adr_hyperlink_fails_in_autonomous_factory_doc` (red gate); `test_consumer_pruned_adr_backtick_passes_in_autonomous_factory_doc` (false-positive gate) |

## Key Reviewer Files

- Primary files to review first:
  - `docs/blueprint/autonomous-factory/instrumentation-plan.md` — 11 links removed (largest changeset)
  - `scripts/bin/quality/lint_docs.py` — regression guard: new check + constants
- `docs/blueprint/autonomous-factory/design-contracts.md` — 4 hyperlinks + 3 backtick paths converted
- `docs/blueprint/autonomous-factory/pre-factory-baselines.md` — 4 links removed
- `docs/blueprint/autonomous-factory/triage-decomposition-data-feed.md` — 7 links removed (3 inside table cells)
- `tests/docs/test_docs_lint.py` — 2 new test cases for the regression guard

Bootstrap template mirrors (`scripts/templates/blueprint/bootstrap/docs/blueprint/autonomous-factory/`) are auto-synced and do not require separate review.

## Validation Evidence

```
# AC-001: no broken ADR hyperlinks remain
$ grep -rn '../architecture/decisions/ADR' docs/blueprint/autonomous-factory/
(no output) → PASS

# AC-002: docs lint
$ make quality-docs-lint
docs lint passed for 155 markdown files → PASS

# AC-003: template sync check
$ uv run python3 scripts/lib/docs/sync_blueprint_template_docs.py --check
summary: quality-docs-sync-blueprint-template (created=0 updated=0 removed=0 skipped=17) → PASS

# AC-004: SDD check
$ make quality-sdd-check
[quality-sdd-check] validated SDD assets, readiness gates, and language policy → PASS

# Regression guard tests
$ uv run python3 -m pytest tests/docs/test_docs_lint.py -q
11 passed in 1.91s → PASS

# Full quality gate
$ make quality-hooks-fast
===== all checks passed ===== → PASS
```

## Risk and Rollback

- Risk: none — docs-only change + additive lint check. No runtime, no schema, no API surface affected.
- Rollback: `git revert <sha>`. No data migration. Consumer repos inherit the fix on next `make blueprint-upgrade-consumer`.
- Blast radius: 4 markdown source files + 4 bootstrap template mirrors + 1 quality script + 1 test file.

## Deferred Proposals

- None — the lint regression guard was implemented in this PR rather than deferred.
