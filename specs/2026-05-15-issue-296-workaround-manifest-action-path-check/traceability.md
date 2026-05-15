# Traceability Matrix

## Requirement-to-Delivery Mapping

| Requirement ID | Control IDs | WCAG SC | Design Element | Implementation Path(s) | Test Evidence | Documentation Evidence | Operational Evidence |
|---|---|---|---|---|---|---|---|
| FR-001 | SDD-C-005, SDD-C-011 | — | `quality-workaround-manifest-check` Make target | `make/blueprint.generated.mk` + `scripts/templates/blueprint/bootstrap/make/blueprint.generated.mk.tmpl` | AC-001: `make quality-workaround-manifest-check` exits 0 | Make target self-documenting via inline `##` comment | n/a |
| FR-002 | SDD-C-005, SDD-C-011 | — | `check_workaround_manifest.py` checker | `scripts/bin/quality/check_workaround_manifest.py` | AC-001 (exit 0 valid), AC-002 (exit 1 missing file), AC-004 pytest | n/a | n/a |
| FR-003 | SDD-C-005, SDD-C-011 | — | `hooks_fast.sh` wiring | `scripts/bin/quality/hooks_fast.sh` — unconditional `run_check` | AC-003: summary includes PASS | n/a | n/a |
| FR-004 | SDD-C-005, SDD-C-008 | — | Pytest test coverage | `tests/blueprint/test_workaround_manifest_check.py` | AC-004: pytest passes — exit 0, exit 1, live-manifest paths | n/a | n/a |
| FR-005 | SDD-C-005, SDD-C-011 | — | `.PHONY` list + template mirror | `make/blueprint.generated.mk` + template counterpart | AC-005: `make quality-hooks-fast` passes | n/a | n/a |
| NFR-PERF-001 | SDD-C-012 | — | Checker completes < 1s | `check_workaround_manifest.py` — `Path.exists()` only | Observed wall time from `make quality-workaround-manifest-check` | n/a | n/a |
| NFR-MAINT-001 | SDD-C-007 | — | No import of `upgrade_workarounds.py` | `check_workaround_manifest.py` imports stdlib + pyyaml only | Code review of imports | n/a | n/a |
| NFR-ADDITIVE-001 | SDD-C-007 | — | Existing checks unmodified | `hooks_fast.sh` diff — no deletions in existing `run_check` calls | PR diff review | n/a | n/a |
| NFR-SEC-001 | SDD-C-009 | — | File existence only — no execution | `check_workaround_manifest.py` — `Path.exists()`, no exec/subprocess on action files | Code review | n/a | n/a |
| NFR-OBS-001 | SDD-C-010 | — | `[quality-workaround-manifest-check]`-prefixed output | `check_workaround_manifest.py` stdout/stderr | AC-002: error output confirmed in pytest | n/a | n/a |
| NFR-REL-001 | SDD-C-012 | — | Missing manifest exits non-zero with clear message | `check_workaround_manifest.py` explicit `FileNotFoundError` guard | pytest or manual test | n/a | n/a |
| NFR-OPS-001 | SDD-C-010 | — | Inline `##` Make comment | `make/blueprint.generated.mk` target line | Code review | n/a | n/a |
| NFR-A11Y-001 | — | — | N/A — no UI changes | — | — | — | — |
| AC-001 | SDD-C-012 | — | Exit 0 for valid manifest | `make quality-workaround-manifest-check` | Pass confirmed post-implementation | — | n/a |
| AC-002 | SDD-C-012 | — | Exit 1 + stderr for missing file | checker + pytest case (b) | pytest PASS | — | n/a |
| AC-003 | SDD-C-012 | — | `quality-workaround-manifest-check  PASS` in hooks_fast summary | `hooks_fast.sh` | `make quality-hooks-fast` output | — | n/a |
| AC-004 | SDD-C-012 | — | Pytest all 3 cases pass | `tests/blueprint/test_workaround_manifest_check.py` | pytest PASS | — | n/a |
| AC-005 | SDD-C-012 | — | `make quality-hooks-fast` passes end-to-end | full fast gate | `make quality-hooks-fast` output | — | n/a |

## Graph Linkage
- Graph file: `graph.json`
- Every `FR-###`, `NFR-*-###`, and `AC-###` listed in this file MUST have a corresponding node in `graph.json`.
- Node IDs referenced:
  - FR-001, FR-002, FR-003, FR-004, FR-005
  - NFR-PERF-001, NFR-MAINT-001, NFR-ADDITIVE-001, NFR-SEC-001, NFR-OBS-001, NFR-REL-001, NFR-OPS-001, NFR-A11Y-001
  - AC-001, AC-002, AC-003, AC-004, AC-005

## Validation Summary
- Required bundles executed: `make quality-hooks-fast`, `make infra-validate`, `uv run pytest tests/blueprint/test_workaround_manifest_check.py -v`
- Result summary: 6 pytest tests pass; `make quality-workaround-manifest-check` exits 0; `quality-workaround-manifest-check PASS` in `quality-hooks-fast` summary; all other fast-gate checks pass.
- Documentation validation:
  - `make docs-build`: PASS — static site generated successfully
  - `make docs-smoke`: PASS

## Evidence Manifest
- Manifest file: `evidence_manifest.json`
- Context export: `context_pack.md`
- PR context export: `pr_context.md`
- Hardening review export: `hardening_review.md`

## Open Risks and Follow-Ups
- None at intake.
