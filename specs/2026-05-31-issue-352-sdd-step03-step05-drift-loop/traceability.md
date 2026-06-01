# Traceability Matrix

## Requirement-to-Delivery Mapping

| Requirement ID | Control IDs | WCAG SC | Design Element | Implementation Path(s) | Test Evidence | Documentation Evidence | Operational Evidence |
|---|---|---|---|---|---|---|---|
| FR-001 | SDD-C-020, SDD-C-005 | N/A | ADR D-1 | `AGENTS.md` § Mandatory Workflow | `tests/blueprint/test_quality_gating.py::AC-010` | `AGENTS.md` § Mandatory Workflow + ADR § D-1 | none (text-only) |
| FR-002 | SDD-C-002, SDD-C-019 | N/A | ADR D-1, D-2 | `scripts/bin/quality/check_sdd_assets.py::_check_step03_complete_event` | `tests/infra/test_sdd_asset_checker.py::AC-001`, `::AC-002`, `::AC-005` | ADR § D-1 + plan.md Slice 4 | `[METRIC] name=sdd_step03_missing_spec_complete` in CI logs |
| FR-003 | SDD-C-002 | N/A | ADR D-1 | `scripts/bin/quality/check_sdd_assets.py` (exemption branches) | `tests/infra/test_sdd_asset_checker.py::AC-003`, `::AC-004` | ADR § D-1 (exempt tracks) | none |
| FR-004 | SDD-C-019, SDD-C-005 | N/A | ADR D-3 | `.agents/skills/blueprint-sdd-step03-spec-complete/SKILL.md` | `tests/blueprint/test_quality_gating.py::AC-006` | SKILL.md AC authoring section | none (human-enforced per ADR D-7) |
| FR-005 | SDD-C-008, SDD-C-023 | N/A | ADR D-4 | `.agents/skills/blueprint-sdd-step05-implement/SKILL.md` Guardrails | `tests/blueprint/test_quality_gating.py::AC-007` | SKILL.md Guardrails section | none |
| FR-006 | SDD-C-008 | N/A | ADR D-4 | `.agents/skills/blueprint-sdd-step05-implement/SKILL.md` Guardrails | `tests/blueprint/test_quality_gating.py::AC-007` | SKILL.md Guardrails section | none |
| FR-007 | SDD-C-008 | N/A | ADR D-4 | `.agents/skills/blueprint-sdd-step05-implement/SKILL.md` Guardrails | `tests/blueprint/test_quality_gating.py::AC-007` | SKILL.md Guardrails section | none |
| FR-008 | SDD-C-008 | N/A | ADR D-4 | `.agents/skills/blueprint-sdd-step05-implement/SKILL.md` Guardrails | `tests/blueprint/test_quality_gating.py::AC-007`, `::AC-009` | SKILL.md Guardrails section | none |
| FR-009 | SDD-C-008 | N/A | ADR D-4 | `.agents/skills/blueprint-sdd-step05-implement/SKILL.md` Guardrails (FR-008 body) | `tests/blueprint/test_quality_gating.py::AC-009` | SKILL.md FR-008 guardrail body | none |
| FR-010 | SDD-C-006 | N/A | ADR D-5 | `.agents/skills/blueprint-sdd-step05-implement/SKILL.md` Per-profile examples table | `tests/blueprint/test_quality_gating.py::AC-008` | SKILL.md Per-profile section | none |
| FR-011 | SDD-C-002 | N/A | ADR D-6 | `scripts/bin/quality/check_sdd_assets.py` (merge-date constant) | `tests/infra/test_sdd_asset_checker.py::AC-001` (indirect) | ADR § D-6 | none |
| FR-012 | SDD-C-019, SDD-C-005 | N/A | ADR D-3 | `.agents/skills/blueprint-sdd-step01-intake/SKILL.md`, `.spec-kit/templates/blueprint/spec.md`, `.spec-kit/templates/consumer/spec.md` | `tests/blueprint/test_quality_gating.py::AC-011` | step01 SKILL.md Discover-phase section + scaffold template AC placeholder | none (human-enforced shift-left) |
| FR-013 | SDD-C-002, SDD-C-019 | N/A | ADR D-7 (reversed), Option E | `scripts/bin/quality/check_sdd_assets.py::_check_ac_format` | `tests/infra/test_sdd_asset_checker.py::TestAcFormatScanner` (AC-012) | ADR § D-7 (reversed) + spec.md FR-013 | none |
| FR-014 | SDD-C-019, SDD-C-005 | N/A | ADR D-8 | `.agents/skills/blueprint-sdd-step01-intake/SKILL.md`, `.agents/skills/blueprint-sdd-step07-pr-packager/SKILL.md`, `.spec-kit/templates/blueprint/spec.md`, `.spec-kit/templates/consumer/spec.md` | `tests/blueprint/test_quality_gating.py::TestProposalsShiftLeft` (AC-013) | step01 + step07 SKILL.md + scaffold templates `## Potential Deferred Proposals` section | none (human-enforced shift-left) |
| NFR-SEC-001 | SDD-C-009 | N/A | N/A | N/A | N/A | spec.md NFR-SEC-001 rationale | none |
| NFR-OBS-001 | SDD-C-010 | N/A | ADR D-1 | `scripts/bin/quality/check_sdd_assets.py` (metric emission) | `tests/infra/test_sdd_asset_checker.py::AC-002` | spec.md NFR-OBS-001 | `[METRIC] name=sdd_step03_missing_spec_complete value=1 work_item=<slug>` |
| NFR-REL-001 | SDD-C-012 | N/A | architecture.md § Non-Functional | `scripts/bin/quality/check_sdd_assets.py` (error handling) | `tests/infra/test_sdd_asset_checker.py::AC-002` (extended for malformed JSONL) | spec.md NFR-REL-001 | none |
| NFR-OPS-001 | SDD-C-016 | N/A | architecture.md § Non-Functional | `scripts/bin/quality/check_sdd_assets.py` (composite error message) | `tests/infra/test_sdd_asset_checker.py::AC-002` | spec.md NFR-OPS-001 | none |
| NFR-A11Y-001 | N/A | N/A | N/A | N/A | N/A | spec.md NFR-A11Y-001 rationale (N/A — no UI) | none |
| AC-001 | SDD-C-002, SDD-C-012 | N/A | ADR D-1 | `scripts/bin/quality/check_sdd_assets.py::_check_step03_complete_event` | `tests/infra/test_sdd_asset_checker.py::AC-001` | plan.md Slice 4 | none |
| AC-002 | SDD-C-002, SDD-C-012 | N/A | ADR D-1 | `scripts/bin/quality/check_sdd_assets.py::_check_step03_complete_event` | `tests/infra/test_sdd_asset_checker.py::AC-002` | plan.md Slice 4 | NFR-OBS-001 metric |
| AC-003 | SDD-C-002 | N/A | ADR D-1 | `scripts/bin/quality/check_sdd_assets.py` (upgrade branch) | `tests/infra/test_sdd_asset_checker.py::AC-003` | plan.md Slice 4 | none |
| AC-004 | SDD-C-002 | N/A | ADR D-1 | `scripts/bin/quality/check_sdd_assets.py` (no-specs branch) | `tests/infra/test_sdd_asset_checker.py::AC-004` | plan.md Slice 4 | none |
| AC-005 | SDD-C-002 | N/A | ADR D-1 | `scripts/bin/quality/check_sdd_assets.py` (opt-out filter) | `tests/infra/test_sdd_asset_checker.py::AC-005` | plan.md Slice 4 | none |
| AC-006 | SDD-C-019 | N/A | ADR D-3 | `.agents/skills/blueprint-sdd-step03-spec-complete/SKILL.md` | `tests/blueprint/test_quality_gating.py::AC-006` | SKILL.md AC authoring section | none |
| AC-007 | SDD-C-008 | N/A | ADR D-4 | `.agents/skills/blueprint-sdd-step05-implement/SKILL.md` | `tests/blueprint/test_quality_gating.py::AC-007` | SKILL.md Guardrails section | none |
| AC-008 | SDD-C-006 | N/A | ADR D-5 | `.agents/skills/blueprint-sdd-step05-implement/SKILL.md` | `tests/blueprint/test_quality_gating.py::AC-008` | SKILL.md Per-profile section | none |
| AC-009 | SDD-C-008 | N/A | ADR D-4 | `.agents/skills/blueprint-sdd-step05-implement/SKILL.md` | `tests/blueprint/test_quality_gating.py::AC-009` | SKILL.md FR-008 guardrail body | none |
| AC-010 | SDD-C-020 | N/A | ADR D-1 | `AGENTS.md` § Mandatory Workflow | `tests/blueprint/test_quality_gating.py::AC-010` | AGENTS.md § Mandatory Workflow | none |
| AC-011 | SDD-C-019, SDD-C-005 | N/A | ADR D-3 | `.agents/skills/blueprint-sdd-step01-intake/SKILL.md`, `.spec-kit/templates/blueprint/spec.md`, `.spec-kit/templates/consumer/spec.md` | `tests/blueprint/test_quality_gating.py::AC-011` | step01 SKILL.md Discover-phase section + scaffold template AC placeholder | none |
| AC-012 | SDD-C-002, SDD-C-019 | N/A | ADR D-7 (reversed) | `scripts/bin/quality/check_sdd_assets.py::_check_ac_format` | `tests/infra/test_sdd_asset_checker.py::TestAcFormatScanner::test_label_only_ac_produces_violation` | ADR § D-7 + spec.md AC-012 | none |
| AC-013 | SDD-C-019, SDD-C-005 | N/A | ADR D-8 | `.agents/skills/blueprint-sdd-step01-intake/SKILL.md`, `.agents/skills/blueprint-sdd-step07-pr-packager/SKILL.md`, `.spec-kit/templates/blueprint/spec.md`, `.spec-kit/templates/consumer/spec.md` | `tests/blueprint/test_quality_gating.py::TestProposalsShiftLeft` | step01 + step07 SKILL.md + scaffold templates | none |

## Graph Linkage
- Graph file: `graph.json`
- Every `FR-###`, `NFR-*-###`, and `AC-###` listed in this file MUST have a corresponding node in `graph.json`.
- Node IDs referenced:
  - FR-001, FR-002, FR-003, FR-004, FR-005, FR-006, FR-007, FR-008, FR-009, FR-010, FR-011, FR-012, FR-013, FR-014
  - NFR-SEC-001, NFR-OBS-001, NFR-REL-001, NFR-OPS-001, NFR-A11Y-001
  - AC-001, AC-002, AC-003, AC-004, AC-005, AC-006, AC-007, AC-008, AC-009, AC-010, AC-011, AC-012, AC-013

## Validation Summary
- Required bundles executed: `make quality-sdd-check`, `make quality-hooks-fast`, `make docs-build`, `make docs-smoke`, `make quality-hardening-review`
- Result summary: populated at Step 6 (Implement) and Step 7 (Document) — pending implementation.
- Documentation validation:
  - `make docs-build`
  - `make docs-smoke`

## Evidence Manifest
- Manifest file: `evidence_manifest.json`
- Context export: `context_pack.md`
- PR context export: `pr_context.md`
- Hardening review export: `hardening_review.md`

## Open Risks and Follow-Ups
- Follow-up 1 (closed): ADR D-7 revisit clause was triggered in this same PR — `_check_ac_format` implemented as FR-013; no separate chore needed.
- Follow-up 2: When a new `Implementation Stack Profile` is introduced, the per-profile examples table in step05 SKILL.md MUST be updated in the same commit (documented in ADR § Consequences).
