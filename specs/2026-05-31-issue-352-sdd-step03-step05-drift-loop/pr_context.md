# PR Context

## Summary

Closes the structural loop between SDD step03 (spec authoring) and step05 (implementation) that allowed spec-to-implementation drift to survive automated gates. Step03 is promoted from optional accelerator to **mandatory gate** enforced by `make quality-sdd-check` for `{none, bug-fix, refactor, chore, authorized-deviation}` tracks: the checker reads `artifacts/c7/<slug>.jsonl` and rejects any implementation-ready spec that lacks a `phase=spec-complete` event. Exempt: `upgrade` (automated pipeline, no human sign-off model) and `chore-with-no-specs` (no specs/ dir). A new AC authoring rule is added to step03 SKILL.md and seeded into both scaffold templates — every AC must follow the canonical form `AC-NNN [description] — verified by T-N, which MUST assert <exact condition>.`. Step05 SKILL.md gains four numbered guardrails (spec-value regression tests, union types for spec-enumerated fields, single source of truth for enum constants, mandatory automated rendered-output coverage) and a per-profile examples table (TypeScript / Python / Kotlin / Go). All changes are forward-only: existing work items with slug dates before 2026-06-01 are grandfathered by `_SPEC_COMPLETE_GATE_SINCE`.

## Requirement Coverage

| Requirement | Implementation path | Test evidence |
|---|---|---|
| FR-001 (mandatory gate clause) | `AGENTS.md` § Mandatory Workflow item 14 | `test_quality_gating.py::TestAgentsMandatoryGateStep03` (AC-010) |
| FR-002 (machine enforcement via C7) | `check_sdd_assets.py::_check_step03_complete_event` | `test_sdd_asset_checker.py::TestStep03CompleteEventGate` AC-001, AC-002, AC-005 |
| FR-003 (exempt tracks) | `check_sdd_assets.py` exemption branches | `test_sdd_asset_checker.py::TestStep03CompleteEventGate` AC-003, AC-004 |
| FR-004 (AC authoring rule) | `step03-spec-complete/SKILL.md` § AC Authoring Rule | `test_quality_gating.py::TestStep03SkillAcAuthoringRule` (AC-006) |
| FR-005 (spec-value regression tests) | `step05-implement/SKILL.md` Guardrail 16 | `test_quality_gating.py::TestStep05SkillGuardrails` (AC-007) |
| FR-006 (union types) | `step05-implement/SKILL.md` Guardrail 17 | `test_quality_gating.py::TestStep05SkillGuardrails` (AC-007) |
| FR-007 (SSOT constants) | `step05-implement/SKILL.md` Guardrail 18 | `test_quality_gating.py::TestStep05SkillGuardrails` (AC-007) |
| FR-008 (rendered-output coverage) | `step05-implement/SKILL.md` Guardrail 19 | `test_quality_gating.py::TestStep05SkillGuardrails` (AC-007), `TestStep05SkillVitestEscalation` (AC-009) |
| FR-009 (Playwright escalation) | `step05-implement/SKILL.md` Guardrail 19 body | `test_quality_gating.py::TestStep05SkillVitestEscalation` (AC-009) |
| FR-010 (per-profile table) | `step05-implement/SKILL.md` § Per-profile table | `test_quality_gating.py::TestStep05SkillPerProfileTable` (AC-008) |
| FR-011 (forward-only guard) | `check_sdd_assets.py::_SPEC_COMPLETE_GATE_SINCE = "2026-06-01"` | `test_sdd_asset_checker.py::TestStep03CompleteEventGate` (indirect via AC-001) |
| FR-012 (shift-left AC authoring) | `step01-intake/SKILL.md` Discover step 2 + both scaffold `spec.md` templates | `test_quality_gating.py::TestStep01SkillAcAuthoringGuidance`, `TestScaffoldTemplatesAcPlaceholder` (AC-011) |
| NFR-OBS-001 (metric) | `check_sdd_assets.py` metric print to stderr | `test_sdd_asset_checker.py` AC-002 (violation triggers metric) |
| NFR-SEC-001 | No auth surface; read-only filesystem check | N/A (no attack surface) |
| NFR-REL-001, NFR-OPS-001 | Error handling in `_check_step03_complete_event` (malformed JSONL, OSError) | AC-002 extended coverage |
| NFR-A11Y-001 | N/A — no UI surface | N/A |
| AC-001..AC-011 | See traceability.md for full mapping | 74 tests total; all pass |
| Contract surfaces: | `AGENTS.md`, SKILL.md files (operator contract) | N/A |
| Contract surfaces: | `check_sdd_assets.py` (quality gate contract) | 22 unit/integration tests |
| Contract surfaces: | `spec.md` templates, consumer-init template | Drift test `test_consumer_init_sdd_assets_in_sync` |

## Key Reviewer Files

- Primary files to review first:
  - `scripts/bin/quality/check_sdd_assets.py` — new `_check_step03_complete_event()` + `_SPEC_COMPLETE_GATE_SINCE` constant (machine enforcement of the mandatory gate)
  - `tests/infra/test_sdd_asset_checker.py` — AC-001..AC-005 gate tests (happy path, missing event, upgrade exemption, no-specs exemption, opted-out non-satisfaction)
  - `AGENTS.md` — item 14 added to `§ Mandatory Workflow` (normative policy)
  - `.agents/skills/blueprint-sdd-step03-spec-complete/SKILL.md` — new `## AC Authoring Rule (Normative — FR-004)` section
  - `.agents/skills/blueprint-sdd-step05-implement/SKILL.md` — Guardrails 16-19 + per-profile examples table
  - `tests/blueprint/test_quality_gating.py` — AC-006..AC-011 coverage tests
  - `docs/blueprint/governance/spec_driven_development.md` — AC authoring rule section + step05 guardrails + step03 mandatory gate note
  - `.spec-kit/templates/blueprint/spec.md`, `.spec-kit/templates/consumer/spec.md` — canonical AC placeholder seeded in both templates (FR-012)
- High-risk files:
  - `check_sdd_assets.py` forward-only guard (`_SPEC_COMPLETE_GATE_SINCE`) — string comparison relies on slug date-prefix format; non-date slugs skipped via regex guard

## Validation Evidence

```
uv run python3 -m pytest tests/ --tb=short
  → 1108 passed, 42 subtests passed in 124.98s (pre-push hook)
  → New tests: 22 in test_sdd_asset_checker.py + 19 in test_quality_gating.py

make quality-sdd-check
  → [quality-sdd-check] validated SDD assets, readiness gates, and language policy

make quality-hardening-review
  → [METRIC] name=quality_hardening_review_total value=1 status=success

make quality-docs-check-changed
  → [test-pyramid] OK
  → [METRIC] name=test_pyramid_check value=1 ... status=success

uv run python3 scripts/lib/docs/sync_blueprint_template_docs.py
  → updated: sdd_execution_guide.md, spec_driven_development.md (2 updated, 15 skipped)

uv run python3 scripts/lib/spec_kit/sync_consumer_init_sdd_assets.py
  → updated: spec.md.tmpl (1 updated, 14 skipped)

make quality-hooks-fast
  → all 11 checks passed (quality-spec-pr-ready, infra-contract-test-fast, quality-sdd-check-all, ...)

make quality-spec-pr-ready
  → exit 0 (no violations)
```

## Risk and Rollback

- **Main risk**: Contributors who ran step05 before step03 on a new work item (slug date ≥ 2026-06-01) will receive a `make quality-sdd-check` failure. This is the intended behavior — they must run `/blueprint-sdd-step03-spec-complete` first.
- **Blast radius**: Governance/tooling only. No application code, no data migrations, no schema changes, no Kubernetes manifests.
- **Forward-only guard**: `_SPEC_COMPLETE_GATE_SINCE = "2026-06-01"` ensures pre-existing work items (slug date < 2026-06-01) are not retroactively blocked.
- **Rollback**: Revert `_check_step03_complete_event()` and `_SPEC_COMPLETE_GATE_SINCE` from `check_sdd_assets.py`; remove item 14 from `AGENTS.md § Mandatory Workflow`. No data migration or state cleanup required. Template changes (spec.md AC placeholder) can remain — they do not break any existing workflow.
- **Feature flag**: None — the gate is enabled on merge.

## Deferred Proposals

- Machine-enforced AC format scanner — deferred per ADR D-7. A regex parser in `check_sdd_assets.py` that rejects label-only ACs was considered but deferred; SKILL.md guidance + human review at step03 is adequate for now.
- Metric wiring to alerting — `sdd_step03_missing_spec_complete` stderr emission is sufficient for a pre-merge gate; Grafana/PagerDuty wiring is a low-priority follow-on.
