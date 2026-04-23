# Hardening Review

## Repository-Wide Findings Fixed
- Finding 1: `run_cmd_capture` in `scripts/lib/shell/exec.sh` merged stderr into stdout via `2>&1`, silently corrupting parsed output when a subprocess emitted warnings. Fixed by removing `2>&1` so stderr passes through unmodified.

## Observability and Diagnostics Changes
- Metrics/logging/tracing updates: none — stderr from subprocesses now goes directly to the terminal (was previously swallowed into `$output`), improving passive diagnosability without any code change to the observability surface.
- Operational diagnostics updates: none required.

## Architecture and Code Quality Compliance
- SOLID / Clean Architecture / Clean Code / DDD checks: single-responsibility preserved — `run_cmd_capture` now has one clear contract (stdout capture, stderr pass-through). No abstraction added or removed.
- Test-automation and pyramid checks: one structural test added at the unit layer (`contract_refactor_scripts_cases.py`). No integration or e2e tests required; the change is a single-line removal in a utility function.
- Documentation/diagram/CI/skill consistency checks: inline doc comment added to `run_cmd_capture`; no external docs or diagrams required.

## Proposals Only (Not Implemented)
- none
