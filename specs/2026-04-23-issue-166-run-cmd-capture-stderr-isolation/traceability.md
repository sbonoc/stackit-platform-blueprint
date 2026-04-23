# Traceability Matrix

## Requirement-to-Delivery Mapping

| Requirement ID | Control IDs | Design Element | Implementation Path(s) | Test Evidence | Documentation Evidence | Operational Evidence |
|---|---|---|---|---|---|---|
| FR-001 | SDD-C-005 | Remove `2>&1` from `run_cmd_capture` command substitution | `scripts/lib/shell/exec.sh` — `run_cmd_capture` function body | `test_run_cmd_capture_does_not_merge_stderr_into_stdout` (AC-001 assertion) | inline doc comment in `exec.sh` | n/a |
| FR-002 | SDD-C-005 | Inline doc comment above `run_cmd_capture` definition | `scripts/lib/shell/exec.sh` — line above `run_cmd_capture()` | `test_run_cmd_capture_does_not_merge_stderr_into_stdout` (AC-002 assertion) | doc comment text in `exec.sh` | n/a |
| NFR-SEC-001 | SDD-C-009 | Single-line removal; no new env vars or subprocess calls | `scripts/lib/shell/exec.sh` diff | `shellcheck --severity=error` pass; structural test | n/a | n/a |
| NFR-OBS-001 | SDD-C-010 | Failure path continues to `printf '%s\n' "$output" >&2` | `scripts/lib/shell/exec.sh` — failure branch of `run_cmd_capture` | structural test confirms failure branch retained | n/a | stderr from subprocess directly visible in terminal |
| NFR-REL-001 | SDD-C-012 | All 12 call sites unchanged; inherit fix automatically | `scripts/bin/infra/`, `scripts/bin/platform/auth/`, `scripts/lib/infra/tooling.sh` | `make quality-hooks-fast` green; shellcheck on all modified scripts | n/a | n/a |
| AC-001 | SDD-C-012 | `run_cmd_capture` body does not contain `2>&1` | `scripts/lib/shell/exec.sh` | `test_run_cmd_capture_does_not_merge_stderr_into_stdout` | n/a | n/a |
| AC-002 | SDD-C-012 | Doc comment present above `run_cmd_capture` | `scripts/lib/shell/exec.sh` | `test_run_cmd_capture_does_not_merge_stderr_into_stdout` | doc comment in `exec.sh` | n/a |
| AC-003 | SDD-C-012 | `exec.sh` passes shellcheck after change | `scripts/lib/shell/exec.sh` | `shellcheck --severity=error scripts/lib/shell/exec.sh` | n/a | n/a |
| AC-004 | SDD-C-012 | Structural test asserts AC-001 and AC-002 | `tests/blueprint/contract_refactor_scripts_cases.py` | pytest pass | n/a | n/a |

## Graph Linkage
- Graph file: `graph.json`
- Every `FR-###`, `NFR-*-###`, and `AC-###` listed in this file MUST have a corresponding node in `graph.json`.
- Node IDs referenced:
  - FR-001
  - FR-002
  - NFR-SEC-001
  - NFR-OBS-001
  - NFR-REL-001
  - AC-001
  - AC-002
  - AC-003
  - AC-004

## Validation Summary
- Required bundles executed: `make quality-hooks-fast`, `shellcheck --severity=error scripts/lib/shell/exec.sh`, `python3 -m pytest tests/blueprint/contract_refactor_scripts_cases.py -k run_cmd_capture -v`
- Result summary: all gates green; 105 tests pass; shellcheck clean; 1 new structural test passes
- Documentation validation:
  - `make docs-build`
  - `make docs-smoke`

## Evidence Manifest
- Manifest file: `evidence_manifest.json`
- Context export: `context_pack.md`
- PR context export: `pr_context.md`
- Hardening review export: `hardening_review.md`

## Open Risks and Follow-Ups
- None.
