# Work Item Context Pack

## Context Snapshot
- Work item: `specs/2026-05-12-issue-272-273-v110-docs-hotfix`
- Track: blueprint
- SPEC_READY: true
- ADR path: `docs/blueprint/architecture/decisions/ADR-issue-272-273-v110-docs-hotfix.md`
- ADR status: approved

## Scope Summary
Two v1.10.0 regressions in `scripts/lib/docs/site.sh`:
- **#272** — `--ignore-workspace` removed from three pnpm invocations; consumers with root `pnpm-workspace.yaml` that excludes `docs/` get empty `docs/node_modules/` and a `docusaurus: not found` error on `make docs-build`.
- **#273** — New strict pnpm version assertion emits an opaque error that does not name the root `package.json` `packageManager` field or the CI corepack prepare pin as possible mismatch sources.

Both fixes are single-line or single-block changes to `scripts/lib/docs/site.sh`. No new Make targets, no new scripts, no contract changes.

## Guardrail Controls
- Applicable control IDs: SDD-C-001, SDD-C-002, SDD-C-003, SDD-C-004, SDD-C-005, SDD-C-006, SDD-C-008, SDD-C-009, SDD-C-010, SDD-C-011, SDD-C-012, SDD-C-016, SDD-C-017, SDD-C-019, SDD-C-020, SDD-C-021, SDD-C-024

## Key Files
- `scripts/lib/docs/site.sh` — the only implementation file changed
- `tests/infra/test_docs_site_sh_issue_272_273.py` — regression test file (6 tests: 3 × Issue272PnpmIgnoreWorkspaceTests, 3 × Issue273PnpmVersionErrorMessageTests)
- `docs/platform/consumer/troubleshooting.md` — add v1.10.0 docs build section

## Required Commands
- `uv run python3 -m pytest tests/infra/ -k "issue_272 or issue_273" -v`
- `make docs-build && make docs-smoke`
- `make quality-hooks-fast`
- `make quality-sdd-check`
- `make quality-hooks-run`
- `make quality-hardening-review`
- `make infra-validate`

## Artifact Index
- `architecture.md`
- `spec.md`
- `plan.md`
- `tasks.md`
- `traceability.md`
- `graph.json`
- `evidence_manifest.json`
- `pr_context.md`
- `hardening_review.md`
