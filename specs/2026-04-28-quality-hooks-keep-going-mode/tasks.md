# Tasks

## Gate Checks (Required Before Implementation)
- [ ] G-001 Confirm `SPEC_READY=true` in `spec.md`
- [ ] G-002 Confirm open questions and unresolved alternatives are `0`
- [ ] G-003 Confirm required sign-offs are approved
- [ ] G-004 Confirm `Applicable Guardrail Controls` section includes `SDD-C-###` IDs
- [ ] G-005 Confirm `Implementation Stack Profile` section is fully populated

## Implementation
- [ ] T-001 Add `scripts/lib/shell/keep_going.sh` with `keep_going_active`, `keep_going_init`, `run_check`, `keep_going_finalize` and EXIT-trap cleanup composition
- [ ] T-002 Add `scripts/lib/shell/quality_gating.sh` with `quality_changed_paths`, `quality_paths_match_infra_gate`, `quality_spec_is_ready`, and `QUALITY_HOOKS_FORCE_FULL` semantics
- [ ] T-003 Modify `scripts/bin/quality/hooks_fast.sh` to parse `--keep-going`, source the keep-going helper, run pre-commit fail-fast first, dispatch downstream checks via `run_check` when keep-going is active, and update `--help`
- [ ] T-004 Modify `scripts/bin/quality/hooks_strict.sh` to parse `--keep-going`, source the keep-going helper, dispatch every check via `run_check` when keep-going is active, and update `--help`
- [ ] T-005 Modify `scripts/bin/quality/hooks_run.sh` to parse `--keep-going`, propagate to both child invocations, gate the strict-phase invocation on the fast-phase pre-commit-passed signal, and update `--help`
- [ ] T-006 Modify `scripts/bin/quality/hooks_fast.sh` to source `quality_gating.sh`, compute changed paths once, and gate `infra-validate` + `infra-contract-test-fast` on the gating set with `QUALITY_HOOKS_FORCE_FULL=true` override; emit `quality_hooks_skip_total` metric on skip; update `--help`
- [ ] T-007 Modify the existing `quality-spec-pr-ready` invocation block in `hooks_fast.sh` to consult `quality_spec_is_ready` and emit the skip log + metric when not ready; honor `QUALITY_HOOKS_FORCE_FULL=true` override
- [ ] T-008 Delete the redundant `run_cmd make ... quality-docs-lint` and `run_cmd make ... quality-test-pyramid` lines in `hooks_fast.sh`; reframe the existing `command -v pre-commit` fallback to emit a `log_warn` directing the user to install pre-commit
- [ ] T-009 Edit `.agents/skills/blueprint-sdd-step05-implement/SKILL.md` to add the per-slice / pre-PR gate directive, reframe the `Reproducible pre-commit failures` subsection, and add the AGENTS.md cross-link line (FR-014 + FR-016)
- [ ] T-010 Add the new `Quality Hooks — Inner-Loop and Pre-PR Usage` subsection to `AGENTS.md` (FR-015) using deterministic normative language; mirror the subsection into `scripts/templates/consumer/init/AGENTS.md.tmpl`
- [ ] T-011 Add the canonical FR-016 cross-link line to: `.agents/skills/blueprint-sdd-step04-plan-slicer/SKILL.md`, `.agents/skills/blueprint-sdd-step07-pr-packager/SKILL.md`, `.agents/skills/blueprint-consumer-upgrade/SKILL.md`, `.agents/skills/blueprint-consumer-ops/SKILL.md`, and the matching `references/*.md` checklists where present
- [ ] T-012 Create `.envrc` at the repo root exporting `QUALITY_HOOKS_KEEP_GOING=true`; create `.claude/settings.json` at the repo root with an `env` block setting `QUALITY_HOOKS_KEEP_GOING=true` (FR-017); neither file sets `QUALITY_HOOKS_FORCE_FULL`
- [ ] T-013 Update `scripts/templates/blueprint/bootstrap/make/blueprint.generated.mk.tmpl` doc-comments for `quality-hooks-fast`, `quality-hooks-strict`, `quality-hooks-run` to mention `QUALITY_HOOKS_KEEP_GOING` and `QUALITY_HOOKS_FORCE_FULL`; re-render `make/blueprint.generated.mk`
- [ ] T-014 Add the operations doc entry under `docs/blueprint/operations/` documenting `--keep-going`, `QUALITY_HOOKS_KEEP_GOING`, `QUALITY_HOOKS_KEEP_GOING_TAIL_LINES`, `QUALITY_HOOKS_FORCE_FULL`, the path-gating set, the phase-gating rationale, the dedup rationale, the failure-cascade caveat, the agent-agnostic env propagation kit, and the recommended agent inner-loop usage
- [ ] T-015 Move ADR `Status: proposed → approved` once Architecture sign-off is recorded

## Test Automation
- [ ] T-101 Add `tests/blueprint/test_quality_hooks_keep_going.py` (Python `subprocess`-based, Q-2 resolved: Option A) covering helper contract: env-var detection, per-check pass/fail/duration recording, summary block format, exit code aggregation, tail-length env-var override, EXIT-trap cleanup
- [ ] T-102 Add `tests/blueprint/test_quality_gating.py` (Python `subprocess`-based) covering: `quality_changed_paths` (merge-base ∪ working-tree), `quality_paths_match_infra_gate` (each gating-set entry triggers; non-matching paths do not), `quality_spec_is_ready` (true / false / missing-file cases), `QUALITY_HOOKS_FORCE_FULL=true` override
- [ ] T-103 Add `tests/blueprint/test_quality_hooks_fast_keep_going.py` (Python `subprocess`-based) covering: AC-001 (default fail-fast), AC-002 (`--keep-going` flag aggregation), AC-003 (env-var trigger), AC-004 (pre-commit fail-fast invariant), AC-006 (`--help` mentions keep-going and `QUALITY_HOOKS_FORCE_FULL`)
- [ ] T-104 Add `tests/blueprint/test_quality_hooks_strict_keep_going.py` (Python `subprocess`-based) covering: keep-going aggregation across strict-phase checks, default fail-fast preservation, `--help` mentions keep-going
- [ ] T-105 Add `tests/blueprint/test_quality_hooks_run_keep_going.py` (Python `subprocess`-based) covering: AC-005 (cross-phase invocation order), env-var propagation through composite, combined exit code aggregation, `--help` mentions keep-going
- [ ] T-106 Add a contract test that asserts default invocation (no flag, env var unset) produces byte-equivalent behavior on a fixture with two known-broken independent checks (only the first failure observed; no summary marker emitted)
- [ ] T-107 Add `tests/blueprint/test_quality_hooks_fast_path_gating.py` covering AC-009 (docs/spec-only commit skips infra-validate + infra-contract-test-fast), AC-010 (infra-touching commit runs both), AC-011 (`QUALITY_HOOKS_FORCE_FULL=true` forces both regardless of paths)
- [ ] T-108 Add `tests/blueprint/test_quality_hooks_fast_spec_ready_gating.py` covering AC-012 (`SPEC_READY: false` skips quality-spec-pr-ready), AC-013 (`SPEC_READY: true` runs it), `QUALITY_HOOKS_FORCE_FULL=true` override path
- [ ] T-109 Add `tests/blueprint/test_quality_hooks_fast_dedup.py` covering AC-014 (no separate `run_cmd` lines for `quality-docs-lint` or `quality-test-pyramid`; no double execution observed in log output) and the FR-013 `log_warn` fallback when pre-commit is missing
- [ ] T-110 Add `tests/blueprint/test_step05_skill_per_slice_gate.py` covering AC-015 (`make test-unit-all` directive present; `quality-hooks-fast` framed only as slice-batch / pre-PR gate; `Reproducible pre-commit failures` subsection reframed; FR-016 cross-link present)
- [ ] T-111 Add `tests/blueprint/test_agents_md_quality_hooks_subsection.py` covering AC-016 (subsection title, body invariants, normative language; consumer-init AGENTS.md.tmpl mirror)
- [ ] T-112 Add `tests/blueprint/test_skill_quality_hooks_cross_links.py` covering AC-017 (each of the six skill files contains the canonical cross-link line; absence of restated policy paragraphs)
- [ ] T-113 Add `tests/blueprint/test_envrc_and_claude_settings.py` covering AC-018 (`.envrc` exports `QUALITY_HOOKS_KEEP_GOING=true`; `.claude/settings.json` env block sets it; neither file sets `QUALITY_HOOKS_FORCE_FULL`)

## Validation and Release Readiness
- [ ] T-201 Run `make quality-hooks-fast`, `make quality-hooks-fast QUALITY_HOOKS_KEEP_GOING=true`, `make quality-hooks-fast QUALITY_HOOKS_FORCE_FULL=true`, `make quality-hooks-run`, `make quality-hooks-run QUALITY_HOOKS_KEEP_GOING=true` locally; capture observed runtimes (baseline ~107s vs new docs/spec-only target <15s); record pass/fail and timings in `traceability.md`
- [ ] T-202 Attach evidence (test output, summary block sample) to `traceability.md`
- [ ] T-203 Confirm no stale TODOs / dead code / drift; confirm default code path remains a verbatim `run_cmd` invocation per file
- [ ] T-204 Run documentation validation (`make docs-build` and `make docs-smoke`)
- [ ] T-205 Run hardening review validation bundle (`make quality-hardening-review`)

## Publish
- [ ] P-001 Update `hardening_review.md` with repository-wide findings fixed and proposals-only section
- [ ] P-002 Update `pr_context.md` with requirement/contract coverage, key reviewer files, validation evidence, and rollback notes
- [ ] P-003 Ensure PR description follows repository template headings and references `pr_context.md`

## App Onboarding Minimum Targets (Normative)
- [ ] A-001 `apps-bootstrap` and `apps-smoke` are implemented and verified for the affected app scope
- [ ] A-002 Backend app lanes (`backend-test-unit`, `backend-test-integration`, `backend-test-contracts`, `backend-test-e2e`) are available
- [ ] A-003 Frontend app lanes (`touchpoints-test-unit`, `touchpoints-test-integration`, `touchpoints-test-contracts`, `touchpoints-test-e2e`) are available
- [ ] A-004 Aggregate gates (`test-unit-all`, `test-integration-all`, `test-contracts-all`, `test-e2e-all-local`) are available
- [ ] A-005 Port-forward operational wrappers (`infra-port-forward-start`, `infra-port-forward-stop`, `infra-port-forward-cleanup`) are available
