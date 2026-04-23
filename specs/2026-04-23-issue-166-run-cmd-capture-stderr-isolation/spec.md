# Specification

## Spec Readiness Gate (Blocking)
- SPEC_READY: true
- Open questions count: 0
- Unresolved alternatives count: 0
- Unresolved TODO markers count: 0
- Pending assumptions count: 0
- Open clarification markers count: 0
- Product sign-off: approved
- Architecture sign-off: approved
- Security sign-off: approved
- Operations sign-off: approved
- Missing input blocker token: none
- ADR path: docs/blueprint/architecture/decisions/ADR-20260423-issue-166-run-cmd-capture-stderr-isolation.md
- ADR status: approved

## Applicable Guardrail Controls (Normative)
- Applicable control IDs: SDD-C-005, SDD-C-006, SDD-C-009, SDD-C-010, SDD-C-012
- Control exception rationale: none

## Implementation Stack Profile (Normative)
- Backend stack profile: python_plus_fastapi_pydantic_v2
- Frontend stack profile: vue_router_pinia_onyx
- Test automation profile: pytest_vitest_playwright_pact
- Agent execution model: specialized-subagents-isolated-worktrees
- Managed service preference: stackit-managed-first
- Managed service exception rationale: none
- Runtime profile: local-first-docker-desktop-kubernetes
- Local Kubernetes context policy: docker-desktop-preferred
- Local provisioning stack: crossplane-plus-helm
- Runtime identity baseline: eso-plus-argocd-plus-keycloak
- Local-first exception rationale: none

## Objective
- Business outcome: Any script that calls `run_cmd_capture` and redirects or captures its output for parsing receives only stdout content; stderr from the subprocess is never silently injected into the parsed result, eliminating a class of silent data-corruption failures that are environment-dependent and hard to diagnose.
- Success metric: The body of `run_cmd_capture` in `scripts/lib/shell/exec.sh` does not contain `2>&1`; all 12 existing call sites continue to work correctly; the function carries a doc comment stating the stdout-only contract.

## Normative Requirements

### Functional Requirements (Normative)
- FR-001 `run_cmd_capture` in `scripts/lib/shell/exec.sh` MUST capture stdout only; the `2>&1` merge redirect MUST be removed from its command substitution so that stderr from the subprocess passes through to the shell's stderr unmodified.
- FR-002 `run_cmd_capture` MUST carry an inline doc comment directly above its definition stating: (a) it captures stdout only, (b) stderr from the subprocess passes through to the shell's stderr unmodified and is visible to the caller, and (c) it is safe for output-parsing and file-redirect call sites.

### Non-Functional Requirements (Normative)
- NFR-SEC-001 The fix MUST introduce no new environment variables, subprocess calls, or shell injection vectors; the change MUST be limited to removing `2>&1` and adding the doc comment.
- NFR-OBS-001 On command failure, `run_cmd_capture` MUST continue to print any captured stdout content to stderr via `printf '%s\n' "$output" >&2`; stderr from the subprocess is already directly visible because it was not redirected.
- NFR-REL-001 All 12 existing call sites of `run_cmd_capture` (10 file-redirect patterns, 2 discard-to-`/dev/null` patterns, 1 internal wrapper) MUST continue to work correctly after the change; no call site behavior changes in a breaking way.

## Normative Option Decision
- Option A: Remove `2>&1` from `run_cmd_capture`; stderr passes through unmodified.
- Option B: Add a prominent doc comment warning only; leave the `2>&1` behavior unchanged.
- Option C: Introduce a new `run_cmd_capture_stdout` variant; migrate all parsing call sites to it.
- Selected option: Option A
- Rationale: Option A is the minimal correct fix — all 12 existing call sites redirect output to files or `/dev/null`; none rely on stderr being merged into stdout. Removing `2>&1` makes the function safe by default without introducing new abstractions. Option B leaves a silent data-corruption hazard in the primitive. Option C adds an unnecessary new abstraction: a dedicated stdout-only capture variant already exists for the kubectl case (`run_kubectl_capture_stdout_with_active_access`), and the pattern shows that the correct answer is to fix the general primitive, not proliferate per-command variants.

## Contract Changes (Normative)
- Config/Env contract: none.
- API contract: none.
- Event contract: none.
- Make/CLI contract: none.
- Docs contract: none.

## Blueprint Upstream Defect Escalation (Normative)
- Upstream issue URL: https://github.com/sbonoc/stackit-platform-blueprint/issues/166
- Temporary workaround path: use `run_kubectl_capture_stdout_with_active_access` (or an equivalent stdout-only capture primitive with explicit `2>/dev/null`) for any call site that parses command output.
- Replacement trigger: none (this spec is the fix).
- Workaround review date: none.

## Normative Acceptance Criteria
- AC-001 The body of `run_cmd_capture` in `scripts/lib/shell/exec.sh` does NOT contain `2>&1`.
- AC-002 `run_cmd_capture` carries an inline doc comment directly above its definition describing its stdout-only contract.
- AC-003 `scripts/lib/shell/exec.sh` passes `shellcheck --severity=error` after the change.
- AC-004 A structural test in `tests/blueprint/contract_refactor_scripts_cases.py` asserts AC-001 and AC-002.

## Informative Notes (Non-Normative)
- Context: Issue #166 reports that `run_cmd_capture` merges stderr into stdout via `2>&1`. All 12 existing call sites redirect output to files or `/dev/null`; none assign to a variable and parse inline. The hazard exists for any current or future caller that captures the output in a variable — including all 10 file-redirect sites where a subprocess warning line silently corrupts a JSON or YAML file.
- Tradeoffs: Removing `2>&1` means stderr from the subprocess goes directly to the terminal on both success and failure. This is correct for a function named "capture" — capture means keep stdout for the caller, not merge all streams.
- Clarifications: none.

## Explicit Exclusions
- Migrating `run_kubectl_capture_with_active_access` (the kubectl-specific wrapper) to use a different capture primitive is out of scope; after this fix it inherits the corrected behavior automatically.
- Adding a new `run_cmd_capture_stdout` variant is out of scope; Option A makes it unnecessary.
- Auditing all shell scripts for stderr-merge hazards outside `run_cmd_capture` is out of scope.
