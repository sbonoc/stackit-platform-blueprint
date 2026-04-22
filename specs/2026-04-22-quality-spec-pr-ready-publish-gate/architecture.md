# Architecture

## Context
- Work item: 2026-04-22-quality-spec-pr-ready-publish-gate
- Owner: bonos
- Date: 2026-04-22

## Stack and Execution Model
- Backend stack profile: python_plus_fastapi_pydantic_v2
- Frontend stack profile: vue_router_pinia_onyx
- Test automation profile: pytest_vitest_playwright_pact
- Agent execution model: specialized-subagents-isolated-worktrees

## Problem Statement
- What needs to change and why: `quality-sdd-check` validates only the five SDD readiness-gate files (spec.md, architecture.md, context_pack.md, traceability.md, graph.json, evidence_manifest.json). The four publish-gate files (plan.md, tasks.md, hardening_review.md, pr_context.md) have no machine-readable validation, so scaffold placeholders can ship in PRs undetected — as confirmed by the previous work item (issue-118-137) where all four files shipped with all-placeholder content.
- Scope boundaries: new script `scripts/bin/quality/check_spec_pr_ready.py`; new make target `quality-spec-pr-ready` in the blueprint makefile template and its rendered output; conditional invocation in `hooks_fast.sh`; test file `tests/blueprint/test_spec_pr_ready.py`.
- Out of scope: modifying `check_sdd_assets.py`; validating readiness-gate files; semantic completeness checks; scanning files outside the four publish-gate files.

## Bounded Contexts and Responsibilities
- Context A (publish-gate validation): `check_spec_pr_ready.py` owns structural/placeholder validation of the four publish-gate files. It is the single authority on what constitutes a "PR-ready" publish artifact set. It derives the active spec dir from `SPEC_SLUG` env var or from the git branch name.
- Context B (hooks integration): `hooks_fast.sh` owns the local quality gate orchestration. It invokes `quality-spec-pr-ready` conditionally based on branch pattern and spec dir presence; it does not duplicate any validation logic.

## High-Level Component Design
- Domain layer: Each of the four publish-gate files has a distinct check function in `check_spec_pr_ready.py`: `_check_tasks`, `_check_plan`, `_check_hardening_review`, `_check_pr_context`. Each returns a list of `Violation` instances.
- Application layer: `main()` in `check_spec_pr_ready.py` resolves the spec dir, runs all four check functions, prints each violation prefixed with `[quality-spec-pr-ready]`, and exits 1 if any violation was found. Spec dir resolution is isolated in `_resolve_spec_dir(repo_root, spec_slug_env, branch)`.
- Infrastructure adapters: all file reads use `pathlib.Path.read_text(encoding="utf-8", errors="surrogateescape")`; git branch is read via `subprocess.check_output(["git", "branch", "--show-current"])` only when `SPEC_SLUG` is unset.
- Presentation/API/workflow boundaries: output is line-prefixed error messages to stdout/stderr; exit code is the only machine-readable signal consumed by make and `hooks_fast.sh`.

## Integration and Dependency Edges
- Upstream dependencies: `blueprint/contract.yaml` (indirectly, via `hooks_fast.sh` which calls `blueprint_repo_is_generated_consumer`); scaffold templates in `.spec-kit/templates/blueprint/` define the placeholder labels that the check knows about.
- Downstream dependencies: `make quality-spec-pr-ready` is consumed by `hooks_fast.sh`; the make target must be present in both the template and rendered makefile for `check_sdd_assets.py` to pass (no new assertion added — it checks `spec-scaffold:` not this target).
- Data/API/event contracts touched: `make/blueprint.generated.mk` and `scripts/templates/blueprint/bootstrap/make/blueprint.generated.mk.tmpl` gain the `quality-spec-pr-ready` target.

## Non-Functional Architecture Notes
- Security: all file reads are in-process Python via `pathlib`; no subprocess beyond `git branch --show-current` for branch resolution; no path traversal beyond the resolved spec directory.
- Observability: each violation is printed with `[quality-spec-pr-ready] <file>: <message>` format; exit code is non-zero on any violation; no metrics emitted (local developer tooling path).
- Reliability and rollback: a missing spec dir exits non-zero with a diagnostic; an unresolvable branch exits non-zero; the check can be bypassed by setting `SPEC_SLUG=` to an explicit value pointing at a ready spec dir. Rollback: remove the make target and the `hooks_fast.sh` invocation; the script file can be left in place as it is not auto-executed.
- Monitoring/alerting: none; this is a local developer tooling path.

## Risks and Tradeoffs
- Risk 1: the static label allowlist for scaffold-placeholder detection must be kept in sync with `.spec-kit/templates/blueprint/` scaffold templates. If a template is updated to use a new placeholder label, the check MUST be updated to include it. Mitigation: the allowlist is centrally defined in `check_spec_pr_ready.py`; tests exercise each label variant so template drift produces a test failure rather than a silent miss.
- Tradeoff 1: label-aware detection avoids false positives on intentionally terse single-word fields at the cost of a static label allowlist. A blanket "no empty bullets" rule would reject valid single-word field values. The tradeoff is acceptable because the scaffold templates change infrequently and the allowlist is easy to update.
