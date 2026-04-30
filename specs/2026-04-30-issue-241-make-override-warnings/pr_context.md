# PR Context

## Summary

Eliminates spurious GNU Make `overriding commands` warnings in consumer repos that customise
`spec-scaffold` (to change the default `--track`) or `blueprint-uplift-status` (to redirect
to a consumer-owned script). Two consumer-settable `?=` override-point variables —
`SPEC_SCAFFOLD_DEFAULT_TRACK` (default: `blueprint`) and `BLUEPRINT_UPLIFT_STATUS_SCRIPT`
(default: `scripts/bin/blueprint/uplift_status.sh`) — are added to `blueprint.generated.mk`
and its template source. Consumers set `:=` in `platform.mk` (included after blueprint)
without redefining the target, which eliminates the warning. Scope: blueprint tooling only;
zero runtime, API, or app delivery path impact. Work item:
`specs/2026-04-30-issue-241-make-override-warnings/`. Closes #241.

## Requirement Coverage

| Requirement ID | Implementation File(s) | Test Evidence |
|---|---|---|
| FR-001 | `scripts/templates/blueprint/bootstrap/make/blueprint.generated.mk.tmpl` (line 137); `make/blueprint.generated.mk` (line 137) | `test_blueprint_generated_mk_template_exposes_override_point_variables`, `test_generated_makefile_exposes_override_point_variables` |
| FR-002 | `scripts/templates/blueprint/bootstrap/make/blueprint.generated.mk.tmpl` (line 58); `make/blueprint.generated.mk` (line 58) | same as FR-001 |
| FR-003 | both template and generated file — `?=` operator verified present by contract tests | both test methods assert the exact `?=` string |
| FR-004 | `scripts/bin/blueprint/render_makefile.sh` (unchanged, re-exercised); template + generated diff | `test_generated_makefile_exposes_override_point_variables` asserts rendered output |
| NFR-REL-001 | recipe defaults unchanged: `blueprint`, `scripts/bin/blueprint/uplift_status.sh` | AC-001 and AC-003 via contract tests |
| NFR-OPS-001 | `make/blueprint.generated.mk` — `?=` declarations before both target definitions | AC-002 and AC-004 via contract tests |
| AC-001 | `spec-scaffold` recipe uses `$(or $(SPEC_TRACK),$(SPEC_SCAFFOLD_DEFAULT_TRACK))` | `test_generated_makefile_exposes_override_point_variables` |
| AC-002 | Consumer sets `SPEC_SCAFFOLD_DEFAULT_TRACK := <value>` in `platform.mk` | contract test (static analysis of variable presence) |
| AC-003 | `blueprint-uplift-status` recipe uses `@$(BLUEPRINT_UPLIFT_STATUS_SCRIPT)` | `test_generated_makefile_exposes_override_point_variables` |
| AC-004 | Consumer sets `BLUEPRINT_UPLIFT_STATUS_SCRIPT := <path>` in `platform.mk` | contract test (static analysis of variable presence) |
| AC-005 | `tests/blueprint/test_quality_contracts.py` — 2 new test methods (lines 131–141) | both methods pass; 57 passed total |

- Contract surfaces changed:
  - [x] docs/templates/tests were synchronized (`core_targets.generated.md` updated; template and generated file in sync)
  - [ ] `blueprint/contract.yaml` changed — not applicable (variable declaration only)
  - [ ] generated consumer behavior changed — not applicable (defaults unchanged; no consumer observes different behavior unless they set the override variables)

## Key Reviewer Files

- Primary files to review first:
  - `scripts/templates/blueprint/bootstrap/make/blueprint.generated.mk.tmpl` — primary
    source of truth; changes propagate to all blueprint consumers on next upgrade. Verify:
    `SPEC_SCAFFOLD_DEFAULT_TRACK ?= blueprint` at line 137 and
    `BLUEPRINT_UPLIFT_STATUS_SCRIPT ?= scripts/bin/blueprint/uplift_status.sh` at line 58;
    both recipe tokens substituted; help strings extended with override-point variable names.
  - `make/blueprint.generated.mk` — re-rendered output; must be in sync with the template.
    Verify identical `?=` declarations and recipe tokens at matching positions.
  - `tests/blueprint/test_quality_contracts.py` (lines 131–141) — two new contract
    assertions that guard against future template regressions removing the override-point
    variables.
- High-risk files:
  - `scripts/templates/blueprint/bootstrap/make/blueprint.generated.mk.tmpl` — any
    unintended change here propagates to all blueprint consumers on next upgrade.
- Supporting reviewer context:
  - `docs/blueprint/architecture/decisions/ADR-20260430-issue-241-make-override-warnings.md`
    — records the Option A decision, include-order mechanics, and why `?=` eliminates
    the warning without requiring structural changes.
  - `docs/reference/generated/core_targets.generated.md` — public command reference;
    verify `SPEC_SCAFFOLD_DEFAULT_TRACK` and `BLUEPRINT_UPLIFT_STATUS_SCRIPT` appear in
    the help strings for their respective targets.

## Validation Evidence

| Command | Result |
|---|---|
| `make infra-contract-test-fast` | 136 passed, 2 subtests passed |
| `make test-unit-all` (slice 2 green gate) | 57 passed, 13 subtests passed; T-101 and T-102 green |
| `make quality-sdd-check` | clean, no violations |
| `make quality-docs-sync-core-targets` | content updated (override variables now in help strings) |
| `make quality-docs-check-changed` | PASS — pyramid unit 95.02%, integration 3.90%, e2e 1.08% |
| `make quality-hooks-fast` | all substantive checks pass |
| `make docs-build` | SUCCESS — static files generated |
| `make docs-smoke` | status=success |
| `make quality-hardening-review` | status=success |
| `python3 scripts/lib/docs/sync_blueprint_template_docs.py` | 13 files already synchronized, 0 updated |

All runs: 2026-04-30 on branch `codex/2026-04-30-issue-241-make-override-warnings`.

## Risk and Rollback

- **Main risks:**
  - Risk 1: consumer sets `SPEC_SCAFFOLD_DEFAULT_TRACK` to an invalid value →
    `spec_scaffold.py` validates its `--track` argument and exits with a clear error;
    no silent failure path introduced.
  - Risk 2: `make blueprint-render-makefile` produces a diff beyond the two targeted
    substitutions → caught immediately by contract tests and `infra-contract-test-fast`.
- **Blast radius:** Blueprint tooling only (Makefile variable declarations). Zero runtime,
  API, or app delivery path impact. No database, secret, or infrastructure state involved.
- **Feature flag:** N/A — `?=` declarations are passive until a consumer explicitly sets
  the variable in `platform.mk`.
- **Rollback strategy:** Revert commits `adadb62` (tests red), `3551a9c` (implementation),
  `b05bdb5` (docs), `65ba94d` (traceability) via `git revert`; run
  `make blueprint-render-makefile` to re-sync the generated file. No runtime state or
  database migration to reverse.

## Deferred Proposals

- **Extend `?=` override-point pattern to other blueprint-managed targets
  (P-HRD-001)** — explicitly out of scope per spec exclusion ("Does not add `?=` override
  points for any Make targets beyond `spec-scaffold` and `blueprint-uplift-status`");
  no consumer override request exists for other specific targets.
  Parked — trigger: `on-scope: blueprint` — surfaces when blueprint template/upgrade scope
  is next touched; apply if consumer feedback has identified additional targets.

## Follow-Up

- Consumer repos that previously re-defined `spec-scaffold` or `blueprint-uplift-status`
  in `platform.mk` can migrate to variable assignment after consuming this blueprint
  upgrade. No forced migration — old re-definition continues to work (variable declaration
  takes precedence; warning is already eliminated from the blueprint side).
