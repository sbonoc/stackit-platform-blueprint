# Architecture

## Context
- Work item: 2026-04-22-issue-131-blueprint-uplift-status
- Owner: bonos
- Date: 2026-04-22

## Stack and Execution Model
- Backend stack profile: python_plus_fastapi_pydantic_v2
- Frontend stack profile: vue_router_pinia_onyx
- Test automation profile: pytest_vitest_playwright_pact
- Agent execution model: specialized-subagents-isolated-worktrees

## Problem Statement

Generated-consumer repos track upstream blueprint capabilities as unchecked items in `AGENTS.backlog.md`. When the upstream issue closes (capability lands), the consumer must manually check off those items and adopt the capability. Today there is no automated signal: convergence debt accumulates silently, discoverable only by manually querying GitHub and scanning the backlog.

## Bounded Contexts

- **Blueprint governance layer** — owns `scripts/bin/blueprint/` and `scripts/lib/blueprint/`; this command belongs there.
- **Generated-consumer repo** — owns `AGENTS.backlog.md` and `blueprint/repo.init.env`; the command reads from these without writing to them.
- **GitHub API** — accessed via `gh issue view`; read-only.

## Component Design

```
uplift_status.sh (shell wrapper)
  ├── blueprint_load_env_defaults()     → resolves BLUEPRINT_GITHUB_ORG/REPO → BLUEPRINT_UPLIFT_REPO
  ├── shell_normalize_bool_truefalse()  → BLUEPRINT_UPLIFT_STRICT → --strict flag
  ├── run_cmd python3 uplift_status.py  → main logic
  └── emit_uplift_metrics()             → reads artifact, emits log_metric lines

uplift_status.py (Python core)
  ├── _parse_backlog(path, repo)        → list[UpliftEntry]  (pure, no I/O except file read)
  ├── _query_issue_state(id, repo)      → "OPEN"|"CLOSED"|"UNKNOWN"  (gh subprocess)
  ├── _build_report(entries, states, …) → dict  (pure)
  ├── _write_json(path, payload)        → artifacts/blueprint/uplift_status.json
  ├── _print_table(report)              → human-readable stdout
  └── _emit_metrics(report)             → key=value stdout for shell consumption

artifacts/blueprint/uplift_status.json  → state artifact consumed by metrics emitter
```

## Integration Edges

- `blueprint/repo.init.env` — loaded by `blueprint_load_env_defaults`; provides `BLUEPRINT_GITHUB_ORG` and `BLUEPRINT_GITHUB_REPO` as defaults for `BLUEPRINT_UPLIFT_REPO`.
- `AGENTS.backlog.md` — read-only; parsed by `_parse_backlog`.
- `gh issue view` — called once per unique tracked issue; result cached in `issue_states` dict for the run.
- `make/blueprint.generated.mk` + template — `blueprint-uplift-status` target distributes the command to all generated-consumer repos on next upgrade.

## NFR Notes

- **Security**: `gh` is invoked with explicit `--repo`; no ambient token scopes are widened beyond read-only issue access.
- **Reliability**: missing backlog returns zero entries without error; `gh` failure is recorded as `UNKNOWN` and `query_failures` increment; artifact is always written.
- **Observability**: `log_metric` lines emitted for all aggregate fields; artifact is machine-readable JSON with `timestamp_utc`.
- **Operability**: `--help` on the shell wrapper documents all env vars; `_issue_states_override` parameter on `main()` enables test-time injection without subprocess mocking at the module level.
