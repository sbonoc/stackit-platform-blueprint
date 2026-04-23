# Architecture

## Context
- Work item: issue-162-post-merge-behavioral-validation
- Owner: blueprint maintainer
- Date: 2026-04-23

## Stack and Execution Model
- Backend stack profile: python_scripting_plus_bash (pure Python stdlib + subprocess; no FastAPI/Pydantic)
- Frontend stack profile: none
- Test automation profile: pytest
- Agent execution model: single-agent (bounded change in upgrade pipeline)

## Problem Statement
- What needs to change and why: The upgrade postcheck phase validates that 3-way merges were applied but does not validate that the merged shell scripts are behaviorally correct. A merge can silently drop a function definition while its call site is retained, producing a `command not found` failure at runtime — the most dangerous upgrade failure class because the upgrade report is green and the defect only surfaces on execution.
- Scope boundaries: New behavioral gate injected into the existing `upgrade_consumer_postcheck.py` orchestrator, applied only to `.sh` files whose apply report entry carries `result=merged` (i.e. 3-way-merged files). Shell wrapper `upgrade_consumer_postcheck.sh` forwards the opt-out flag and emits new metrics. New module `scripts/lib/blueprint/upgrade_shell_behavioral_check.py` holds all gate logic.
- Out of scope: Transitive source-chain resolution beyond depth 1; variable/alias symbol tracking; non-shell file types; files with `result=applied` or `result=skipped` (only clean copies — no merge drops possible); fully general shell parser.

## Bounded Contexts and Responsibilities

### Context A — Behavioral gate logic (`scripts/lib/blueprint/upgrade_shell_behavioral_check.py`, new)
- Receives a list of file paths (the merged `.sh` files from the apply report) and the repo root.
- Runs `bash -n <file>` via subprocess for syntax validation.
- Applies grep-based heuristics to identify function definitions (`function foo` or `foo ()`) and call sites, resolving direct `source`/`.` references at depth 1.
- Returns a structured result per file: syntax pass/fail + list of unresolved call sites (file path, line, symbol).
- No I/O side effects beyond reading existing files and spawning subprocesses.

### Context B — Postcheck orchestrator integration (`scripts/lib/blueprint/upgrade_consumer_postcheck.py`, extended)
- Loads merged-file paths from the apply report (`result=merged`, `.sh` extension).
- Invokes Context A gate, passing the opt-out flag `skip_behavioral_check`.
- Appends `behavioral_check` section to the postcheck report JSON.
- Appends `behavioral-check-failure` to `blocked_reasons` when the gate fails.
- Adds `behavioral_check_skipped` and `behavioral_check_failure_count` to the summary.

### Context C — Shell wrapper (`scripts/bin/blueprint/upgrade_consumer_postcheck.sh`, extended)
- Reads `BLUEPRINT_UPGRADE_SKIP_BEHAVIORAL_CHECK` env var and forwards it to the Python module.
- Emits `blueprint_upgrade_postcheck_behavioral_check_failures_total` metric.
- Emits a prominent `log_warn` when the gate is skipped.

### Context D — Test coverage (`tests/blueprint/test_upgrade_postcheck.py` + fixture shell scripts, extended)
- Positive-path unit assertions: merged script with all call sites defined — gate passes.
- Negative-path unit assertions: merged script with a dropped function definition — gate reports the unresolved call site.
- Opt-out path: `BLUEPRINT_UPGRADE_SKIP_BEHAVIORAL_CHECK=true` — gate skipped, no failure.
- Syntax-error path: merged script with syntax error — syntax check fails.

## High-Level Component Design
- Domain layer: `upgrade_shell_behavioral_check.py` — pure logic, no global state, accepts explicit inputs.
- Application layer: `upgrade_consumer_postcheck.py` — orchestrates gate, merges result into report/summary.
- Infrastructure adapters: subprocess calls to `bash -n`; file reads via `pathlib.Path`.
- Presentation/API/workflow boundaries: CLI — env var `BLUEPRINT_UPGRADE_SKIP_BEHAVIORAL_CHECK`; JSON report artifact; shell wrapper metrics.

## Integration and Dependency Edges
- Upstream dependencies: apply report JSON (`result=merged` entries); `bash` binary on PATH.
- Downstream dependencies: `upgrade_consumer_postcheck.sh` (reads updated postcheck JSON for metrics); CI e2e lane (`ci_upgrade_validate.sh` → `make blueprint-upgrade-consumer-postcheck`).
- Data/API/event contracts touched: postcheck report JSON schema (additive `behavioral_check` key); `blocked_reasons` list (new value `behavioral-check-failure`); postcheck shell wrapper env contract (new `BLUEPRINT_UPGRADE_SKIP_BEHAVIORAL_CHECK` var).

## Non-Functional Architecture Notes
- Security: No shell execution of merged content — `bash -n` performs syntax-only parse, does not execute. No network access. No secrets in scope.
- Observability: New metric `blueprint_upgrade_postcheck_behavioral_check_failures_total`. Structured log lines on skip and failure. Per-file findings in the JSON report.
- Reliability and rollback: Gate failure is a hard block on postcheck success but does not mutate the working tree. Opt-out flag `BLUEPRINT_UPGRADE_SKIP_BEHAVIORAL_CHECK=true` provides a deterministic escape hatch with mandatory warning. Rollback = revert this work item (no schema migration, no persistent state).
- Monitoring/alerting: Existing postcheck status metric already surfaces in CI. New `behavioral_check_failures_total` can be alerted on separately if needed.

## Risks and Tradeoffs
- Risk 1: Grep-based heuristic has false negatives for dynamically constructed function names or call sites inside heredocs. Accepted for MVP — the common case (static function defs/calls in a single file or direct source) is covered. Documented in spec exclusions.
- Tradeoff 1: Depth-1 source resolution only. Full transitive resolution would require a shell interpreter or a significant parser. The issue explicitly accepts this scope for MVP.
