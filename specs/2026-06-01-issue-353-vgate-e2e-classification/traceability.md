# Traceability Matrix

## Requirement-to-Delivery Mapping

| Requirement ID | Control IDs | WCAG SC | Design Element | Implementation Path(s) | Test Evidence | Documentation Evidence | Operational Evidence |
|---|---|---|---|---|---|---|---|
| FR-001 | SDD-C-006 | — | Four new Implementation Stack Profile fields in spec.md (including `E2E automation escalation`) | `.spec-kit/templates/blueprint/spec.md`, `.spec-kit/templates/consumer/spec.md` | T-110, T-111 | FR-001 text in spec.md | — |
| FR-002 | SDD-C-016, SDD-C-024 | — | `_check_vgate_classification` function | `scripts/bin/quality/check_sdd_assets.py` | T-101, T-102 | architecture.md flowchart | `make quality-sdd-check` output |
| FR-003 | SDD-C-024 | — | `automation_target` date validation in `_check_vgate_classification` | `scripts/bin/quality/check_sdd_assets.py` | T-103, T-104, T-105 | NFR-SEC-001 in spec.md | — |
| FR-004 | SDD-C-005 | — | `_VGATE_GATE_SINCE` forward-only guard | `scripts/bin/quality/check_sdd_assets.py` | T-106 | FR-004 text in spec.md | — |
| FR-005 | SDD-C-008 | — | Wired into `_validate_work_item_specs` | `scripts/bin/quality/check_sdd_assets.py` | T-101..T-109 | — | `make quality-sdd-check` |
| FR-006 | SDD-C-006 | — | Template field seeding (4 fields + definition comments) | `.spec-kit/templates/blueprint/spec.md`, `.spec-kit/templates/consumer/spec.md`, consumer init tmpl | T-110, T-111 | — | — |
| FR-007 | SDD-C-011 | — | Playwright mandatory artifact rule with three MUSTs | `AGENTS.md`, `docs/blueprint/governance/spec_driven_development.md`, bootstrap mirror, `.agents/skills/blueprint-sdd-step05-implement/SKILL.md` | T-112 | AGENTS.md testing section + governance doc | — |
| FR-008 | SDD-C-010 | — | Metric emission to stderr | `scripts/bin/quality/check_sdd_assets.py` | T-109 | NFR-OBS-001 in spec.md | stderr in CI |
| NFR-SEC-001 | SDD-C-009 | — | Date field validation via regex; no network calls | `scripts/bin/quality/check_sdd_assets.py` | T-104, T-105 | NFR-SEC-001 text | — |
| NFR-OBS-001 | SDD-C-010 | — | Violation messages include slug + field + value | `scripts/bin/quality/check_sdd_assets.py` | T-109 | NFR-OBS-001 text | stderr |
| NFR-REL-001 | SDD-C-012 | — | Pure function, no side effects | `scripts/bin/quality/check_sdd_assets.py` | T-101..T-108 | NFR-REL-001 text | — |
| NFR-OPS-001 | SDD-C-012 | — | Exception-safe field parsing | `scripts/bin/quality/check_sdd_assets.py` | T-101..T-109 | NFR-OPS-001 text | — |
| AC-001 | SDD-C-024 | — | `_check_vgate_classification` rejects manual for user-facing+playwright | `scripts/bin/quality/check_sdd_assets.py` | T-101 | AC-001 in spec.md | — |
| AC-002 | SDD-C-024 | — | `_check_vgate_classification` passes for automated | `scripts/bin/quality/check_sdd_assets.py` | T-102 | AC-002 in spec.md | — |
| AC-003 | SDD-C-024 | — | Passes for manual-with-target + valid date | `scripts/bin/quality/check_sdd_assets.py` | T-103 | AC-003 in spec.md | — |
| AC-004 | SDD-C-024 | — | Rejects manual-with-target + absent date | `scripts/bin/quality/check_sdd_assets.py` | T-104 | AC-004 in spec.md | — |
| AC-005 | SDD-C-024 | — | Rejects manual-with-target + malformed date | `scripts/bin/quality/check_sdd_assets.py` | T-105 | AC-005 in spec.md | — |
| AC-006 | SDD-C-024 | — | Pre-gate slugs exempt via forward-only guard | `scripts/bin/quality/check_sdd_assets.py` | T-106 | AC-006 in spec.md | — |
| AC-007 | SDD-C-024 | — | Non-playwright profiles exempt | `scripts/bin/quality/check_sdd_assets.py` | T-107 | AC-007 in spec.md | — |
| AC-008 | SDD-C-024 | — | `has-user-facing-flow: false` exempt | `scripts/bin/quality/check_sdd_assets.py` | T-108 | AC-008 in spec.md | — |
| AC-009 | SDD-C-010 | — | Metric emitted to stderr | `scripts/bin/quality/check_sdd_assets.py` | T-109 | AC-009 in spec.md | — |
| AC-010 | SDD-C-006 | — | Blueprint template seeds three fields | `.spec-kit/templates/blueprint/spec.md` | T-110 | AC-010 in spec.md | — |
| AC-011 | SDD-C-006 | — | Consumer template seeds three fields | `.spec-kit/templates/consumer/spec.md` | T-111 | AC-011 in spec.md | — |
| AC-012 | SDD-C-011 | — | AGENTS.md rule present | `AGENTS.md` | T-112 | AC-012 in spec.md | — |

## Graph Linkage
- Graph file: `graph.json`
- Every `FR-###`, `NFR-*-###`, and `AC-###` listed in this file MUST have a corresponding node in `graph.json`.
- Node IDs referenced:
  - FR-001, FR-002, FR-003, FR-004, FR-005, FR-006, FR-007, FR-008
  - NFR-SEC-001, NFR-OBS-001, NFR-REL-001, NFR-OPS-001
  - AC-001, AC-002, AC-003, AC-004, AC-005, AC-006, AC-007, AC-008, AC-009, AC-010, AC-011, AC-012

## Validation Summary
- Required bundles executed: pending (pre-implementation)
- Result summary: pending
- Documentation validation:
  - `make docs-build`
  - `make docs-smoke`

## Evidence Manifest
- Manifest file: `evidence_manifest.json`
- Context export: `context_pack.md`
- PR context export: `pr_context.md`
- Hardening review export: `hardening_review.md`

## Open Risks and Follow-Ups
- Follow-up 1: Deferred proposals (`automation-target` future-date enforcement, Playwright test existence check, frontend-stack-mismatch heuristic warning, required escalation justification on past-target slugs) tracked in spec.md Potential Deferred Proposals section.
- Follow-up 2: Largest residual risk (R-2 in `architecture.md`) is author silently setting `has-user-facing-flow: false` on a UI-bearing work item. Mitigated by template definition comment, paired-justification rule when `frontend-stack-profile != none`, AGENTS.md rule visibility, and code review. Deferred-proposal heuristic warning is the longer-term machine-side safety net.
