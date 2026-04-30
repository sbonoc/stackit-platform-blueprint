# Traceability Matrix

## Requirement-to-Delivery Mapping

| Requirement ID | Control IDs | Design Element | Implementation Path(s) | Test Evidence | Documentation Evidence | Operational Evidence |
|---|---|---|---|---|---|---|
| FR-001 | SDD-C-005, SDD-C-008 | `SPEC_SCAFFOLD_DEFAULT_TRACK ?=` variable + recipe substitution | `scripts/templates/blueprint/bootstrap/make/blueprint.generated.mk.tmpl`; `make/blueprint.generated.mk` | `tests/blueprint/test_quality_contracts.py::test_blueprint_generated_mk_template_exposes_override_point_variables`; `test_generated_makefile_exposes_override_point_variables` | ADR-20260430-issue-241-make-override-warnings.md | `make help` output unchanged; no override warning for `spec-scaffold` |
| FR-002 | SDD-C-005, SDD-C-008 | `BLUEPRINT_UPLIFT_STATUS_SCRIPT ?=` variable + recipe substitution | `scripts/templates/blueprint/bootstrap/make/blueprint.generated.mk.tmpl`; `make/blueprint.generated.mk` | same as FR-001 | same as FR-001 | `make help` output unchanged; no override warning for `blueprint-uplift-status` |
| FR-003 | SDD-C-004 | GNU Make `?=` conditional assignment operator | both files above | both tests above verify `?=` syntax is present | ADR Option A rationale | consumer `platform.mk` sets `:=` after include — no structural change required |
| FR-004 | SDD-C-007 | render pipeline: template → `make blueprint-render-makefile` → generated | `scripts/bin/blueprint/render_makefile.sh` (no change); template + generated file diff | `test_generated_makefile_exposes_override_point_variables` (asserts rendered output) | `docs/reference/generated/core_targets.generated.md` — override-point variables documented in help strings | `make blueprint-render-makefile` idempotent after fix |
| NFR-REL-001 | SDD-C-012 | Backward compatibility — `?=` default matches previous hardcoded values | recipe defaults (`blueprint`, `scripts/bin/blueprint/uplift_status.sh`) | AC-001 and AC-003 verified by contract tests | — | zero behavior change for consumers not setting override vars |
| NFR-OPS-001 | SDD-C-012 | Eliminate override warning | `make/blueprint.generated.mk` variable declarations | AC-002 and AC-004 (consumer override path, no warning) | — | `make help 2>&1 | grep "warning:"` → no output |
| AC-001 | SDD-C-012 | Default track unchanged when var not set | `spec-scaffold` recipe | `test_generated_makefile_exposes_override_point_variables` | — | — |
| AC-002 | SDD-C-012 | Consumer override without warning | `platform.mk` `:=` assignment | contract test (static analysis of variable presence) | — | — |
| AC-003 | SDD-C-012 | Default script unchanged when var not set | `blueprint-uplift-status` recipe | `test_generated_makefile_exposes_override_point_variables` | — | — |
| AC-004 | SDD-C-012 | Consumer script override without warning | `platform.mk` `:=` assignment | contract test (static analysis of variable presence) | — | — |
| AC-005 | SDD-C-008 | Contract assertions in test suite | `tests/blueprint/test_quality_contracts.py` | both new test methods pass | — | regression gate active in CI |

## Graph Linkage
- Graph file: `graph.json`
- Node IDs referenced: FR-001, FR-002, FR-003, FR-004, NFR-REL-001, NFR-OPS-001, AC-001, AC-002, AC-003, AC-004, AC-005

## Validation Summary
- Required bundles executed:
  - `make infra-contract-test-fast` — 136 passed, 2 subtests passed (2026-04-30)
  - `make test-unit-all` (slice 2 green phase) — 57 passed, 13 subtests passed; T-101 and T-102 green (2026-04-30)
  - `make quality-sdd-check` — clean, no violations (2026-04-30)
  - `make quality-docs-sync-core-targets` — "already up to date", no content change in `docs/reference/generated/core_targets.generated.md` (2026-04-30)
  - `make quality-hooks-fast` — all substantive checks pass; `quality-spec-pr-ready` fails on scaffold `pr_context.md` (expected at Step 5, filled at Step 7) (2026-04-30)
  - `make docs-build` — SUCCESS, static files generated (2026-04-30)
  - `make docs-smoke` — status=success (2026-04-30)
  - `make quality-hardening-review` — status=success (2026-04-30)
- Result summary: All implementation, contract, docs, and hardening bundles pass. No blocking gaps.

## Evidence Manifest
- Manifest file: `evidence_manifest.json`
- Context export: `context_pack.md`
- PR context export: `pr_context.md`
- Hardening review export: `hardening_review.md`

## Open Risks and Follow-Ups
- Follow-up: identify other blueprint-managed targets commonly re-defined by consumers; apply the same `?=` override-point pattern in a subsequent work item if consumer feedback surfaces new cases
