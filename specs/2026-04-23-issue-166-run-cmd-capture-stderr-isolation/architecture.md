# Architecture

## Context
- Work item: 2026-04-23-issue-166-run-cmd-capture-stderr-isolation
- Owner: bonos
- Date: 2026-04-23

## Stack and Execution Model
- Backend stack profile: python_plus_fastapi_pydantic_v2
- Frontend stack profile: vue_router_pinia_onyx
- Test automation profile: pytest_vitest_playwright_pact
- Agent execution model: specialized-subagents-isolated-worktrees

## Problem Statement
- What needs to change and why: `run_cmd_capture` in `scripts/lib/shell/exec.sh` uses `output="$("$@" 2>&1)"`, which merges stderr into the captured stdout. Any subprocess warning or diagnostic line is silently injected into the output and corrupts downstream consumers that parse it (JSON parsers, YAML appliers, grep pipelines). The failure is environment-dependent and produces exit code 0, making it very hard to diagnose.
- Scope boundaries: single function body change in `scripts/lib/shell/exec.sh` plus a doc comment; one structural test added.
- Out of scope: new helper functions, caller migration beyond inheriting the fix, audit of other stderr-merge sites.

## Bounded Contexts and Responsibilities
- Shell execution primitives (`scripts/lib/shell/exec.sh`): defines `run_cmd()` and `run_cmd_capture()`; the only change is in `run_cmd_capture`.
- Callers (12 call sites across `scripts/bin/` and `scripts/lib/`): unchanged; they inherit the fixed behavior automatically.

## High-Level Component Design
- Domain layer: not applicable (shell utility library).
- Application layer: `run_cmd_capture` is a low-level shell capture primitive; no application-layer logic changes.
- Infrastructure adapters: not applicable.
- Presentation/API/workflow boundaries: not applicable.

## Integration and Dependency Edges
- Upstream dependencies: none new; `bash`, `shellcheck` already required.
- Downstream dependencies: all 12 call sites of `run_cmd_capture` inherit the corrected stdout-only behavior automatically; no call site changes are required.
- Data/API/event contracts touched: none.

## Non-Functional Architecture Notes
- Security: removing `2>&1` eliminates the risk of a malicious or unexpected stderr line being silently incorporated into a parsed secret, kubeconfig, or manifest file.
- Observability: no new logs or metrics; stderr from subprocesses becomes directly visible in the terminal output on both success and failure, which improves diagnosability.
- Reliability and rollback: the change is a single-line removal; rollback is `git revert`. No state is introduced.
- Monitoring/alerting: none required.

## Risks and Tradeoffs
- Risk 1 (a caller depends on stderr being merged into stdout): investigation found no such caller — all 12 sites redirect to files or `/dev/null`. The risk is negligible.
- Tradeoff 1 (stderr now visible on success): some callers may expose subprocess informational messages that were previously hidden. This is the correct behavior; it aids diagnosability.

## Diagram

```
Before:
  run_cmd_capture cmd [args...]
    stdout ──┐
    stderr ──┤ (2>&1) → $output → caller's stdout/file
             └─────────────────────────────────────────

After:
  run_cmd_capture cmd [args...]
    stdout ──→ $output → caller's stdout/file
    stderr ──→ shell's stderr (directly visible)
```
