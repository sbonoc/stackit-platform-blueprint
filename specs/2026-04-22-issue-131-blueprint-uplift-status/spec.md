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
- ADR path: docs/blueprint/architecture/decisions/ADR-20260422-issue-131-blueprint-uplift-status.md
- ADR status: approved

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
- Business outcome: Eliminate hidden convergence debt in generated-consumer repos by providing a blueprint-native `make blueprint-uplift-status` command that continuously answers which tracked upstream blueprint issues are now CLOSED, which local backlog lines still reference them as unchecked, and which convergence actions are required — all standardized by the blueprint so no consumer re-implements it divergently.
- Success metric: Running `make blueprint-uplift-status` in a generated-consumer repo with tracked blueprint issues reports per-issue classification (required/aligned/none), writes `artifacts/blueprint/uplift_status.json`, and exits non-zero in strict mode when action is required. Running it with no tracked issues exits 0 with `tracked_total=0`.

## Normative Requirements

### Functional Requirements (Normative)
- FR-001 MUST parse `AGENTS.backlog.md` (or `BLUEPRINT_UPLIFT_BACKLOG_PATH`) for unchecked Markdown checkbox lines (`^\s*- \[ \]`) that contain at least one Markdown issue link of the form `[#NNN](https://github.com/<org>/<repo>/issues/NNN)` where `<org>/<repo>` matches `BLUEPRINT_UPLIFT_REPO`; checked lines (`- [x]`) MUST be ignored; header lines with no issue link MUST be ignored.
- FR-002 MUST query each unique referenced issue state via `gh issue view <id> --repo <uplift_repo> --json state --jq .state`; a non-zero exit code or unrecognized state value MUST be recorded as `UNKNOWN` and counted in `query_failures`.
- FR-003 MUST classify each unique tracked issue as exactly one of: `required` (state=CLOSED and at least one unresolved backlog line remains), `aligned` (state=CLOSED and zero unresolved lines remain), or `none` (state=OPEN or UNKNOWN).
- FR-004 MUST write a JSON state artifact to `BLUEPRINT_UPLIFT_STATUS_PATH` (default `artifacts/blueprint/uplift_status.json`) containing all fields specified in NFR-OBS-001.
- FR-005 MUST print a human-readable per-issue table to stdout unless `--emit-metrics` is passed, in which case key=value metric lines MUST be printed instead for shell consumption.
- FR-006 MUST accept `--strict` flag (and `BLUEPRINT_UPLIFT_STRICT=true` env var wired by the shell wrapper); in strict mode MUST exit non-zero when `action_required_count > 0` OR `query_failures > 0` OR `unknown_count > 0`.
- FR-007 MUST default `BLUEPRINT_UPLIFT_REPO` to `$BLUEPRINT_GITHUB_ORG/$BLUEPRINT_GITHUB_REPO` (loaded by `blueprint_load_env_defaults` from `blueprint/repo.init.env`); the shell wrapper MUST fail with a clear message when the resolved value is empty or contains a bare `/`.
- FR-008 The `blueprint-uplift-status` make target MUST be present in both `scripts/templates/blueprint/bootstrap/make/blueprint.generated.mk.tmpl` and the regenerated `make/blueprint.generated.mk`.

### Non-Functional Requirements (Normative)
- NFR-SEC-001 All file reads MUST be in-process Python via `pathlib`; no shell expansion beyond the `gh` subprocess call; `gh` is invoked with explicit `--repo` to prevent ambient credential leakage.
- NFR-OBS-001 The JSON artifact MUST contain: `uplift_repo`, `backlog_path`, `strict_mode`, `tracked_total`, `open_count`, `closed_count`, `unknown_count`, `aligned_closed_count`, `action_required_count`, `action_required_issues`, `query_failures`, `timestamp_utc`, `issues` (per-issue list with `issue_id`, `state`, `unresolved_lines`, `classification`), `status`.
- NFR-REL-001 A missing or unreadable backlog file MUST return zero entries without error (non-fatal); a missing `gh` binary MUST surface as a `query_failures` increment, not a crash.
- NFR-OPS-001 The shell wrapper MUST emit stable metrics via `log_metric` for `tracked_total`, per-state issue counts, `action_required_count`, and `query_failures`.

## Normative Option Decision
- Option A: Python core (`scripts/lib/blueprint/uplift_status.py`) invoked by a thin shell wrapper (`scripts/bin/blueprint/uplift_status.sh`) with the same pattern as `upgrade_readiness_doctor.sh` / `.py`.
- Option B: Pure shell script using `gh` and `grep`/`awk` for backlog parsing.
- Selected option: OPTION_A
- Rationale: Python provides reliable regex-based Markdown link parsing, structured JSON artifact output, testable pure functions, and `--emit-metrics` / `--strict` flag handling without fragile shell string manipulation.

## Contract Changes (Normative)
- Config/Env contract: `BLUEPRINT_UPLIFT_REPO`, `BLUEPRINT_UPLIFT_BACKLOG_PATH`, `BLUEPRINT_UPLIFT_STATUS_PATH`, `BLUEPRINT_UPLIFT_STRICT` env vars accepted by shell wrapper and Python script.
- API contract: none
- Event contract: none
- Make/CLI contract: new target `blueprint-uplift-status` added to both makefile files.
- Docs contract: new entry in `docs/reference/generated/core_targets.generated.md`; ADR added.

## Blueprint Upstream Defect Escalation (Normative)
- Upstream issue URL: none
- Temporary workaround path: none
- Replacement trigger: none
- Workaround review date: none

## Normative Acceptance Criteria
- AC-001 MUST: `_parse_backlog` returns one entry per unchecked Markdown issue link matching `BLUEPRINT_UPLIFT_REPO`; checked lines and header lines without links produce zero entries.
- AC-002 MUST: `_query_issue_state` returns `OPEN`, `CLOSED`, or `UNKNOWN`; a non-zero `gh` exit or exception produces `UNKNOWN`.
- AC-003 MUST: `_build_report` classifies issues as `required`/`aligned`/`none` and counts `action_required_count`, `aligned_closed_count`, `unknown_count`, `query_failures` correctly.
- AC-004 MUST: strict mode exits non-zero when `action_required_count > 0`; exits zero when all tracked issues are `OPEN`.
- AC-005 MUST: zero tracked issues exits 0 with `tracked_total=0` and writes a valid artifact.
- AC-006 MUST: `blueprint-uplift-status` target is present in both makefile files.
- AC-007 MUST: all tests in `tests/blueprint/test_uplift_status.py` pass.

## Informative Notes (Non-Normative)
- Context: Generated-consumer repos use Markdown link syntax `[#NNN](https://github.com/org/repo/issues/NNN)` on indented unchecked lines inside group blocks. The parser must handle indentation and group headers with no issue links.
- Tradeoffs: Querying `gh` per issue adds network latency; since the command is on-demand (not wired into `hooks_fast.sh`), this is acceptable.
- Clarifications: none

## Explicit Exclusions
- `hooks_fast.sh` integration is out of scope; the command is on-demand only.
- Semantic analysis of whether a consumer has actually adopted a closed capability is out of scope; only structural backlog line state is checked.
