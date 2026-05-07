# Hardening Review

## Repository-Wide Findings Fixed

- Finding 1: GNU Make `overriding commands` warnings in consumer repos — Blueprint-managed
  targets `spec-scaffold` and `blueprint-uplift-status` previously used hardcoded recipe
  values, forcing consumers to re-define the entire target in `platform.mk` to change the
  default track or script path. Make emits `overriding commands for target` warnings on
  every re-definition. Fixed by exposing `SPEC_SCAFFOLD_DEFAULT_TRACK ?= blueprint` and
  `BLUEPRINT_UPLIFT_STATUS_SCRIPT ?= scripts/bin/blueprint/uplift_status.sh` in
  `blueprint.generated.mk` and its template source; consumers set `:=` in `platform.mk`
  without redefining the target, eliminating the warning entirely.

## Observability and Diagnostics Changes

- **Metrics/logging/tracing updates:** None. This is a Makefile variable-only change with
  zero runtime execution path impact. No metrics, structured log fields, or trace spans
  are created or modified.
- **Operational diagnostics updates:** None. `make help` output for both affected targets
  has been extended to document the override-point variables
  (`SPEC_SCAFFOLD_DEFAULT_TRACK`, `BLUEPRINT_UPLIFT_STATUS_SCRIPT`), improving
  discoverability but not changing operational behavior.

## Architecture and Code Quality Compliance

- **SOLID / Clean Architecture:** The `?=` / `:=` pattern is the GNU Make analogue of the
  Open/Closed principle — targets are open for variable-level configuration and closed for
  structural modification. No coupling introduced; consumer `platform.mk` continues to be
  the single consumer extension point.
- **Clean Code:** Two `?=` variable declarations, two recipe token substitutions, two help
  string updates — minimal diff, maximum legibility. Defaults match previous hardcoded
  values exactly (backward compatible by construction).
- **Test automation and pyramid:** 2 new `assertIn` contract assertions added in
  `tests/blueprint/test_quality_contracts.py` (methods
  `test_blueprint_generated_mk_template_exposes_override_point_variables` and
  `test_generated_makefile_exposes_override_point_variables`). Pyramid ratios after addition:
  unit 95.02% (min > 60%), integration 3.90% (max ≤ 30%), e2e 1.08% (max ≤ 10%) — all
  within bounds. `quality-docs-check-changed` confirms compliance.
- **Documentation/diagram/CI/skill consistency:**
  - ADR-20260430-issue-241-make-override-warnings.md — status: approved; documents Option A
    rationale and include-order mechanics.
  - `docs/reference/generated/core_targets.generated.md` — both override-point variables
    now appear in the public command reference help strings.
  - Template (`.tmpl`) and generated file (`blueprint.generated.mk`) synchronized via
    `make blueprint-render-makefile` in both the implementation slice and the docs slice.
  - `python3 scripts/lib/docs/sync_blueprint_template_docs.py` — 13 files already
    synchronized, 0 updated (no narrative doc sync required).
  - No CI pipeline changes required. No skill runbook changes required.

## Proposals Only (Not Implemented)

- Proposal 1: Extend `?=` override-point pattern to other blueprint-managed targets —
  `spec-scaffold` and `blueprint-uplift-status` are the two targets explicitly reported in
  issue #241. Other targets that consumers may re-define in `platform.mk` are not inventoried
  in this work item; the same `?=` pattern is directly applicable when consumer feedback
  surfaces additional cases. Explicitly excluded per spec: "Does not add `?=` override points
  for any Make targets beyond `spec-scaffold` and `blueprint-uplift-status`."
  Parked — trigger: `on-scope: blueprint`.
