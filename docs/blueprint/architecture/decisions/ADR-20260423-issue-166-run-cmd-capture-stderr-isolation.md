# ADR-20260423-issue-166-run-cmd-capture-stderr-isolation: Isolate stderr from stdout in run_cmd_capture

## Metadata
- Status: approved
- Date: 2026-04-23
- Owners: bonos
- Related spec path: specs/2026-04-23-issue-166-run-cmd-capture-stderr-isolation/spec.md

## Business Objective and Requirement Summary
- Business objective: Prevent stderr from subprocesses from silently corrupting parsed stdout output in any script that uses `run_cmd_capture`.
- Functional requirements summary: Remove `2>&1` from `run_cmd_capture` in `scripts/lib/shell/exec.sh` so it captures stdout only. Add a doc comment stating the stdout-only contract.
- Non-functional requirements summary: purely additive fix; no new env vars, no new abstractions, no call site changes required.
- Desired timeline: 2026-04-23.

## Decision Drivers
- Driver 1: `run_cmd_capture` currently merges stderr into stdout via `2>&1`. When a subprocess emits a warning or diagnostic on stderr, that line is silently injected into the caller's output and corrupts any downstream parser (JSON, YAML, grep).
- Driver 2: The failure is environment-dependent (occurs only when the subprocess emits stderr), exits with code 0, and is very hard to diagnose. All 12 existing call sites redirect output to files or `/dev/null` — none rely on stderr being merged.
- Driver 3: A stdout-only capture variant already exists for the kubectl case (`run_kubectl_capture_stdout_with_active_access`), confirming that the correct pattern is stream isolation, not merging.

## Options Considered
- Option A: Remove `2>&1` from `run_cmd_capture` — stdout-only capture; stderr passes through to the shell's stderr.
- Option B: Add a prominent doc comment warning only; leave `2>&1` behavior unchanged.
- Option C: Introduce a new `run_cmd_capture_stdout` variant; migrate all parsing call sites to it.

## Decision
- Selected option: Option A
- Rationale: Option A is the minimal correct fix. All 12 existing call sites investigated — none rely on stderr being merged. Option B leaves the hazard in the primitive. Option C adds unnecessary abstraction; the existing `run_kubectl_capture_stdout_with_active_access` pattern shows that when strict stdout isolation is needed, a caller-specific variant is used — but fixing the general primitive makes all callers safe by default.

## Consequences
- Positive: `run_cmd_capture` is safe for output-parsing use cases. Stderr from subprocesses becomes directly visible on both success and failure, improving diagnosability.
- Negative: Subprocess informational messages that were previously silently swallowed may now appear in terminal output on success. This is the correct behavior.
- Neutral: No call site changes required. `run_kubectl_capture_with_active_access` (which wraps `run_cmd_capture`) inherits the corrected behavior automatically.

## Diagram

```
Before:
  run_cmd_capture cmd [args...]
    cmd stdout ──┐
    cmd stderr ──┘ (2>&1) → $output → caller stdout / file

After:
  run_cmd_capture cmd [args...]
    cmd stdout ──→ $output → caller stdout / file
    cmd stderr ──→ shell stderr (directly visible)
```
