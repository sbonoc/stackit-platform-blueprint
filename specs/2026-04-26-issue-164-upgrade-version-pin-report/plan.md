# Implementation Plan

## Implementation Start Gate
- Implementation tasks MUST remain unchecked until `SPEC_READY=true`.
- If required inputs are missing, add `BLOCKED_MISSING_INPUTS` in `spec.md` and keep the gate closed.

## Constitution Gates (Pre-Implementation)
- Simplicity gate: Two focused modules (`upgrade_version_pin_diff.py` for diff logic; `upgrade_residual_report.py` section for rendering). No shared base class or abstraction layer introduced.
- Anti-abstraction gate: `subprocess.run` + `Path.rglob` are used directly; no wrapper layer over git or filesystem operations.
- Integration-first testing gate: Unit tests use fixture `versions.sh` strings (no git required); integration fixture validates full pipeline invocation with a real git repo fixture.
- Positive-path filter/transform test gate: AC-001 and AC-006 both require a fixture with at least one changed pin that maps to at least one template reference; the test MUST assert the `changed_pins` list is non-empty and the `template_references` list contains the expected path.
- Finding-to-test translation gate: AC-005 (git error recovery) MUST be translated into a unit test that mocks `subprocess.run` to raise `CalledProcessError` and asserts the JSON artifact contains the `error` field and the pipeline does not propagate the error.

## Delivery Slices

### Slice 1 — Red: failing unit tests for pin diff logic (TDD baseline)
- Write `tests/blueprint/test_upgrade_version_pin_diff.py` with tests for:
  - `parse_versions_sh` — fixture strings → dict of variable→value
  - `diff_pins` — two dicts → correct `changed_pins`, `new_pins`, `removed_pins`, `unchanged_count`
  - `scan_template_references` — fixture template dir with a file referencing `TERRAFORM_VERSION` → expected path in result
  - `_resolve_baseline_ref` — fixture source path + version string → resolved tag candidate or None when rev-parse fails
  - `run_version_pin_diff` (integration boundary) — fixture `blueprint/contract.yaml` with known `template_version`; mocked git subprocess returns fixture `versions.sh` content → correct JSON artifact written
  - git error path — mocked subprocess raises `CalledProcessError` → JSON artifact with `error` field, function returns True (non-blocking)
- All tests fail (script not yet written).

### Slice 2 — Green: implement `upgrade_version_pin_diff.py`
- Create `scripts/lib/blueprint/upgrade_version_pin_diff.py`:
  - `parse_versions_sh(content: str) -> dict[str, str]`: parse `VAR="value"` and `VAR=value` lines; skip comments and blank lines
  - `diff_pins(baseline: dict, target: dict) -> PinDiffResult`: classify each variable; return `changed_pins`, `new_pins`, `removed_pins`, `unchanged_count`
  - `scan_template_references(repo_root: Path, variable_names: list[str]) -> dict[str, list[str]]`: rglob `scripts/templates/infra/bootstrap/`, read each file, return variable → [file_paths]
  - `_resolve_baseline_ref(source_path: str, template_version: str) -> str | None`: try `v{template_version}` then `{template_version}` as git tag candidates via `git rev-parse` (mirrors `upgrade_consumer.py:_resolve_baseline_ref`)
  - `run_version_pin_diff(repo_root: Path, upgrade_source: str, upgrade_ref: str) -> bool`: read baseline version from `blueprint/contract.yaml` → `spec.repository.template_bootstrap.template_version`; resolve baseline ref; run `git show <baseline_ref>:scripts/lib/infra/versions.sh` and `git show <target_ref>:scripts/lib/infra/versions.sh` with `cwd=upgrade_source`; diff, scan, write JSON; catch all exceptions, log, write error artifact, return True always
  - `main()`: argparse CLI (`--repo-root`); read `BLUEPRINT_UPGRADE_SOURCE` and `BLUEPRINT_UPGRADE_REF` from env (consistent with Stage 5 pattern); call `run_version_pin_diff`
- All Slice 1 tests go green.

### Slice 3 — Red: failing unit test for residual report version pin section
- Add test in `tests/blueprint/test_upgrade_residual_report.py` (or new file):
  - Fixture: `version_pin_diff.json` with one changed pin (`TERRAFORM_VERSION`), one new pin, one removed pin, and one template reference
  - Assert residual report Markdown contains "Version Pin Changes" heading, the changed pin line, the template reference path, and the prescribed action
  - Fixture: `version_pin_diff.json` with zero changes → assert section contains "No version pin changes detected"
  - Fixture: `version_pin_diff.json` absent → assert section contains "Version pin diff unavailable" with fallback command
- Tests fail (section not yet added).

### Slice 4 — Green: add "Version Pin Changes" section to `upgrade_residual_report.py`
- Add `_render_version_pin_section(repo_root: Path) -> str` function:
  - Read `artifacts/blueprint/version_pin_diff.json`; handle absent/malformed with fallback text
  - Format changed pins as `| VARIABLE | old → new | template_references | Prescribed action |`
  - Format new pins and removed pins in subsections
  - Return empty section header with "No changes detected" when all lists are empty
- Insert section call in `generate_residual_report` after the "Prune-Glob Violations" section
- All Slice 3 tests go green.

### Slice 5 — Pipeline wiring
- In `upgrade_consumer_pipeline.sh`, after Stage 1 success block and before Stage 2, add:
  ```bash
  log_info "[PIPELINE] Stage 1b: starting — version pin diff"
  BLUEPRINT_UPGRADE_SOURCE="$upgrade_source" \
  BLUEPRINT_UPGRADE_REF="$upgrade_ref" \
  python3 "$ROOT_DIR/scripts/lib/blueprint/upgrade_version_pin_diff.py" \
    --repo-root "$ROOT_DIR" || true
  log_info "[PIPELINE] Stage 1b: complete"
  ```
- This is consistent with Stage 5 (`upgrade_coverage_fetch.py`) pattern: `BLUEPRINT_UPGRADE_SOURCE` is the local blueprint clone path; `BLUEPRINT_UPGRADE_REF` is the target ref; baseline ref is resolved internally from `blueprint/contract.yaml`. No new pipeline variables needed.

### Slice 6 — Skill runbook update
- In `.agents/skills/blueprint-consumer-upgrade/SKILL.md`, add a step after the residual report review step:
  - Document the "Version Pin Changes" section of `artifacts/blueprint/upgrade-residual.md`
  - Instruct operator: if any changed pins are listed, run `make infra-bootstrap`, then sync the listed templates under `scripts/templates/infra/bootstrap/`, then run `make infra-validate`

### Slice 7 — Validation
- Run `make quality-sdd-check` — fix all violations
- Run `make infra-validate` — confirm contract validation passes
- Run `make quality-hooks-run` — confirm pre-commit hooks pass
- Run `pytest tests/blueprint/ -k "version_pin"` — confirm all new tests pass

## Change Strategy
- Migration/rollout sequence: additive only; existing pipeline behavior is unchanged. Stage 1b runs and emits an artifact; if the artifact is absent the residual report degrades gracefully. No consumer repo changes required.
- Backward compatibility policy: fully backward compatible; the JSON artifact is a new file in the existing gitignored `artifacts/blueprint/` directory. The residual report gains a new section but existing sections are unchanged.
- Rollback plan: remove the Stage 1b invocation from `upgrade_consumer_pipeline.sh` and remove `_render_version_pin_section` from `upgrade_residual_report.py`; no state changes persist after rollback.

## Validation Strategy (Shift-Left)
- Unit checks: `pytest tests/blueprint/test_upgrade_version_pin_diff.py tests/blueprint/test_upgrade_residual_report.py` — covers parse, diff, scan, error paths, and Markdown rendering
- Contract checks: `make infra-validate` — confirms no contract drift introduced
- Integration checks: full pipeline invocation test with a real git fixture (if available in existing test suite); otherwise the unit mocks constitute the integration boundary
- E2E checks: not applicable — no Kubernetes or external runtime components involved

## App Onboarding Contract (Normative)
- Required minimum make targets:
  - `apps-bootstrap`
  - `apps-smoke`
  - `backend-test-unit`
  - `backend-test-integration`
  - `backend-test-contracts`
  - `backend-test-e2e`
  - `touchpoints-test-unit`
  - `touchpoints-test-integration`
  - `touchpoints-test-contracts`
  - `touchpoints-test-e2e`
  - `test-unit-all`
  - `test-integration-all`
  - `test-contracts-all`
  - `test-e2e-all-local`
  - `infra-port-forward-start`
  - `infra-port-forward-stop`
  - `infra-port-forward-cleanup`
- App onboarding impact: no-impact
- Notes: this work item adds a Python script, modifies shell orchestration and a Python report generator only; no app delivery, build, or runtime changes.

## Documentation Plan (Document Phase)
- Blueprint docs updates: `.agents/skills/blueprint-consumer-upgrade/SKILL.md` — new version pin diff review step
- Consumer docs updates: none — the residual report is the operator-facing artifact; no separate consumer docs needed
- Mermaid diagrams updated: `architecture.md` contains the two diagrams for this work item; no existing docs diagrams require update
- Docs validation commands:
  - `make docs-build`
  - `make docs-smoke`

## Publish Preparation
- PR context file: `pr_context.md`
- Hardening review file: `hardening_review.md`
- Local smoke gate (HTTP route/filter changes): not applicable — no HTTP routes or filters involved
- Publish checklist:
  - include requirement/contract coverage
  - include key reviewer files
  - include validation evidence + rollback notes

## Operational Readiness
- Logging/metrics/traces: `upgrade_version_pin_diff.py` logs via pipeline conventions; no persistent metrics
- Alerts/ownership: no alerting required; this is a local CLI tool
- Runbook updates: `.agents/skills/blueprint-consumer-upgrade/SKILL.md` updated in Slice 6

## Risks and Mitigations
- Baseline ref unavailable in cloned source → script exits zero with error artifact; residual report emits manual fallback command
- Variable-name grep is a substring match — could produce false positives for short variable names (e.g., `KIND_VERSION` matching `KIND_SOMETHING_VERSION`). Mitigation: use word-boundary grep pattern or match the exact variable assignment form `VAR=` to reduce false positives.
