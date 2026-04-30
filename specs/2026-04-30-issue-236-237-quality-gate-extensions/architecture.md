# Architecture

## Context
- Work item: issue-236-237-quality-gate-extensions (Issues #236, #237)
- Owner: Software Engineer
- Date: 2026-04-30

## Stack and Execution Model
- Backend stack profile: N/A — blueprint tooling (Makefile, pre-commit YAML, Python contract tests)
- Frontend stack profile: N/A — no UI
- Test automation profile: pytest contract assertions (test_quality_contracts.py)
- Agent execution model: specialized-subagents-isolated-worktrees

## Problem Statement
- What needs to change and why: Two gaps in the blueprint quality gate chain. (1) No local pre-push gate catches pnpm lockfile drift before it fails CI at bootstrap (Issue #236). (2) No upgrade-safe consumer extension point exists for custom test tiers — consumers add raw hooks/steps that create merge conflicts on every blueprint upgrade (Issue #237).
- Scope boundaries: Blueprint tooling and governance only. Template files and Makefile recipe additions. No consumer application code, no STACKIT managed services, no Kubernetes changes.
- Out of scope: Consumer test-tier implementations; changes to consumer `platform.mk` or `ci.yml`.

## Bounded Contexts and Responsibilities
- Blueprint (template-source): Owns `.pre-commit-config.yaml` bootstrap template, `blueprint.generated.mk.tmpl`, and `make/blueprint.generated.mk`. Delivers hooks and stubs to consumers on upgrade.
- Consumer (generated-consumer): Owns `platform.mk` and may override `quality-consumer-pre-push` and `quality-consumer-ci` there. Never touches `blueprint.generated.mk` directly.

## High-Level Component Design
- Domain layer: N/A — pure tooling
- Application layer: N/A
- Infrastructure adapters: N/A
- Presentation/API/workflow boundaries: N/A; quality gate chain is the primary "boundary" — see ADR flowchart

## Integration and Dependency Edges
- Upstream dependencies: `pnpm` CLI (consumer devDependency); `pre-commit` (already required)
- Downstream dependencies: `quality-ci-blueprint` recipe calls `quality-consumer-ci` (new); `pre-push` hooks call `pnpm install` and `make quality-consumer-pre-push` (new)
- Data/API/event contracts touched: Make/CLI contract — two new `.PHONY` targets; `.pre-commit-config.yaml` bootstrap template — two new hooks

## Non-Functional Architecture Notes
- Security: No secret handling, authn/authz, or privilege changes.
- Observability: No new metrics, logs, or traces. The pre-push hook exits with `pnpm install` output (existing pnpm behavior).
- Reliability and rollback: All changes additive. Rollback: `git revert` the blueprint upgrade commit in the consumer repo. The stub targets are no-ops so partial adoption (stubs present but not overridden) is safe.
- Monitoring/alerting: None required.

## Risks and Tradeoffs
- Risk 1: `pnpm install --frozen-lockfile --prefer-offline` fails if the local pnpm store is incomplete (e.g. after `pnpm store prune`). In that case the consumer must run `pnpm install` with network access first. This is equivalent to the CI failure today — the pre-push gate surfaces the same issue locally rather than later.
- Tradeoff 1: Consumer pre-push extension loses `files:` pattern filtering. Acceptable — documented in spec.md, and the consumer can implement changed-file checks inside the `quality-consumer-pre-push` target body.
