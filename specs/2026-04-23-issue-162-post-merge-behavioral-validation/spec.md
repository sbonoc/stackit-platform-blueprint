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
- ADR path: docs/blueprint/architecture/decisions/ADR-issue-162-post-merge-behavioral-validation.md
- ADR status: approved

## Applicable Guardrail Controls (Normative)
- Applicable control IDs: SDD-C-001, SDD-C-002, SDD-C-003, SDD-C-004, SDD-C-005, SDD-C-006, SDD-C-007, SDD-C-008, SDD-C-009, SDD-C-010, SDD-C-011, SDD-C-012, SDD-C-013, SDD-C-014, SDD-C-015, SDD-C-016, SDD-C-017, SDD-C-018, SDD-C-019, SDD-C-020, SDD-C-021
- Control exception rationale: none

## Implementation Stack Profile (Normative)
- Backend stack profile: python_scripting_plus_bash (Python stdlib + subprocess; no web framework)
- Frontend stack profile: none
- Test automation profile: pytest
- Agent execution model: single-agent
- Managed service preference: explicit-consumer-exception
- Managed service exception rationale: Tooling-only Python/shell script change; no managed service is provisioned or consumed by this work item.
- Runtime profile: local-first-docker-desktop-kubernetes
- Local Kubernetes context policy: docker-desktop-preferred
- Local provisioning stack: crossplane-plus-helm
- Runtime identity baseline: eso-plus-argocd-plus-keycloak
- Local-first exception rationale: This change adds Python scripting and shell tooling with no K8s, Crossplane, or runtime identity components. The local-first profile is declared for compliance; none of its runtime components are exercised by this work item.

## Objective
- Business outcome: Consumer upgrade runs that apply 3-way-merged shell scripts are validated for behavioral correctness before the upgrade is declared complete, preventing silent `command not found` regressions from reaching CI or production.
- Success metric: Any upgrade apply run that produces a `result=merged` `.sh` file with a dropped function definition is detected and blocked by the postcheck gate; the postcheck report includes actionable per-file findings (file path, symbol, line).

## Normative Requirements

### Functional Requirements (Normative)

- REQ-001 The behavioral gate MUST run `bash -n <file>` on every `.sh` file whose apply report entry carries `result=merged`, and MUST treat a non-zero exit code as a hard gate failure.
- REQ-002 The behavioral gate MUST perform a symbol resolution check for every `.sh` file in scope: for every function call site identified in a merged script, the gate MUST verify that a corresponding function definition is reachable in the same file or in files directly sourced by it (depth-1 `source`/`.` resolution), and MUST report each unresolved call site as a gate failure.
- REQ-003 Each gate failure MUST surface the specific file path, the unresolved symbol name, and the line number (where determinable) so the consumer has an actionable error.
- REQ-004 The behavioral gate MUST be integrated into the existing postcheck orchestrator (`upgrade_consumer_postcheck.py`) and MUST run after merge-required entries are applied, before the upgrade is declared complete.
- REQ-005 The gate MUST be skippable only via `BLUEPRINT_UPGRADE_SKIP_BEHAVIORAL_CHECK=true`; when skipped, the postcheck MUST emit a prominent warning and MUST record `behavioral_check_skipped: true` in the report.
- REQ-006 The postcheck report JSON artifact MUST include a `behavioral_check` section containing: `skipped` (bool), `files_checked` (int), `syntax_errors` (list of `{file, error}`), `unresolved_symbols` (list of `{file, symbol, line}`), `status` (`pass`/`fail`/`skipped`).
- REQ-007 The `blocked_reasons` list in the postcheck report MUST include `behavioral-check-failure` when the gate status is `fail`.
- REQ-008 The shell wrapper `upgrade_consumer_postcheck.sh` MUST read `BLUEPRINT_UPGRADE_SKIP_BEHAVIORAL_CHECK` from the environment and forward it to the Python postcheck module.
- REQ-009 The shell wrapper MUST emit the metric `blueprint_upgrade_postcheck_behavioral_check_failures_total` with the count of behavioral gate failures after the Python module completes.
- REQ-010 The implementation MUST NOT require a full shell parser; a grep/regex heuristic covering the common patterns (`function foo`, `foo ()`, and `source`/`.` directives) is sufficient for MVP.
- REQ-011 Every unit assertion for the behavioral gate MUST include at least one positive-path fixture (merged script with all call sites defined — gate passes) and at least one negative-path fixture (merged script with a dropped function definition — gate reports the unresolved symbol); empty-result-only assertions MUST NOT satisfy coverage.

### Non-Functional Requirements (Normative)

- NFR-SEC-001 The gate MUST NOT execute merged script content; `bash -n` MUST be used for syntax-only parsing. No shell execution of untrusted merged content is permitted.
- NFR-OBS-001 Gate outcomes MUST be recorded in the postcheck JSON artifact (`behavioral_check` section). The shell wrapper MUST emit `blueprint_upgrade_postcheck_behavioral_check_failures_total` metric. A `log_warn` MUST be emitted when the gate is skipped.
- NFR-REL-001 Gate failure MUST NOT mutate the working tree. The opt-out flag MUST provide a deterministic escape hatch. The gate MUST be idempotent (re-runnable on the same apply artifact without side effects).
- NFR-OPS-001 Failure output MUST identify the specific file, symbol, and line so consumers can locate and fix the merge result without additional diagnosis. The postcheck JSON artifact MUST be the canonical authoritative evidence for CI/CD reporting.

## Normative Option Decision
- Option A: Implement gate logic in a new standalone module `scripts/lib/blueprint/upgrade_shell_behavioral_check.py`, integrated into `upgrade_consumer_postcheck.py` as a function call.
- Option B: Inline all gate logic directly in `upgrade_consumer_postcheck.py`.
- Selected option: OPTION_A
- Rationale: A standalone module is independently unit-testable without standing up the full postcheck orchestration, satisfies SRP, and can be reused or extended without touching the orchestrator. Option B would bloat `upgrade_consumer_postcheck.py` and couple gate tests to the full postcheck fixture stack.

## Contract Changes (Normative)
- Config/Env contract: New env var `BLUEPRINT_UPGRADE_SKIP_BEHAVIORAL_CHECK` (default `false`); accepted by `upgrade_consumer_postcheck.sh` and forwarded to Python module.
- API contract: none
- Event contract: none
- Make/CLI contract: No new Make targets. Existing `blueprint-upgrade-consumer-postcheck` target is unchanged; gate is transparent to callers.
- Docs contract: `docs/blueprint/` reference docs for the upgrade postcheck phase MUST be updated to document the new gate and the opt-out flag.

## Blueprint Upstream Defect Escalation (Normative)
- Upstream issue URL: none (this is the blueprint fix itself)
- Temporary workaround path: none
- Replacement trigger: none
- Workaround review date: none

## Normative Acceptance Criteria

- AC-001 Given an upgrade apply report containing a `.sh` file with `result=merged` that has a syntax error, the postcheck MUST exit non-zero and the report MUST include the file path and syntax error in `behavioral_check.syntax_errors`.
- AC-002 Given an upgrade apply report containing a `.sh` file with `result=merged` where a function call site has no reachable definition in the same file or depth-1 sourced files, the postcheck MUST exit non-zero and the report MUST include the file, symbol, and line in `behavioral_check.unresolved_symbols`.
- AC-003 Given an upgrade apply report where all `result=merged` `.sh` files pass syntax check and symbol resolution, the postcheck MUST exit zero and `behavioral_check.status` MUST be `pass`.
- AC-004 Given `BLUEPRINT_UPGRADE_SKIP_BEHAVIORAL_CHECK=true`, the postcheck MUST exit zero for behavioral gate reasons, `behavioral_check.skipped` MUST be `true`, `behavioral_check.status` MUST be `skipped`, and a warning MUST appear in the log output.
- AC-005 The `blocked_reasons` list in the postcheck report MUST contain `behavioral-check-failure` if and only if `behavioral_check.status` is `fail`.
- AC-006 The metric `blueprint_upgrade_postcheck_behavioral_check_failures_total` MUST be emitted by the shell wrapper with the correct failure count after postcheck completes.

## Informative Notes (Non-Normative)
- Context: This is Phase 2, Issue #162 of the consumer upgrade flow improvement programme. Phase 1 (#169) introduced the CI e2e upgrade validation lane; this gate extends the postcheck phase that lane already invokes.
- Tradeoffs: Grep-based heuristics have known false negatives (dynamic function names, heredoc call sites, deep source chains). These are accepted for MVP as they cover the dominant failure pattern described in the issue. A follow-up can deepen source resolution if false negatives are observed.
- Clarifications: Symbol resolution depth is explicitly capped at 1 (direct `source`/`.` calls only). Dynamically constructed function names are out of scope. Only `.sh` files with `result=merged` in the apply report are in scope; `result=applied` files (clean copies) cannot drop definitions.

## Explicit Exclusions
- Transitive source-chain resolution beyond depth 1.
- Non-shell file types (YAML, Python, Makefile, and similar).
- Files with `result=applied` or `result=skipped` in the apply report.
- Variable, alias, or export symbol tracking (functions only for MVP).
- Dynamically constructed function names or call sites in heredocs.
- Fully general POSIX shell parser.
