# Architecture

## Context
- Work item: 2026-04-23-issue-163-fresh-env-smoke-gate
- Owner: sbonoc
- Date: 2026-04-23

## Stack and Execution Model
- Backend stack profile: python_scripting_plus_bash (Python stdlib + subprocess; no web framework)
- Frontend stack profile: none
- Test automation profile: pytest
- Agent execution model: single-agent

## Problem Statement
- What needs to change and why: The existing upgrade smoke gate runs in the developer's working tree, where files previously created by `ensure_file_with_content` and `ensure_infra_template_file` persist across runs. CI starts from a clean checkout — those files are absent. This creates a systematic class of upgrade failures that are invisible locally but fail in CI: the upgrade validates green on the developer's machine, the PR lands, and CI fails. The developer has no signal during the upgrade that CI will behave differently.
- Scope boundaries: The change adds a new gate step (`blueprint-upgrade-fresh-env-gate`) that runs after `blueprint-upgrade-consumer-postcheck` exits 0. The gate creates a temporary git worktree from the upgrade branch HEAD, runs `make infra-validate` and `make blueprint-upgrade-consumer-postcheck` inside it, diffs the resulting file state against the post-apply working tree on failure, and discards the worktree on exit.
- Out of scope: Opt-out flag, time budget enforcement, sanitized environment, non-file divergence detection, transitive bootstrap dependency analysis.

## Bounded Contexts and Responsibilities
- Upgrade orchestration context (existing): The upgrade skill (`blueprint-consumer-upgrade`) owns the upgrade command sequence. The fresh-env gate is an additive step appended to the end of the sequence; it does not modify any existing step.
- Fresh-env gate context (new): Owns worktree lifecycle (create, run, diff, discard), structured JSON report emission, metric emission, and inline stdout progress. Bounded to `scripts/bin/blueprint/upgrade_fresh_env_gate.sh` and `scripts/lib/blueprint/upgrade_fresh_env_gate.py`.

## High-Level Component Design
- Domain layer: Gate logic — worktree creation (`git worktree add`), target execution (`make infra-validate`, `make blueprint-upgrade-consumer-postcheck`), file-state diff (compare worktree file set vs working tree), and result classification (pass|fail|error).
- Application layer: `scripts/lib/blueprint/upgrade_fresh_env_gate.py` — Python module responsible for the diff logic and JSON report serialization. Called by the shell wrapper with worktree path, working tree path, target exit codes, and error context.
- Infrastructure adapters: `scripts/bin/blueprint/upgrade_fresh_env_gate.sh` — shell wrapper responsible for worktree lifecycle (`git worktree add`, EXIT trap with `git worktree remove --force`), sequential target execution, metric emission, and delegating report writing to the Python module.
- Presentation/API/workflow boundaries: New make target `blueprint-upgrade-fresh-env-gate` in `make/blueprint.generated.mk` (and template counterpart). Called explicitly by the upgrade skill after `blueprint-upgrade-consumer-postcheck`. Contract declared in `blueprint/contract.yaml`.

## Integration and Dependency Edges
- Upstream dependencies: `make blueprint-upgrade-consumer-postcheck` exits 0 (gate precondition); `git worktree` support in the consumer repo environment (already required by upgrade flow); `python3` on PATH (already required by postcheck).
- Downstream dependencies: None — gate is terminal in the upgrade sequence.
- Data/API/event contracts touched: New env var `BLUEPRINT_UPGRADE_FRESH_ENV_GATE_PATH` (default: `artifacts/blueprint/fresh_env_gate.json`). New make target `blueprint-upgrade-fresh-env-gate`. `blueprint/contract.yaml` updated with new required target. Upgrade skill SKILL.md command sequence updated.

## Non-Functional Architecture Notes
- Security: Worktree is created from committed HEAD only — no uncommitted content is executed. Environment variable inheritance is acceptable; same trust boundary as the parent upgrade run.
- Observability: JSON artifact `artifacts/blueprint/fresh_env_gate.json` with fields `status`, `worktree_path`, `targets_run`, `divergences`, `error`, `exit_code`. Shell wrapper emits metric `blueprint_upgrade_fresh_env_gate_status_total{status=pass|fail|error}` via `log_metric` (same pattern as postcheck wrapper).
- Reliability and rollback: EXIT trap unconditionally removes the worktree. Gate is idempotent — re-runnable on the same HEAD. Gate does not mutate the working tree. If the gate is the only failing step, the developer re-runs the full upgrade sequence after fixing the bootstrap regression.
- Monitoring/alerting: `blueprint_upgrade_fresh_env_gate_status_total` metric is the primary signal. No additional dashboard or alert is required beyond what exists for postcheck.

## Risks and Tradeoffs
- Risk 1: Worktree creation adds overhead proportional to the time required to run both targets in a clean environment. On slow machines or large repos, this may make the upgrade sequence noticeably longer.
- Mitigation 1: No time budget is enforced. This is consistent with the existing postcheck contract. A follow-up can introduce a configurable timeout if users report friction.
- Risk 2: `make blueprint-upgrade-consumer-postcheck` running inside the worktree may produce artifact files in the worktree's `artifacts/` directory. If the worktree removal fails, these artifacts persist on disk.
- Mitigation 2: EXIT trap uses `--force` flag to ensure removal even if artifact files remain. If the trap fails (e.g., signal 9), `git worktree prune` cleans up orphaned metadata.
- Tradeoff 1: Full environment inheritance means the fresh-env gate is not a hermetic CI simulation — it only simulates the file-system starting state, not the full CI environment (e.g., CI-specific env vars, different PATH). This is the stated scope of the issue and is accepted for MVP.
