# ADR: Issue #182 — Fresh-Env Gate Artifact Seeding

- **Status**: approved
- **Date**: 2026-04-24
- **Issue**: #182
- **Work item**: `specs/2026-04-24-issue-182-fresh-env-gate-gitignored-artifacts/`

## Context

`upgrade_fresh_env_gate.sh` creates a temporary git worktree from `HEAD` via
`git worktree add <path> HEAD` to simulate a fresh CI checkout. Gitignored files
are absent from this worktree by design. The gate then runs
`make blueprint-upgrade-consumer-postcheck` inside the worktree.

The postcheck requires upgrade artifacts under `artifacts/blueprint/` (plan
report, apply report, reconcile report) as inputs. Because these files are
gitignored and absent in a fresh worktree, the postcheck immediately hard-fails
with "missing required input". The gate never reaches its CI-equivalence
validation logic.

## Decision

Seed `artifacts/blueprint/` from the working tree into the temporary worktree
immediately after worktree creation, before any make targets are invoked:

```bash
if [[ -d "$consumer_root/artifacts/blueprint" ]]; then
  log_info "fresh-env gate: seeding blueprint upgrade artifacts into worktree from ${consumer_root}/artifacts/blueprint"
  mkdir -p "$worktree_path/artifacts"
  cp -r "$consumer_root/artifacts/blueprint" "$worktree_path/artifacts/"
else
  log_info "fresh-env gate: artifacts/blueprint not found in working tree — skipping artifact seeding"
fi
```

This accurately models what a CI pipeline does: prior pipeline steps (plan,
apply) produce the artifacts; the postcheck step consumes them in a clean
checkout. The worktree provides the clean file-system state; the seeded
artifacts provide the required inputs.

## Alternatives Considered

**Option B — pass artifact paths as environment variables to make targets**:
would require changes to the shell script, the Makefile, and the postcheck
script, introducing coupling between the gate and the postcheck's internal path
handling. Rejected for higher blast radius and no benefit.

## Consequences

- `upgrade_fresh_env_gate.sh`: ~8-line addition, no other changes.
- `upgrade_fresh_env_gate.py`: no changes — `_EXCLUDE_TOP_DIRS` already
  excludes `artifacts/` from divergence computation.
- Postcheck, make targets, environment variables: no changes.
- Cleanup: the existing `_cleanup_worktree` EXIT trap handles seeded files
  unconditionally via `rm -rf "$worktree_path"`.
- Tests: two new integration test cases added to
  `tests/blueprint/test_upgrade_fresh_env_gate.py`.
