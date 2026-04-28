# Architecture

## Context
- Work item: 2026-04-28-quality-hooks-keep-going-mode
- Owner: bonos
- Date: 2026-04-28

## Stack and Execution Model
- Backend stack profile: python_plus_fastapi_pydantic_v2
- Frontend stack profile: vue_router_pinia_onyx
- Test automation profile: pytest_vitest_playwright_pact
- Agent execution model: specialized-subagents-isolated-worktrees

## Problem Statement
- What needs to change and why: `scripts/bin/quality/hooks_fast.sh`, `hooks_strict.sh`, and `hooks_run.sh` invoke each check via `run_cmd` under `set -euo pipefail`. The first non-zero exit aborts the script. For an agent inner loop, this means each failing check costs an additional full pass: fix one, re-run the gate, hit the next, re-run, etc. With N independent failures, the gate runs N+1 times. We need an opt-in mode that runs every independent check and reports them together so a single fix-batch can resolve N failures.
- Scope boundaries: a new shell helper `scripts/lib/shell/keep_going.sh`; modifications to the three quality-hooks shell entry points to source the helper and dispatch in keep-going mode; updated make recipes to pass the env var through; help-text updates; an ADR; tests for the helper.
- Out of scope: changing default fail-fast behavior; aggregating pre-commit's internal hooks; parallel check execution; JSON output; new make targets.

## Bounded Contexts and Responsibilities
- Context A (aggregation helper): `scripts/lib/shell/keep_going.sh` owns the per-check execution, output capture, status accumulation, and summary rendering. It is the single authority for what the keep-going summary block looks like and how per-check capture is handled. It exposes a small functional surface (`keep_going_init`, `run_check`, `keep_going_finalize`) and reads `QUALITY_HOOKS_KEEP_GOING` and `QUALITY_HOOKS_KEEP_GOING_TAIL_LINES` from the environment.
- Context B (hooks orchestration): `hooks_fast.sh`, `hooks_strict.sh`, `hooks_run.sh` own the ordered list of checks for their respective phases. They MUST keep the existing `run_cmd` invocations as the default code path and dispatch through the helper only when keep-going is active. They own the pre-commit fail-fast invariant (only `hooks_fast.sh` runs pre-commit) and the cross-phase ordering (`hooks_run.sh` runs strict only after fast pre-commit succeeded).

## High-Level Component Design
- Domain layer: `keep_going.sh` defines `KEEP_GOING_RESULTS` (parallel arrays for check name, status, duration, capture file path), `keep_going_active` (returns 0 when active), `run_check <name> -- <command...>` (executes, captures stdout+stderr to a temp file, records exit code and duration, re-emits the captured-tail to stderr on failure), and `keep_going_finalize` (prints the summary block, removes temp files via the EXIT trap, returns 0/1 by aggregate result).
- Application layer: each hooks entry script after sourcing `keep_going.sh` calls `keep_going_init` near the start. For each check, the script either calls `run_cmd <command>` (default fail-fast — unchanged from today) or `run_check <name> -- <command>` (keep-going mode). A small dispatch wrapper at the top of each script picks one or the other based on `keep_going_active`. At the end of the script, when keep-going is active, `keep_going_finalize` is called and the script exits with its return value. `hooks_run.sh` propagates the keep-going trigger to its child invocations and orders pre-commit explicitly (fast first; strict only when pre-commit passed).
- Infrastructure adapters: per-check captures use `mktemp -t quality_hook_XXXX`; a single EXIT trap (registered via the existing `start_script_metric_trap` mechanism in `exec.sh`, extended to compose with the keep-going cleanup trap) removes the temp directory. Branch detection (`git branch --show-current`) and `blueprint_repo_is_generated_consumer` continue to gate conditional checks; the gating decision happens before dispatch — gated-out checks are not added to the aggregator at all (so the summary reflects only checks actually executed).
- Presentation/API/workflow boundaries: the keep-going summary is plain text on stdout; the marker line is a stable contract (`===== quality-hooks keep-going summary =====`). Exit codes are the only machine-readable signal consumed by `hooks_run.sh` and by `make`.

## Integration and Dependency Edges
- Upstream dependencies: `scripts/lib/shell/exec.sh` (`run_cmd`, `start_script_metric_trap`); `scripts/lib/shell/logging.sh` (`log_info`, `log_warn`, `log_error`, `log_metric`); `scripts/lib/blueprint/contract_runtime.sh` (`blueprint_repo_is_generated_consumer`).
- Downstream dependencies: `make/blueprint.generated.mk` recipes for `quality-hooks-fast`, `quality-hooks-strict`, `quality-hooks-run` and the corresponding template `scripts/templates/blueprint/bootstrap/make/blueprint.generated.mk.tmpl`. The recipes today are `@scripts/bin/quality/hooks_fast.sh` style with no env-var pass-through; make already exports the calling environment, so `QUALITY_HOOKS_KEEP_GOING=true make quality-hooks-fast` works without recipe changes — but recipe doc-comments need to mention it.
- Data/API/event contracts touched: none. The only externally observable contract is the summary marker line and the env var name.

## Non-Functional Architecture Notes
- Security: per-check captures live under `${TMPDIR:-/tmp}` with default user-only permissions; temp files are removed in the EXIT trap; no eval, no shell expansion of captured output (output is `printf '%s\n' "$captured"` only); no widening of script-level filesystem permissions.
- Observability: each check start logs via `log_info` (already present today via `run_cmd`'s `+ <command>` echo); on failure in keep-going mode, a 40-line tail (configurable) is re-emitted to stderr immediately. End-of-run metric `quality_hooks_keep_going_total` includes phase, status, and failed-check count.
- Reliability and rollback: default behavior is byte-identical when env var is unset and flag is not passed (FR-009). Rollback is to revert the patch — no state, no migration. The EXIT trap composes with the existing metric trap so cleanup runs even when checks are killed by signal.
- Monitoring/alerting: none — local developer + agent inner-loop tooling. No production-path SLOs.

## Risks and Tradeoffs
- Risk 1: The aggregation helper introduces a second control flow alongside the existing `run_cmd` calls. If the dispatch branch is buggy, the default path could regress. Mitigation: the default path remains a pure `run_cmd` call (the original line is preserved verbatim under an `if keep_going_active; then run_check ...; else run_cmd ...; fi` guard); a contract test asserts default invocations exit on first failure.
- Risk 2: Cascading false positives — a single root cause (e.g. a syntax error in a shared helper) can produce failures in every aggregated check that loads it. Mitigation: documentation makes the failure-ordering policy explicit ("fix the most fundamental failure first, re-run") and the summary block lists checks in execution order so the earliest failure is the first reported.
- Risk 3: Composing with `set -euo pipefail` — capturing the exit code of a failing command without aborting the script requires deliberate `||` patterns. Mitigation: the helper isolates the only `||` patterns to `run_check` itself; entry scripts continue to use the default `set -e` semantics for everything else.
- Tradeoff 1: Two code paths (default fail-fast and keep-going) increase script complexity slightly but preserve the byte-identical default needed by CI. The alternative — replace `run_cmd` with `run_check` everywhere — would shift all of CI to keep-going semantics, which we explicitly do not want for production gates.
