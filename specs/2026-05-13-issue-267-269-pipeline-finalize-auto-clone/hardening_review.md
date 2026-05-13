# Hardening Review

## Repository-Wide Findings Fixed

- Finding 1: `BLUEPRINT_UPGRADE_SOURCE` URL form caused fatal Stage 5 abort for all consumers supplying a URL (the documented canonical form). Fixed by URL normalization block in `upgrade_consumer_pipeline.sh` that auto-clones before Stage 1b, so all stages receive a local filesystem path.
- Finding 2: No single canonical post-apply convergence command existed. Consumers required 5+ manual cycles of `quality-hooks-run` and related targets to reach a green state after upgrade apply. Fixed by `blueprint-upgrade-consumer-finalize` (sync pass + verify pass) and pipeline Stage 8+9 replacement.
- Finding 3: `upgrade_consumer.py` always ran an internal `git clone` even when `upgrade_source` was already a pre-cloned local path. Fixed by `source_is_pre_cloned` guard that detects local `.git` directories and skips the redundant clone.

## Observability and Diagnostics Changes

- Logging updates: `upgrade_consumer_finalize.sh` emits `[finalize] <step>: <status>` log lines via `log_info`/`log_error` for every sync and verify target, consistent with the existing `[PIPELINE]` pattern. Operators can now diagnose which specific step failed from the log without reading the full make output.
- Logging updates: `upgrade_consumer_pipeline.sh` emits `[PIPELINE] auto-clone: cloning $upgrade_source@$upgrade_ref → $cloned_source_dir (--depth 1)` and `[PIPELINE] auto-clone: complete` lines for URL-form sources, making the clone operation visible in CI logs.
- Operational diagnostics: summary banner `[finalize] verify: <target>: FAILED (exit <rc>) — finalize aborted.` emitted on first verify-pass failure, directly naming the failing target.
- No new metrics endpoints required; finalize exit code is the observable CI signal.

## Architecture and Code Quality Compliance

- SOLID / Clean Code: finalize script is a thin orchestrator (37 lines of logic) that delegates to existing make targets with no embedded business logic. No new abstractions introduced. Two-pass structure (sync pass: aggregated; verify pass: fail-fast) is a direct sequential loop — no dispatch tables or wrapper functions.
- Clean Architecture: no layering violations. Finalize script calls make targets (infrastructure layer contracts); pipeline script calls finalize (same layer). Engine's skip-clone guard is a pure boolean check on `Path.is_dir()` — no cross-boundary dependency.
- Security: URL prefix allowlist (`https://`, `git@`, `ssh://`, `/`, `./`, `../`) validated before `git clone` invocation. Unknown prefix causes immediate `log_fatal` abort. No shell-metacharacter injection path.
- Cleanup: EXIT trap consolidates both residual-report emission and clone-dir removal in a single `trap` registration, preventing the double-trap override bug that would silently skip cleanup on error paths.
- Test pyramid: 25 new unit tests (7 auto-clone + 18 finalize), all static source assertions in `tests/infra/`. Pyramid ratios unchanged: unit 96.18%, integration 2.99%, e2e 0.83% — well within policy bounds.
- Documentation / diagram consistency: `ADR-20260425-scripted-upgrade-pipeline.md` Mermaid stage diagram updated (Stage 8+9 → `blueprint-upgrade-consumer-finalize`); `SKILL.md` Step 7 updated; pipeline and finalize usage blocks updated.

## Accessibility Gate (Normative — non-UI reviewers mark non-applicable items N/A)

- [x] SC 4.1.2: N/A — CLI tool only, no browser-rendered UI surface.
- [x] SC 2.1.1: N/A — CLI tool only, no browser-rendered UI surface.
- [x] SC 2.4.7: N/A — CLI tool only, no browser-rendered UI surface.
- [x] SC 1.4.1: N/A — CLI tool only, no browser-rendered UI surface.
- [x] SC 3.3.1: N/A — CLI tool only, no browser-rendered UI surface.
- [x] axe-core scan: N/A — no browser-rendered UI surface; NFR-A11Y-001 declared N/A in spec.md.

## Proposals Only (Not Implemented)

- Proposal 1: Deepen clone for ancestry traversal — current `--depth 1` clone is sufficient for Stage 5 `git show` operations but would fail if a future pipeline stage requires `git log` across commit history. Rationale for deferral: no current stage needs ancestry; adding depth only when a future stage requires it avoids unnecessary network cost today.
- Proposal 2: Standalone finalize precondition guard — `blueprint-upgrade-consumer-finalize` aborts with an unhelpful postcheck failure if called before Stage 3–7 artifacts exist (e.g. `artifacts/blueprint/upgrade_apply.json` absent). A `--skip-postcheck` flag or artifact-presence check would improve the standalone UX. Rationale for deferral: the usage block documents the precondition; out-of-scope for this work item.
- Proposal 3: Sync pass target expansion — `quality-docs-sync-all` may not cover all sync targets in future. A dynamic discovery mechanism (reading `quality-sdd-sync-all` deps) would be more robust than the current explicit list. Rationale for deferral: current three-target list is complete; expansion tracked as a follow-up in traceability.md.
