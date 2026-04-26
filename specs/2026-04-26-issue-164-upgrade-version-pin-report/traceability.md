# Traceability Matrix

## Requirement-to-Delivery Mapping

| Requirement ID | Control IDs | Design Element | Implementation Path(s) | Test Evidence | Documentation Evidence | Operational Evidence |
|---|---|---|---|---|---|---|
| FR-001 | SDD-C-005 | Version pin diff — baseline ref derived from `blueprint/contract.yaml` → `spec.repository.template_bootstrap.template_version`; resolved via `_resolve_baseline_ref` (tries `v{version}` then `{version}` as tag candidates); both baseline and target `versions.sh` read via `git show <ref>:scripts/lib/infra/versions.sh` with `cwd=BLUEPRINT_UPGRADE_SOURCE` | `scripts/lib/blueprint/upgrade_version_pin_diff.py` | `tests/blueprint/test_upgrade_version_pin_diff.py` — `_resolve_baseline_ref` fixture (version string → resolved tag or None); mocked git subprocess returns fixture `versions.sh` content | `architecture.md` §Integration Edges | `artifacts/blueprint/version_pin_diff.json` |
| FR-002 | SDD-C-005 | `parse_versions_sh` + `diff_pins` domain functions | `scripts/lib/blueprint/upgrade_version_pin_diff.py` | `tests/blueprint/test_upgrade_version_pin_diff.py` — parse and diff fixture assertions | `architecture.md` §High-Level Component Design | `artifacts/blueprint/version_pin_diff.json` |
| FR-003 | SDD-C-005 | `scan_template_references` — rglob + substring match | `scripts/lib/blueprint/upgrade_version_pin_diff.py` | `tests/blueprint/test_upgrade_version_pin_diff.py` — fixture template dir with known variable reference | `architecture.md` §High-Level Component Design | `artifacts/blueprint/version_pin_diff.json` |
| FR-004 | SDD-C-005, SDD-C-013 | JSON artifact schema — `baseline_ref`, `target_ref`, `changed_pins`, `new_pins`, `removed_pins`, `unchanged_count` | `scripts/lib/blueprint/upgrade_version_pin_diff.py` | `tests/blueprint/test_upgrade_version_pin_diff.py` — JSON output shape assertions | `architecture.md` §Data Flow diagram | `artifacts/blueprint/version_pin_diff.json` |
| FR-005 | SDD-C-009, SDD-C-011 | Error isolation — catch all exceptions, emit error artifact, return zero | `scripts/lib/blueprint/upgrade_version_pin_diff.py` | `tests/blueprint/test_upgrade_version_pin_diff.py` — mocked subprocess `CalledProcessError` → error artifact path | `plan.md` §Slice 1 error-path test | `artifacts/blueprint/version_pin_diff.json` `error` field |
| FR-006 | SDD-C-003, SDD-C-005 | Pipeline Stage 1b invocation with `|| true` guard | `scripts/bin/blueprint/upgrade_consumer_pipeline.sh` | Pipeline invocation smoke (if available); `make quality-hooks-run` | `architecture.md` §Pipeline Stage Sequence diagram | Stage 1b log output in pipeline run |
| FR-007 | SDD-C-005, SDD-C-012 | `_render_version_pin_section` in residual report | `scripts/lib/blueprint/upgrade_residual_report.py` | `tests/blueprint/` residual section fixture tests | `plan.md` §Slice 3 | `artifacts/blueprint/upgrade-residual.md` |
| FR-008 | SDD-C-012 | Zero-changes message path in `_render_version_pin_section` | `scripts/lib/blueprint/upgrade_residual_report.py` | `tests/blueprint/` zero-changes fixture assertion | `plan.md` §Slice 3 | `artifacts/blueprint/upgrade-residual.md` |
| FR-009 | SDD-C-012 | Prescribed action string per changed pin entry | `scripts/lib/blueprint/upgrade_residual_report.py` | `tests/blueprint/` prescribed-action string assertion in rendered Markdown | `plan.md` §Slice 3 | `artifacts/blueprint/upgrade-residual.md` |
| FR-010 | SDD-C-008, SDD-C-016 | Operator guidance step in skill runbook | `.agents/skills/blueprint-consumer-upgrade/SKILL.md` | Skill runbook review (manual) | `plan.md` §Slice 6 | Skill runbook diff in PR |
| NFR-PERF-001 | SDD-C-006 | Local git ops only — no network calls | `scripts/lib/blueprint/upgrade_version_pin_diff.py` | `tests/blueprint/` mocked subprocess confirms no real network call; timing assertion optional | `spec.md` §NFR-PERF-001 | Pipeline Stage 1b elapsed time in log |
| NFR-SEC-001 | SDD-C-009 | No secrets in `versions.sh`; no filtering required | `scripts/lib/blueprint/upgrade_version_pin_diff.py` | No test required — invariant by inspection of `versions.sh` content | `spec.md` §NFR-SEC-001 | `version_pin_diff.json` review in PR |
| NFR-OBS-001 | SDD-C-010 | `log_info`/`log_warning`/`log_error` per stage | `scripts/lib/blueprint/upgrade_version_pin_diff.py` | `tests/blueprint/` log capture assertions (stdout/stderr) | `architecture.md` §Non-Functional Architecture Notes | Pipeline run log output |
| NFR-REL-001 | SDD-C-011 | Graceful degradation — absent/malformed artifact → fallback text | `scripts/lib/blueprint/upgrade_residual_report.py` | `tests/blueprint/` absent-artifact fixture → fallback message assertion | `plan.md` §Risks and Mitigations | `artifacts/blueprint/upgrade-residual.md` fallback section |
| NFR-OPS-001 | SDD-C-008 | Standalone CLI: env vars `BLUEPRINT_UPGRADE_SOURCE` + `BLUEPRINT_UPGRADE_REF` consumed from environment (mirrors Stage 5 pattern); `--repo-root` is the only argparse flag; baseline ref resolved internally | `scripts/lib/blueprint/upgrade_version_pin_diff.py` | `tests/blueprint/` env-var invocation test (set `BLUEPRINT_UPGRADE_SOURCE`/`BLUEPRINT_UPGRADE_REF`, invoke `main()`, assert artifact written) | `spec.md` §NFR-OPS-001 | `BLUEPRINT_UPGRADE_SOURCE=. BLUEPRINT_UPGRADE_REF=v1.7.0 python3 upgrade_version_pin_diff.py --repo-root .` |
| AC-001 | SDD-C-012 | Changed pin + template reference → residual section | `upgrade_version_pin_diff.py`, `upgrade_residual_report.py` | T-103 positive-path fixture test | `pr_context.md` §Validation Evidence | `artifacts/blueprint/upgrade-residual.md` |
| AC-002 | SDD-C-012 | Zero-changes path | `upgrade_residual_report.py` | T-102 zero-changes fixture assertion | `pr_context.md` §Validation Evidence | `artifacts/blueprint/upgrade-residual.md` |
| AC-003 | SDD-C-012 | New-pins subsection | `upgrade_version_pin_diff.py`, `upgrade_residual_report.py` | T-101 new-pins fixture assertion | `pr_context.md` §Validation Evidence | `artifacts/blueprint/upgrade-residual.md` |
| AC-004 | SDD-C-012 | Removed-pins subsection | `upgrade_version_pin_diff.py`, `upgrade_residual_report.py` | T-101 removed-pins fixture assertion | `pr_context.md` §Validation Evidence | `artifacts/blueprint/upgrade-residual.md` |
| AC-005 | SDD-C-011 | Git error → error artifact + fallback text | `upgrade_version_pin_diff.py`, `upgrade_residual_report.py` | T-104 mocked error path test | `pr_context.md` §Validation Evidence | `artifacts/blueprint/version_pin_diff.json` `error` field |
| AC-006 | SDD-C-012 | Fixture-driven parse + diff → correct JSON output | `upgrade_version_pin_diff.py` | T-101 / T-103 positive-path unit test | `pr_context.md` §Validation Evidence | `version_pin_diff.json` |

## Graph Linkage
- Graph file: `graph.json`
- Every `FR-###`, `NFR-*-###`, and `AC-###` listed in this file MUST have a corresponding node in `graph.json`.
- Node IDs referenced:
  - FR-001, FR-002, FR-003, FR-004, FR-005, FR-006, FR-007, FR-008, FR-009, FR-010
  - NFR-PERF-001, NFR-SEC-001, NFR-OBS-001, NFR-REL-001, NFR-OPS-001
  - AC-001, AC-002, AC-003, AC-004, AC-005, AC-006

## Validation Summary
- Required bundles executed: (to be completed at Publish phase)
- Result summary: (to be completed at Publish phase)
- Documentation validation:
  - `make docs-build`
  - `make docs-smoke`

## Evidence Manifest
- Manifest file: `evidence_manifest.json`
- Context export: `context_pack.md`
- PR context export: `pr_context.md`
- Hardening review export: `hardening_review.md`

## Open Risks and Follow-Ups
- Follow-up 1: Value-based template scanning (matching hardcoded version strings, not just variable names) — deferred to a separate work item.
- Follow-up 2: Issue #183 (stale reconcile report) re-triage after next upgrade cycle to confirm deterministic pipeline fully eliminates the stale-report risk surface.
