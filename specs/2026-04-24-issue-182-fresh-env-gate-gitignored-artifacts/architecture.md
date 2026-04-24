# Architecture

## Context
- Work item: issue-182 — upgrade_fresh_env_gate: seed gitignored artifacts into clean worktree
- Owner: platform blueprint maintainer
- Date: 2026-04-24

## Stack and Execution Model
- Backend stack profile: bash (shell wrapper) + python3 (report module)
- Frontend stack profile: none
- Test automation profile: pytest integration tests (tests/blueprint/test_upgrade_fresh_env_gate.py)
- Agent execution model: specialized-subagents-isolated-worktrees

## Problem Statement
- What needs to change and why: `upgrade_fresh_env_gate.sh` creates a temporary git worktree via `git worktree add <path> HEAD`. Gitignored files are absent in this worktree by design. The gate then runs `make blueprint-upgrade-consumer-postcheck` inside the worktree; the postcheck requires files under `artifacts/blueprint/` (plan report, apply report, reconcile report) as inputs. Because these files are gitignored and absent in the worktree, the postcheck hard-fails immediately with "missing required input". The gate never reaches its actual CI-equivalence validation logic. The fix is to seed `artifacts/blueprint/` from the working tree into the worktree before invoking make targets.
- Scope boundaries: single shell script (`upgrade_fresh_env_gate.sh`), ~8 lines added. No changes to the Python report module, postcheck script, or make targets.
- Out of scope: postcheck internals, divergence computation, make target signatures, environment variables.

## Bounded Contexts and Responsibilities
- Fresh-env gate shell wrapper (`scripts/bin/blueprint/upgrade_fresh_env_gate.sh`): owns worktree lifecycle (create → seed → run targets → cleanup) and orchestrates the gate sequence.
- Fresh-env gate Python report module (`scripts/lib/blueprint/upgrade_fresh_env_gate.py`): owns divergence computation and JSON report serialization. No changes required.

## High-Level Component Design
- Domain layer: upgrade artifact seeding is a pre-condition step in the gate orchestration — it belongs in the shell wrapper, immediately after worktree creation and before any make targets are invoked.
- Application layer: `cp -r "$consumer_root/artifacts/blueprint" "$worktree_path/artifacts/"` is the complete implementation. No new functions, modules, or abstractions required.
- Infrastructure adapters: standard POSIX `cp` and `mkdir`; no new tool dependencies.
- Presentation/API/workflow boundaries: the gate's external interface (make target, exit code, JSON report schema) is unchanged.

## Integration and Dependency Edges
- Upstream dependencies: `artifacts/blueprint/` produced by prior upgrade steps (`make blueprint-upgrade-consumer` plan + apply); these must exist before the gate is invoked.
- Downstream dependencies: `make blueprint-upgrade-consumer-postcheck` consumes the seeded artifacts inside the worktree. The postcheck is unmodified.
- Data/API/event contracts touched: `docs/blueprint/architecture/execution_model.md` documents the gate flow and MUST be updated to reflect the seeding step.

## Non-Functional Architecture Notes
- Security: `artifacts/blueprint/` contains only JSON/text upgrade report files. No secrets, credentials, or `.env` files reside there by contract. The `cp -r` is scoped to this subdirectory only.
- Observability: `log_info` emitted on seeding (with source + destination paths) and on skip (with reason). The existing `blueprint_upgrade_fresh_env_gate_status_total` metric covers the gate outcome; no new metrics needed.
- Reliability and rollback: the existing `_cleanup_worktree` EXIT trap removes the entire worktree directory unconditionally via `rm -rf`; seeded artifacts are cleaned up by this trap with no additional code. If `cp` fails, `set -euo pipefail` causes the script to exit non-zero, which is the correct failure behavior.
- Monitoring/alerting: no changes to existing alerting surface.

## Risks and Tradeoffs
- Risk 1: If `artifacts/blueprint/` is very large in a future scenario (e.g. many upgrade reports accumulated), `cp -r` could be slow. Mitigation: the directory is bounded by the number of upgrade artifacts per run (3–5 JSON files, few KB total); this is not a realistic concern.
- Tradeoff 1: Seeding copies all of `artifacts/blueprint/`, not only the specific files the postcheck requires. This is intentional: it avoids tight coupling between the gate and the postcheck's internal file expectations, and keeps the seeding logic stable across postcheck evolution.
