# Architecture

## Context
- Work item: issue-296-workaround-manifest-action-path-check
- Owner: bonos
- Date: 2026-05-15

## Stack and Execution Model
- Backend stack profile: python-tooling-only (no FastAPI; pure Python CLI/checker script)
- Frontend stack profile: none
- Test automation profile: pytest-unit (tests/blueprint/)
- Agent execution model: single-agent

## Problem Statement
- What needs to change and why: A blueprint maintainer can commit a `manifest.yaml` entry with a typo in `action_path` and the error surfaces only at consumer upgrade time — after the release is shipped. A fast-gate CI check that validates all `action_path` values resolve to existing files eliminates this latent defect class at commit time.
- Scope boundaries: `scripts/bin/quality/check_workaround_manifest.py` (new checker), `make/blueprint.generated.mk` (new target + .PHONY), `scripts/templates/blueprint/bootstrap/make/blueprint.generated.mk.tmpl` (mirror), `scripts/bin/quality/hooks_fast.sh` (wiring), `tests/blueprint/test_workaround_manifest_check.py` (new pytest test).
- Out of scope: Semantic validation of action file content (YAML schema, patch syntax). Wiring into `quality-hooks-run` or `quality-ci-blueprint`. Checking `landed_in` field validity.

## Bounded Contexts and Responsibilities

- **Quality gate layer** (`scripts/bin/quality/check_workaround_manifest.py`): Reads `manifest.yaml` from the workaround catalogue, resolves all `action_path` values relative to the skill root, and exits non-zero for any missing file. Stateless — no side effects.
- **Make target layer** (`make/blueprint.generated.mk`): Exposes `quality-workaround-manifest-check` as a named target; wires into `quality-hooks-fast` via `run_check`. No logic in the Makefile itself.
- **Test layer** (`tests/blueprint/test_workaround_manifest_check.py`): Invokes the checker as a subprocess in both a passing (all files present) and failing (one file missing) scenario, plus a live-manifest integration assertion against the real v1.10.0 entries.

## High-Level Component Design
- Domain layer: None — this is pure tooling; no domain model.
- Application layer: `check_workaround_manifest.py` — reads YAML, iterates entries, checks file existence, collects violations, reports and exits.
- Infrastructure adapters: `pathlib.Path.exists()` for file existence; `yaml.safe_load` for manifest parsing. No network I/O.
- Presentation/API/workflow boundaries: CLI exit code + stderr/stdout output. Make target wrapper. `hooks_fast.sh` `run_check` registration.

```flowchart TD
    A[hooks_fast.sh run_check] --> B[make quality-workaround-manifest-check]
    B --> C[uv run python3 check_workaround_manifest.py]
    C --> D[yaml.safe_load manifest.yaml]
    D --> E{For each entry action_path}
    E --> F[Resolve: skill_root / action_path]
    F --> G{Path.exists?}
    G -- yes --> E
    G -- no --> H[Collect violation]
    E --> I{Any violations?}
    I -- no --> J[stdout: all paths valid, exit 0]
    I -- yes --> K[stderr: missing paths, exit 1]
```

## Integration and Dependency Edges
- Upstream dependencies: `.agents/skills/blueprint-consumer-upgrade/workarounds/manifest.yaml` (read-only input); `pyyaml` (already in project `uv` environment).
- Downstream dependencies: `scripts/bin/quality/hooks_fast.sh` reads the exit code of the Make target.
- Data/API/event contracts touched: Make/CLI contract — `quality-workaround-manifest-check` target added.

## Non-Functional Architecture Notes
- Security: Checker reads file metadata only (`Path.exists()`); no file content execution. No network access. No subprocess invocation of action files.
- Observability: stdout success line + stderr per-violation lines, both prefixed with `[quality-workaround-manifest-check]`. Consistent with existing checker convention.
- Reliability and rollback: Checker is stateless — rollback is `git revert` of the three changed files (checker script, Makefile target, hooks_fast.sh). No persistent state.
- Monitoring/alerting: N/A — CI gate only; no runtime monitoring.

## Risks and Tradeoffs
- Risk 1: `manifest.yaml` YAML schema changes could cause the checker to miss entries. Mitigation: checker iterates the documented `versions → <tag> → workarounds → action_path` path; any schema change would break the checker visibly (KeyError), not silently.
- Tradeoff 1: Standalone checker (`check_workaround_manifest.py`) vs. extending `check_sdd_assets.py`. Standalone wins on separation of concerns — the workaround catalogue has no dependency on SDD assets. See ADR for full rationale.
