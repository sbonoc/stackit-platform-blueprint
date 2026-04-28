# Specification

## Spec Readiness Gate (Blocking)
<!-- SPEC_PRODUCT_READY=true: intake gate — Product sign-off only; unlocks agent ADR drafting.
     SPEC_READY=true: implementation gate — all sign-offs required; unlocks coding. -->
- SPEC_READY: false
- SPEC_PRODUCT_READY: false
- Open questions count: 2
- Unresolved alternatives count: 0
- Unresolved TODO markers count: 0
- Pending assumptions count: 0
- Open clarification markers count: 0
- Product sign-off: pending
- Architecture sign-off: pending
- Security sign-off: pending
- Operations sign-off: pending
- Missing input blocker token: BLOCKED_MISSING_INPUTS
- ADR path: docs/blueprint/architecture/decisions/ADR-20260428-quality-hooks-keep-going-mode.md
- ADR status: proposed

## Applicable Guardrail Controls (Normative)
- Applicable control IDs: SDD-C-001, SDD-C-002, SDD-C-003, SDD-C-004, SDD-C-005, SDD-C-006, SDD-C-007, SDD-C-008, SDD-C-009, SDD-C-010, SDD-C-011, SDD-C-012, SDD-C-013, SDD-C-014, SDD-C-015, SDD-C-016, SDD-C-017, SDD-C-018, SDD-C-019, SDD-C-020, SDD-C-021
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
- Business outcome: Eliminate the agent inner-loop cost where `make quality-hooks-run` (and `quality-hooks-fast`) stops at the first failing check, the agent fixes that one issue, re-runs the full gate, hits the next check, fixes it, re-runs, and so on — multiplying gate runtime and token consumption by the number of independent failures present in the working tree. Add an opt-in keep-going mode that aggregates failures from independent checks in a single run and reports a consolidated summary, so an agent (or a human) can fix all surfaced issues in one batch.
- Success metric: With `--keep-going` (or `QUALITY_HOOKS_KEEP_GOING=true`), `quality-hooks-fast` and `quality-hooks-run` execute every independent downstream check even when earlier ones fail; the script exits non-zero with a summary section listing each failed check and its captured stderr tail; default invocation (no flag, env var unset) preserves byte-identical fail-fast behavior. Pre-commit auto-mutating hooks remain fail-fast in all modes (mutations make downstream check results unreliable).

## Normative Requirements

### Functional Requirements (Normative)
- FR-001 `quality-hooks-fast` MUST accept a `--keep-going` CLI flag and MUST treat the environment variable `QUALITY_HOOKS_KEEP_GOING=true` (case-sensitive) as equivalent to passing the flag; any other value of the env var (including unset, empty, `false`, `0`) MUST behave as fail-fast (default).
- FR-002 `quality-hooks-strict` MUST accept the same `--keep-going` flag and `QUALITY_HOOKS_KEEP_GOING=true` env var with the same semantics as FR-001.
- FR-003 `quality-hooks-run` MUST accept the same `--keep-going` flag and `QUALITY_HOOKS_KEEP_GOING=true` env var, MUST forward the keep-going signal to both `hooks_fast.sh` and `hooks_strict.sh`, and MUST continue to invoke `hooks_strict.sh` after `hooks_fast.sh` returns non-zero EXACTLY WHEN keep-going is active.
- FR-004 In keep-going mode, `hooks_fast.sh` MUST run pre-commit (`pre-commit run --all-files`) as the first step in fail-fast semantics; if pre-commit reports failure (which on this codebase typically reflects file mutations performed by hooks), `hooks_fast.sh` MUST abort the keep-going run before any downstream check executes and MUST exit non-zero. Rationale: pre-commit MUST be assumed to rewrite files, and downstream checks observing the post-mutation tree would produce results that no longer correspond to the original input.
- FR-005 In keep-going mode, after pre-commit succeeds, `hooks_fast.sh` MUST execute every downstream independent check (shellcheck, `quality-root-dir-prelude-check`, `quality-infra-shell-source-graph-check`, `quality-sdd-check-all`, conditional `quality-spec-pr-ready`, `quality-docs-lint`, conditional `quality-ci-check-sync`, `quality-docs-check-changed`, `quality-test-pyramid`, `infra-validate`, `infra-contract-test-fast`) regardless of prior failures, capture each check's exit status and a tail of its captured output, and emit a consolidated summary block at the end.
- FR-006 In keep-going mode, `hooks_strict.sh` MUST execute every independent check (`infra-audit-version`, `apps-audit-versions`, conditional `blueprint-template-smoke`) regardless of prior failures and emit the same consolidated summary block format.
- FR-007 The consolidated summary block emitted by both scripts in keep-going mode MUST be prefixed with the literal marker line `===== quality-hooks keep-going summary =====`, MUST list each executed check with its status (`PASS` or `FAIL`) and runtime in seconds, and MUST be followed by EXACTLY ONE OF the trailer lines `===== all checks passed =====` (when zero checks failed) or `===== N check(s) failed =====` (when N > 0 checks failed).
- FR-008 In keep-going mode, scripts MUST exit `0` if and only if every executed check passed; otherwise they MUST exit `1`. Aggregating across `hooks_run.sh` (fast + strict), the combined exit MUST be `0` only when every check in both phases passed and pre-commit passed.
- FR-009 Default behavior (no `--keep-going` flag, env var unset or not equal to `true`) MUST be byte-identical to the pre-change scripts: each check runs via `run_cmd`, the first non-zero exit aborts the script via `set -e`, no summary block is printed, and exit codes match prior behavior. The `--keep-going` flag MUST be the only addition observable in default invocations.
- FR-010 The `--help` output of `hooks_fast.sh`, `hooks_strict.sh`, and `hooks_run.sh` MUST document the `--keep-going` flag and the `QUALITY_HOOKS_KEEP_GOING` env var.

### Non-Functional Requirements (Normative)
- NFR-SEC-001 The keep-going implementation MUST NOT introduce shell injection vectors via the captured per-check output (output is captured to a file, then printed verbatim; no eval, no expansion). The implementation MUST NOT widen filesystem permissions or write outside `${TMPDIR:-/tmp}` for transient capture files; capture files MUST be removed in an `EXIT` trap.
- NFR-OBS-001 In keep-going mode, each check's start MUST be logged via `log_info` with the check name; on failure, the captured stderr tail (last 40 lines, configurable via `QUALITY_HOOKS_KEEP_GOING_TAIL_LINES` integer env var, default `40`) MUST be re-emitted to the script's stderr immediately after the check completes so the failure is visible in scrollback as well as in the final summary. A `log_metric "quality_hooks_keep_going_total" "1" "status=success|failure phase=fast|strict failed_checks=<count>"` MUST be emitted at the end of each script run in keep-going mode.
- NFR-REL-001 If a check process is killed by signal (e.g. `SIGTERM`, `SIGINT`) during keep-going execution, the script MUST treat the surrounding wait as terminal: the EXIT trap MUST run and the script MUST exit non-zero; in-flight per-check capture files MUST be cleaned up. Subsequent checks MUST NOT execute after a fatal signal.
- NFR-OPS-001 `--keep-going` MUST be discoverable via `--help` for all three scripts (FR-010); the make target `help` output (existing `## Run …` doc-comments in `make/blueprint.generated.mk`) MUST be amended to mention the env var on `quality-hooks-fast`, `quality-hooks-strict`, and `quality-hooks-run` so `make help` lists it.

## Normative Option Decision
- Option A: Implement keep-going as a shell helper (`run_check_aggregating`) in a new file `scripts/lib/shell/keep_going.sh` sourced by `hooks_fast.sh`, `hooks_strict.sh`, and `hooks_run.sh`. Each script declares its check list as `name|command` pairs and dispatches via the helper, which captures stdout+stderr to a per-check temp file, records exit status and duration, and at the end prints the summary block. Default mode keeps the existing `run_cmd <thing>` invocations unchanged.
- Option B: Extract each check into its own make target and use `make -k` (keep-going) at the top level. Rely on make's existing aggregation semantics.
- Selected option: OPTION_A
- Rationale: Option B requires re-architecting all current shell-driven check invocations into make targets and depends on make's keep-going behavior, which aggregates exit codes but does not produce a structured per-check summary, does not capture per-check output for tail-replay, does not handle the conditional checks (branch-pattern-gated `quality-spec-pr-ready`, repo-mode-gated `quality-ci-check-sync` and `blueprint-template-smoke`), and does not enforce the pre-commit-first-and-fail-fast invariant from FR-004. Option A keeps the existing single-responsibility shell entry points, isolates aggregation logic in one helper, and preserves byte-identical default behavior.

## Contract Changes (Normative)
- Config/Env contract: new env vars `QUALITY_HOOKS_KEEP_GOING` (`true` enables keep-going; any other value preserves default) and `QUALITY_HOOKS_KEEP_GOING_TAIL_LINES` (positive integer; default `40`).
- API contract: none
- OpenAPI / Pact contract path: none
- Event contract: none
- Make/CLI contract: no new make targets; existing `quality-hooks-fast`, `quality-hooks-strict`, `quality-hooks-run` make recipes MUST forward both positional arguments and the `QUALITY_HOOKS_KEEP_GOING` env var to the underlying script. Help-text comments updated.
- Docs contract: a new short section in `docs/blueprint/operations/quality-gates.md` (or the closest existing operations doc, to be confirmed during Document phase) describing `--keep-going` and the env var; updated ADR.

## Blueprint Upstream Defect Escalation (Normative)
- Upstream issue URL: none
- Temporary workaround path: none
- Replacement trigger: none
- Workaround review date: none

## Normative Acceptance Criteria
- AC-001 MUST: invoking `bash scripts/bin/quality/hooks_fast.sh` with no flag and `QUALITY_HOOKS_KEEP_GOING` unset on a tree that has two independent failing checks (e.g. a deliberately-broken shellcheck target plus a failing `quality-docs-lint`) exits non-zero after the first failure, does NOT execute subsequent checks, and emits no `===== quality-hooks keep-going summary =====` marker (default fail-fast preserved).
- AC-002 MUST: invoking `bash scripts/bin/quality/hooks_fast.sh --keep-going` on the same tree from AC-001 executes both failing checks and every other downstream check, emits the summary block listing all checks with PASS/FAIL status, and exits non-zero with the trailing `===== N check(s) failed =====` line where N matches the failing-check count.
- AC-003 MUST: setting `QUALITY_HOOKS_KEEP_GOING=true bash scripts/bin/quality/hooks_fast.sh` (no flag) produces results equivalent to AC-002 (env var triggers keep-going).
- AC-004 MUST: in keep-going mode, if pre-commit (`pre-commit run --all-files`) fails, `hooks_fast.sh` aborts before any downstream check is executed, no summary block is emitted (because no downstream check ran), and the exit code is non-zero.
- AC-005 MUST: `bash scripts/bin/quality/hooks_run.sh --keep-going` invokes `hooks_fast.sh --keep-going` and, only if pre-commit passed (regardless of whether downstream fast checks failed), then invokes `hooks_strict.sh --keep-going`; the combined summary across phases is reported by each script independently; the run exits `0` only if every check in both phases passed and pre-commit passed.
- AC-006 MUST: `bash scripts/bin/quality/hooks_fast.sh --help` mentions `--keep-going` and `QUALITY_HOOKS_KEEP_GOING`; same for `hooks_strict.sh` and `hooks_run.sh`.
- AC-007 MUST: a unit test for `scripts/lib/shell/keep_going.sh` (`tests/blueprint/test_quality_hooks_keep_going.py` or equivalent shellspec/bats file) verifies: (a) aggregation across N synthetic checks reports correct PASS/FAIL counts; (b) per-check captured output tail is re-emitted to stderr; (c) `QUALITY_HOOKS_KEEP_GOING_TAIL_LINES` env var changes the tail length; (d) default (no env var, no flag) does not source the helper's aggregation path.
- AC-008 MUST: `make quality-hooks-fast QUALITY_HOOKS_KEEP_GOING=true` propagates the env var through the make recipe to the script; `make quality-hooks-run QUALITY_HOOKS_KEEP_GOING=true` does the same for the composite target.

## Informative Notes (Non-Normative)
- Context: An agent inner loop on `make quality-hooks-run` typically encounters 1–4 independent failures per spec slice. Today each surfaces sequentially, costing a full re-run per fix. Aggregation collapses N runs into 1 + (1 final verification run). On observed mid-size specs this is a 3–5× speedup of the inner verification loop and a comparable reduction in token use.
- Tradeoffs: Aggregated reports can include cascading false positives when a single root cause produces multiple downstream failures. The recommended workflow (operations doc + ADR) is to fix the most fundamental failure first and re-run, rather than mass-applying fixes for every reported item. Pre-commit fail-fast (FR-004) prevents the worst case (file mutations changing downstream tree state).
- Clarifications: none

## Explicit Exclusions
- Excluded item 1: Changing the default behavior of `quality-hooks-fast` / `quality-hooks-strict` / `quality-hooks-run` is out of scope. CI and pre-commit invocations remain fail-fast.
- Excluded item 2: Aggregating pre-commit's individual hook failures inside pre-commit itself is out of scope. Pre-commit already has its own internal aggregation (`pre-commit run --all-files` reports all hooks); we treat its overall exit code as a single fail-fast signal because it can mutate files.
- Excluded item 3: Parallel execution of independent checks is out of scope. Aggregation is sequential. Parallelism is a separate optimization that can build on this foundation later.
- Excluded item 4: Building a structured (JSON) machine-readable summary for the agent harness is out of scope for v1. The plain-text summary block is the v1 contract; a JSON variant can be added later if agent harness integration requires it.
