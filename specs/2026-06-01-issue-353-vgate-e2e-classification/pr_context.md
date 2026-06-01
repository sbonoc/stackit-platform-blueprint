# PR Context

## Summary

This work item (issue #353, PR #357) adds machine enforcement of V-gate E2E classification to the blueprint quality gate. Two new fields — `Has user-facing flow` (true/false) and `E2E gate classification` (automated/manual/N/A) — are added to the Implementation Stack Profile in all spec templates. `check_sdd_assets.py` gains `_check_vgate_classification`, a pure function that rejects any post-`2026-06-01` spec that declares `has-user-facing-flow: true` with a playwright-capable test profile unless `E2E gate classification: automated`. The check is wired into `_validate_work_item_specs` so `make quality-sdd-check` enforces it for every work item in the catalog. Shift-left: the step01 intake skill infers `has-user-facing-flow` from issue signals at intake time so authors must consciously override a signal-driven value rather than passively accepting a `false` default. Three mandatory Playwright E2E artifact requirements are added to `AGENTS.md`. Scope: blueprint tooling only — `check_sdd_assets.py`, spec templates, AGENTS.md, governance docs, and skill runbooks. No consumer runtime code changes.

## Requirement Coverage

| ID | Implementation | Test Evidence |
|---|---|---|
| FR-001 | `.spec-kit/templates/blueprint/spec.md`, `.spec-kit/templates/consumer/spec.md` (two new fields seeded with signal-list comments) | T-110, T-111 |
| FR-002 | `check_sdd_assets.py:_check_vgate_classification` | T-101, T-102 |
| FR-004 | `check_sdd_assets.py:_VGATE_GATE_SINCE = "2026-06-01"` | T-106 |
| FR-005 | `check_sdd_assets.py:_validate_work_item_specs` (wiring at line 1691–1699) | T-101..T-109 |
| FR-006 | Both spec templates (fields + inline HTML comments with signal list and allowed-values / gate-violation notes) | T-110, T-111 |
| FR-007 | `AGENTS.md` — mandatory Playwright rule with all three MUST clauses | T-112 |
| FR-008 | `check_sdd_assets.py` — `sdd_vgate_manual_e2e_violation` emitted to stderr in all violation branches | T-109 |
| FR-009 | `.agents/skills/blueprint-sdd-step01-intake/SKILL.md` — inference step, signal list, frontend-stack cross-check, required report line | T-113 |
| NFR-OBS-001 | Violation message includes slug, field, current value, expected value; `[quality-sdd-check]` prefix via standard violation printer | T-109 |
| NFR-REL-001 | Pure function with no mutable state | T-101..T-108 |
| NFR-OPS-001 | Absent fields produce violations; OSError wrapped in caller | T-114 |
| AC-001 | Rejects `manual` when `has-user-facing-flow: true` + playwright | T-101 |
| AC-002 | Passes for `automated` | T-102 |
| AC-006 | Pre-gate slugs exempt | T-106 |
| AC-007 | Non-playwright profiles exempt | T-107 |
| AC-008 | `has-user-facing-flow: false` exempt | T-108 |
| AC-009 | Metric in stderr | T-109 |
| AC-010 | Blueprint template seeds both fields | T-110 |
| AC-011 | Consumer template seeds both fields | T-111 |
| AC-012 | AGENTS.md rule with all four substrings | T-112 |
| AC-013 | Step01 SKILL.md: inference step + 3+ keywords + frontend-stack cross-check + report line | T-113 |
| AC-014 | Absent fields produce violations (not silent defaults) | T-114 |

Contract surfaces changed:
- `make quality-sdd-check` behavior extended (same invocation, new check added, exit code semantics unchanged)
- `blueprint/contract.yaml`: no change
- Spec templates: two new Implementation Stack Profile fields seeded in blueprint and consumer templates; consumer init template mirror synced
- Generated consumer behavior: no runtime change; new spec fields will appear in next `make spec-scaffold` invocation

## Key Reviewer Files

- Primary files to review first:
  - `scripts/bin/quality/check_sdd_assets.py` — core change: `_VGATE_GATE_SINCE`, `_check_vgate_classification` (HTML-comment stripping, both field-form lookups), and wiring in `_validate_work_item_specs`. Review the decision-tree logic and both absent-field violation branches (lines 536–599).
  - `tests/infra/test_sdd_asset_checker.py::TestVgateClassification` — 12 unit tests covering every decision branch including hyphen-form normalization and inline HTML comment stripping.
  - `.agents/skills/blueprint-sdd-step01-intake/SKILL.md` — V-gate inference step in Discover (FR-009); signal list; frontend-stack cross-check in Specify; `V-gate inference result` in Required Report Format.
- `tests/blueprint/test_quality_gating.py::TestVgateTemplateFields` — 14 tests covering template seeding, AGENTS.md rule, step01 SKILL.md.
- `.spec-kit/templates/blueprint/spec.md` and `.spec-kit/templates/consumer/spec.md` — two new fields added to Implementation Stack Profile with signal-list and gate-violation inline comments.
- `AGENTS.md` lines 438–447 — mandatory Playwright E2E artifact rule (three MUST clauses).

## Validation Evidence

```
uv run python3 -m pytest tests/infra/test_sdd_asset_checker.py tests/blueprint/test_quality_gating.py -v
→ 106 passed in 1.37s (all T-101..T-114 + 2 Gap-1 regression tests)

make quality-sdd-check
→ [quality-sdd-check] validated SDD assets, readiness gates, and language policy
→ zero new violations on full catalog

uv run python3 scripts/lib/docs/sync_blueprint_template_docs.py
→ summary: quality-docs-sync-blueprint-template (created=0 updated=0 removed=0 skipped=17)
→ all bootstrap template mirrors already synchronized

make quality-docs-check-changed
→ [test-pyramid] OK — unit 97.82% / integration 1.63% / e2e 0.54% (ratios unchanged)
```

Full test suite (2026-06-01): 1902 passed; 12 pre-existing environment-dependent failures (DNS_ZONE_FQDNS missing, pnpm version mismatch, ESO cluster access, live e2e infra) — none in files touched by this work item.

## Risk and Rollback

- Main risks: R-1 wrong gate-since date (low, guarded by T-106); R-2 author bypasses via false override (residual, mitigated by step01 inference + template signal list); R-3 hyphen-form bypass (resolved in Gap-1 commit)
  - R-1 (Low): `_VGATE_GATE_SINCE` set incorrectly could retroactively flag existing specs. Mitigation: constant is "2026-06-01" (the merge date); AC-006/T-106 covers the guard regression.
  - R-2 (Residual): Author silently sets `has-user-facing-flow: false` for a UI-bearing work item, bypassing all enforcement. Mitigations: step01 intake inference (FR-009) pre-sets `true` from issue signals; signal-list template comment (FR-006); AGENTS.md three-MUSTs rule (FR-007); frontend-stack cross-check (FR-009). Residual risk is low; deferred frontend-stack-mismatch warning is the longer-term machine-side safety net.
  - R-3 (Resolved): Hyphen-form field names bypass the gate — fixed in Gap 1 audit commit `7ed22fb5`.

- Rollback strategy: Revert the commit to `check_sdd_assets.py` (or revert the entire branch). The gate behavior reverts immediately because it is applied at `make quality-sdd-check` invocation time — no migration, no state to clean up. The two new spec template fields are additive (they default to `false`/`N/A` and the checker is forward-only), so rollback does not affect existing specs.

## Deferred Proposals (Not Implemented)

1. **Playwright test existence check** — machine-verify at least one `*.spec.ts` file exists when `has-user-facing-flow: true`. Deferred: naming convention per repo is not standardized; false positives risk for repos creating tests in a separate work item.

2. **Cross-repo V-gate classification audit report** — generate a report of V-gate status for all specs across consumer repos. Deferred: belongs in a dedicated observability work item requiring aggregation infrastructure.

3. **Frontend-stack-mismatch heuristic warning** — non-blocking stderr warning when `frontend-stack-profile != none` and `has-user-facing-flow: false`. Deferred: warning semantics need a separate UX surface; primary risk addressed by step01 inference and template comment.

## Follow-Up

- Pre-existing environment failures (pnpm version mismatch, ESO cluster access) are independent of this work item and tracked separately.
- Deferred proposals above will receive explicit triage outcomes (file-issue / park / reject) before PR is marked ready.
