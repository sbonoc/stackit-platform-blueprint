# Traceability Matrix

## Requirement-to-Delivery Mapping

| Requirement ID | Control IDs | WCAG SC | Design Element | Implementation Path(s) | Test Evidence | Documentation Evidence | Operational Evidence |
|---|---|---|---|---|---|---|---|
| FR-001 | SDD-C-001, SDD-C-002 | N/A | YAML-aware merge path in `_apply_entries` | `scripts/lib/blueprint/upgrade_consumer.py::_apply_entries` | T-101, T-106 | ADR-issue-346-upgrade-precommit-clobber.md | `upgrade_summary.md` Preserved Consumer Hooks section |
| FR-002 | SDD-C-001, SDD-C-002 | N/A | `_yaml_merge_precommit_hooks` function | `scripts/lib/blueprint/upgrade_consumer.py::_yaml_merge_precommit_hooks` | T-101, T-102 | ADR § Decision | `upgrade_summary.md` |
| FR-003 | SDD-C-001 | N/A | Hook-order preservation in `_yaml_merge_precommit_hooks` | `scripts/lib/blueprint/upgrade_consumer.py::_yaml_merge_precommit_hooks` | T-103 | ADR § Consequences | `upgrade_summary.md` |
| FR-004 | SDD-C-003, SDD-C-004 | N/A | `PrecommitYamlParseError` fallback to `_three_way_merge` | `scripts/lib/blueprint/upgrade_consumer.py::_apply_entries` | T-104 | ADR § Decision | stderr WARNING log |
| FR-005 | SDD-C-001 | N/A | `_classify_entries` produces `merge-required` for diverged consumer file | `scripts/lib/blueprint/upgrade_consumer.py::_classify_entries` | T-106 | spec.md § FR-005 | `upgrade_plan.json` |
| FR-006 | SDD-C-009 | N/A | `_write_summary` Preserved Consumer Hooks section | `scripts/lib/blueprint/upgrade_consumer.py::_write_summary` | T-108 | ADR § Consequences | `upgrade_summary.md` |
| FR-007 | SDD-C-001, SDD-C-011 | N/A | `quality-validate-bootstrap-template-drift` hook unchanged | `.pre-commit-config.yaml` (blueprint source) | Existing drift-check gate | governance/quality_hooks.md | pre-commit hook output |
| FR-008 | SDD-C-005, SDD-C-007 | N/A | Fixture-based unit tests | `tests/blueprint/test_upgrade_precommit_merge.py` | T-101–T-108 | spec.md § FR-008 | CI test run |
| NFR-SEC-001 | SDD-C-009 | N/A | `yaml.safe_load` only; no `eval`; no shell exec of hook entries | `_yaml_merge_precommit_hooks` | T-101 (positive-path), T-104 (parse error) | ADR § Alternatives | N/A |
| NFR-OBS-001 | SDD-C-013 | N/A | log_info per preserved hook; WARNING on parse fallback | `_apply_entries` intercept + `_yaml_merge_precommit_hooks` | T-104 (WARNING path) | spec.md § NFR-OBS-001 | stderr/stdout during `make blueprint-upgrade-consumer` |
| NFR-REL-001 | SDD-C-011 | N/A | Idempotency: no duplicate hook insertion | `_yaml_merge_precommit_hooks` duplicate-id guard | T-105, T-107 | plan.md § Risks | N/A |
| NFR-OPS-001 | SDD-C-014 | N/A | "Preserved Consumer Hooks" section in `upgrade_summary.md` | `_write_summary` | T-108 | spec.md § NFR-OPS-001 | `upgrade_summary.md` |
| NFR-A11Y-001 | N/A | N/A | N/A — no user-facing UI | N/A | T-A01 (N/A) | spec.md § NFR-A11Y-001 | N/A |
| AC-001 | SDD-C-001 | N/A | Consumer hook preserved | `_yaml_merge_precommit_hooks` | T-101 | spec.md § AC-001 | `upgrade_summary.md` |
| AC-002 | SDD-C-001 | N/A | Append position after last blueprint hook | `_yaml_merge_precommit_hooks` | T-102 | spec.md § AC-002 | `upgrade_summary.md` |
| AC-003 | SDD-C-001 | N/A | Multiple hooks preserved in order | `_yaml_merge_precommit_hooks` | T-103 | spec.md § AC-003 | `upgrade_summary.md` |
| AC-004 | SDD-C-003 | N/A | YAML parse error → `PrecommitYamlParseError` → fallback | `_apply_entries` | T-104 | spec.md § AC-004 | stderr WARNING |
| AC-005 | SDD-C-011 | N/A | Idempotency | `_yaml_merge_precommit_hooks` | T-105 | spec.md § AC-005 | N/A |
| AC-006 | SDD-C-001 | N/A | Plan step produces `merge-required` | `_classify_entries` | T-106 | spec.md § AC-006 | `upgrade_plan.json` |
| AC-007 | SDD-C-011 | N/A | No hook duplication on second pass | `_yaml_merge_precommit_hooks` duplicate-id guard | T-107 | spec.md § AC-007 | N/A |
| AC-008 | SDD-C-013 | N/A | Summary lists preserved hook IDs | `_write_summary` | T-108 | spec.md § AC-008 | `upgrade_summary.md` |

## Graph Linkage
- Graph file: `graph.json`
- Node IDs referenced: FR-001, FR-002, FR-003, FR-004, FR-005, FR-006, FR-007, FR-008, NFR-SEC-001, NFR-OBS-001, NFR-REL-001, NFR-OPS-001, NFR-A11Y-001, AC-001, AC-002, AC-003, AC-004, AC-005, AC-006, AC-007, AC-008

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
- Follow-up 1: Allowlist-based triage preference per path (deferred per spec § Potential Deferred Proposals) — parked in AGENTS.backlog.md under `on-scope: upgrade`.
