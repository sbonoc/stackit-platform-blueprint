# Traceability Matrix

## Requirement-to-Delivery Mapping

| Requirement ID | Control IDs | WCAG SC | Design Element | Implementation Path(s) | Test Evidence | Documentation Evidence | Operational Evidence |
|---|---|---|---|---|---|---|---|
| FR-001 | SDD-C-006 | — | Two new Implementation Stack Profile fields in spec.md (`has-user-facing-flow`, `E2E gate classification`) | `.spec-kit/templates/blueprint/spec.md`, `.spec-kit/templates/consumer/spec.md` | T-110, T-111 | FR-001 text in spec.md | — |
| FR-002 | SDD-C-016, SDD-C-024 | — | `_check_vgate_classification` function; `_parse_bullet_kv` HTML-comment stripping (Codex P1 gap fix — ensures step01-inferred inline-comment values are correctly parsed) | `scripts/bin/quality/check_sdd_assets.py` | T-101, T-102, T-inline-1 (HTML comment + manual), T-inline-2 (HTML comment + automated) | architecture.md flowchart | `make quality-sdd-check` output |
| FR-004 | SDD-C-005 | — | `_VGATE_GATE_SINCE` forward-only guard | `scripts/bin/quality/check_sdd_assets.py` | T-106 | FR-004 text in spec.md | — |
| FR-005 | SDD-C-008 | — | Wired into `_validate_work_item_specs` | `scripts/bin/quality/check_sdd_assets.py` | T-101..T-109 | architecture.md § Application layer | `make quality-sdd-check` |
| FR-006 | SDD-C-006 | — | Template field seeding (2 fields + definition comments) | `.spec-kit/templates/blueprint/spec.md`, `.spec-kit/templates/consumer/spec.md`, consumer init tmpl | T-110, T-111 | — | — |
| FR-007 | SDD-C-011 | — | Playwright mandatory artifact rule with three MUSTs | `AGENTS.md`, `docs/blueprint/governance/spec_driven_development.md`, bootstrap mirror, `.agents/skills/blueprint-sdd-step05-implement/SKILL.md` | T-112 | AGENTS.md testing section + governance doc | — |
| FR-008 | SDD-C-010 | — | Metric emission to stderr | `scripts/bin/quality/check_sdd_assets.py` | T-109 | NFR-OBS-001 in spec.md | stderr in CI |
| FR-009 | SDD-C-011, SDD-C-017 | — | Step01 intake V-gate inference (signal list, frontend-stack cross-check, mandatory report line) | `.agents/skills/blueprint-sdd-step01-intake/SKILL.md` | T-113 | FR-009 text in spec.md | intake report output |
| NFR-OBS-001 | SDD-C-010 | — | Violation messages include slug + field + value | `scripts/bin/quality/check_sdd_assets.py` | T-109 | NFR-OBS-001 text | stderr |
| NFR-REL-001 | SDD-C-012 | — | Pure function, no side effects | `scripts/bin/quality/check_sdd_assets.py` | T-101..T-108 | NFR-REL-001 text | — |
| NFR-OPS-001 | SDD-C-012 | — | Exception-safe field parsing; absent fields produce violations; `_parse_bullet_kv` strips inline HTML comments so step01-inferred values with `<!-- ... -->` are never silently dropped | `scripts/bin/quality/check_sdd_assets.py` | T-101..T-109, T-114, T-inline-1, T-inline-2 | NFR-OPS-001 text | — |
| AC-001 | SDD-C-024 | — | `_check_vgate_classification` rejects manual for user-facing+playwright | `scripts/bin/quality/check_sdd_assets.py` | T-101 | AC-001 in spec.md | — |
| AC-002 | SDD-C-024 | — | `_check_vgate_classification` passes for automated | `scripts/bin/quality/check_sdd_assets.py` | T-102 | AC-002 in spec.md | — |
| AC-006 | SDD-C-024 | — | Pre-gate slugs exempt via forward-only guard | `scripts/bin/quality/check_sdd_assets.py` | T-106 | AC-006 in spec.md | — |
| AC-007 | SDD-C-024 | — | Non-playwright profiles exempt | `scripts/bin/quality/check_sdd_assets.py` | T-107 | AC-007 in spec.md | — |
| AC-008 | SDD-C-024 | — | `has-user-facing-flow: false` exempt | `scripts/bin/quality/check_sdd_assets.py` | T-108 | AC-008 in spec.md | — |
| AC-009 | SDD-C-010 | — | Metric emitted to stderr | `scripts/bin/quality/check_sdd_assets.py` | T-109 | AC-009 in spec.md | — |
| AC-010 | SDD-C-006 | — | Blueprint template seeds two fields with signal-list comments | `.spec-kit/templates/blueprint/spec.md` | T-110 | AC-010 in spec.md | — |
| AC-011 | SDD-C-006 | — | Consumer template seeds two fields with signal-list comments | `.spec-kit/templates/consumer/spec.md` | T-111 | AC-011 in spec.md | — |
| AC-012 | SDD-C-011 | — | AGENTS.md rule present with three MUSTs | `AGENTS.md` | T-112 | AC-012 in spec.md | — |
| AC-013 | SDD-C-011, SDD-C-017 | — | Step01 SKILL.md contains inference step, cross-check, and report line | `.agents/skills/blueprint-sdd-step01-intake/SKILL.md` | T-113 | AC-013 in spec.md | — |
| AC-014 | SDD-C-024, SDD-C-012 | — | Absent V-gate fields produce a violation (covers NFR-OPS-001 + FR-002 absent-value clause) | `scripts/bin/quality/check_sdd_assets.py` | T-114 | AC-014 in spec.md | — |

## Graph Linkage
- Graph file: `graph.json`
- Every `FR-###`, `NFR-*-###`, and `AC-###` listed in this file MUST have a corresponding node in `graph.json`.
- Node IDs referenced:
  - FR-001, FR-002, FR-004, FR-005, FR-006, FR-007, FR-008, FR-009
  - NFR-OBS-001, NFR-REL-001, NFR-OPS-001
  - AC-001, AC-002, AC-006, AC-007, AC-008, AC-009, AC-010, AC-011, AC-012, AC-013, AC-014

## Validation Summary
- Required bundles executed: 2026-06-01
- Result summary: **PASS** — 132/132 targeted tests pass (T-101..T-114, 2 Gap-1 hyphen-form regression tests, 2 Codex-P1 HTML-comment regression tests, 3 Codex-P2 unrecognized-value regression tests, 21 transient-error pattern tests); `make quality-sdd-check` zero new violations; pre-existing environment-dependent failures unrelated to this work item
- Targeted test run: `uv run python3 -m pytest tests/infra/test_sdd_asset_checker.py tests/blueprint/test_quality_gating.py tests/infra/test_audit_version_transient_errors.py -v` → 132 passed in 1.29s
- `make quality-sdd-check` → zero new violations on full catalog
- `make quality-spec-pr-ready` → clean pass (plan.md gates, hardening_review.md proposals, pr_context.md structure all corrected)
- Post-review gap fixes:
  - Gap 1 (hyphen-form field names): `_check_vgate_classification` accepts both `has user-facing flow` and `has-user-facing-flow`; 2 regression tests added
  - Codex P1 (inline HTML comment on inferred values): `_parse_bullet_kv` strips `<!-- ... -->` before returning values; 2 regression tests added (`test_inline_html_comment_on_true_value_is_stripped`, `test_inline_html_comment_on_true_value_passes_when_automated`)
  - Codex P2 (unrecognized has-user-facing-flow values): `_check_vgate_classification` now distinguishes recognized falsy (`_VGATE_FLOW_FALSE_VALUES`) from unrecognized values (typos, placeholders); unrecognized values produce a gate violation; 3 regression tests added
  - CI transient error (quay.io EOF): `is_transient_registry_error` in `audit_version.sh` extended with EOF and connection-timed-out patterns; 21 unit tests added in `test_audit_version_transient_errors.py`
  - Codex review (dead code in transient-error tests): removed `_call_is_transient` (referenced undefined `_q`, latent NameError, never called), `_is_transient`, `_FUNC_EXTRACT`, and unused `subprocess` import
  - Codex review (N/A E2E gate classification test): added `test_na_e2e_classification_for_user_facing_with_playwright_is_violation` covering the named third value (N/A) from FR-001
- Documentation validation:
  - `make docs-build` — blocked by pre-existing pnpm version mismatch (pnpm@11.4.0 active vs @10.32.1 required); pre-existing environment issue, not introduced by this work item
  - `make docs-smoke` — blocked by same pnpm issue

## Evidence Manifest
- Manifest file: `evidence_manifest.json`
- Context export: `context_pack.md`
- PR context export: `pr_context.md`
- Hardening review export: `hardening_review.md`

## Open Risks and Follow-Ups
- Follow-up 1: Deferred proposals (Playwright test existence check, cross-repo V-gate classification audit report, frontend-stack-mismatch heuristic warning) tracked in spec.md Potential Deferred Proposals section.
- Follow-up 2: Largest residual risk (R-2 in `architecture.md`) is author silently setting `has-user-facing-flow: false` on a UI-bearing work item. Primary mitigations: step01 intake inference (FR-009) pre-sets `true` from issue signals; signal-list inline comment in spec template (FR-006) gives manual authors the same checklist; frontend-stack cross-check flags the contradiction; AGENTS.md mandatory Playwright rule (FR-007) surfaces the obligation at implementation time. The deferred frontend-stack-mismatch heuristic warning is the longer-term machine-side safety net.
