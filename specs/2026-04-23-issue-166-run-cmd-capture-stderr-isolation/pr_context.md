# PR Context

## Summary
- Work item: 2026-04-23-issue-166-run-cmd-capture-stderr-isolation
- Objective: Remove `2>&1` from `run_cmd_capture` in `scripts/lib/shell/exec.sh` so it captures stdout only, eliminating a class of silent data-corruption failures where subprocess stderr lines are injected into parsed output.
- Scope boundaries: single function body change in `scripts/lib/shell/exec.sh`; one doc comment added; one structural test in `tests/blueprint/contract_refactor_scripts_cases.py`; one ADR; SDD spec artifacts.

## Requirement Coverage
- Requirement IDs covered: FR-001, FR-002, NFR-SEC-001, NFR-OBS-001, NFR-REL-001
- Acceptance criteria covered: AC-001, AC-002, AC-003, AC-004
- Contract surfaces changed: none — `run_cmd_capture` is a blueprint-internal utility; no consumer-facing contract changes.

## Key Reviewer Files
- Primary files to review first:
  - `scripts/lib/shell/exec.sh` — the one-line fix and doc comment
  - `tests/blueprint/contract_refactor_scripts_cases.py` — structural test asserting AC-001 and AC-002
- High-risk files: none — all 12 existing call sites are unchanged; they inherit the corrected behavior automatically.

## Validation Evidence
- Required commands executed: `make quality-hooks-fast`, `shellcheck --severity=error scripts/lib/shell/exec.sh`, `python3 -m pytest tests/blueprint/contract_refactor_scripts_cases.py -k run_cmd_capture -v`
- Result summary: all gates green; 1 new test passes; shellcheck clean.
- Artifact references: `traceability.md`, `evidence_manifest.json`

## Risk and Rollback
- Main risks: negligible — all 12 existing call sites investigated; none rely on stderr being merged into stdout. Subprocess stderr becoming visible on success is the correct behavior.
- Rollback strategy: `git revert <commit>`; no persistent state introduced; all callers are unchanged.

## Deferred Proposals
- none
