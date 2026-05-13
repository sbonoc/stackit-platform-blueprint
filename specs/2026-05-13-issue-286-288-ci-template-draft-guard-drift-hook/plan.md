# Implementation Plan

## Implementation Start Gate
- Implementation tasks MUST remain unchecked until `SPEC_READY=true`.
- If required inputs are missing, add `BLOCKED_MISSING_INPUTS` in `spec.md` and keep the gate closed.

## Constitution Gates (Pre-Implementation)
- Simplicity gate: Four additive changes — two lines in `ci.yml.tmpl`, one flag in `validate_contract.py`, one Make target in `blueprint.generated.mk.tmpl`, two hook stanzas in `.pre-commit-config.yaml` files. No new abstractions or wrapper layers.
- Anti-abstraction gate: Direct file edits; no new helper functions beyond the `--bootstrap-drift-only` flag path in `validate_contract.py` (mirrors the existing `--branch-only` pattern).
- Integration-first testing gate: Tests parse the template files and check for specific string patterns; no mocking required.
- Positive-path filter/transform test gate: N/A — no filter or payload-transform logic in scope.
- Finding-to-test translation gate: Both bugs are reproducible (#288 is verifiable by string search in template; #286 is verifiable by running `make quality-validate-bootstrap-template-drift` before and after). Slice 1 MUST write failing assertions before the fix; Slice 2 turns them green.

## Delivery Slices

### Slice 1 — RED: failing test assertions

Add failing test methods in `tests/blueprint/test_quality_contracts.py`:

1. `test_consumer_ci_template_has_draft_pr_types_filter`:
   - Read `scripts/templates/consumer/init/.github/workflows/ci.yml.tmpl`.
   - Assert `types: [opened, synchronize, reopened, ready_for_review]` is present.
   - Expected result: FAIL (key absent in template).

2. `test_consumer_ci_template_quality_fast_has_draft_pr_guard`:
   - Read `scripts/templates/consumer/init/.github/workflows/ci.yml.tmpl`.
   - Assert `if: github.event_name == 'push' || github.event.pull_request.draft == false` is present.
   - Expected result: FAIL (guard absent in template).

3. `test_precommit_has_bootstrap_drift_hook`:
   - Read `.pre-commit-config.yaml`.
   - Assert `id: quality-validate-bootstrap-template-drift` is present.
   - Expected result: FAIL (hook absent).

4. `test_precommit_template_has_bootstrap_drift_hook`:
   - Read `scripts/templates/blueprint/bootstrap/.pre-commit-config.yaml`.
   - Assert `id: quality-validate-bootstrap-template-drift` is present.
   - Expected result: FAIL (hook absent in template).

5. `test_make_template_has_quality_validate_bootstrap_drift_target`:
   - Read `scripts/templates/blueprint/bootstrap/make/blueprint.generated.mk.tmpl`.
   - Assert `quality-validate-bootstrap-template-drift:` is present.
   - Expected result: FAIL (target absent).

Run `uv run python3 -m pytest tests/blueprint/test_quality_contracts.py -v -k "draft_pr or bootstrap_drift"` — confirms 5 new FAILs, all pre-existing tests still green.

### Slice 2 — GREEN: implement all changes; verify tests pass

**FR-001/FR-002 — CI template update:**
Edit `scripts/templates/consumer/init/.github/workflows/ci.yml.tmpl`:
```yaml
on:
  pull_request:
    types: [opened, synchronize, reopened, ready_for_review]
  push:
    branches:
      - {{DEFAULT_BRANCH}}
  workflow_dispatch:

jobs:
  quality-fast:
    runs-on: ubuntu-latest
    if: github.event_name == 'push' || github.event.pull_request.draft == false
```

**FR-005 — `--bootstrap-drift-only` flag in `validate_contract.py`:**
- Add `--bootstrap-drift-only` argument to `parse_args()` (after `--branch-only`).
- Add fast path in `main()` that calls `_validate_bootstrap_template_sync(repo_root, contract)` and exits.

**FR-003 — Make target in template and generated file:**
- Add to `scripts/templates/blueprint/bootstrap/make/blueprint.generated.mk.tmpl`:
  ```makefile
  quality-validate-bootstrap-template-drift: ## Fail when blueprint-tracked root-level managed files drift from bootstrap template counterparts
  	@uv run python3 scripts/bin/blueprint/validate_contract.py --bootstrap-drift-only
  ```
- Regenerate `make/blueprint.generated.mk` by running `make quality-sdd-sync-all` or equivalent resync command.

**FR-004 — Pre-commit hook in both `.pre-commit-config.yaml` files:**
Add to commit-stage hooks in `.pre-commit-config.yaml` and `scripts/templates/blueprint/bootstrap/.pre-commit-config.yaml`:
```yaml
      - id: quality-validate-bootstrap-template-drift
        name: quality bootstrap template drift check
        language: system
        entry: make quality-validate-bootstrap-template-drift
        pass_filenames: false
        files: ^(\.dockerignore|\.gitignore|\.editorconfig|\.pre-commit-config\.yaml|Makefile|scripts/templates/blueprint/bootstrap/)
```

Run `uv run python3 -m pytest tests/blueprint/test_quality_contracts.py -v -k "draft_pr or bootstrap_drift"` — confirms all 5 new tests green.
Run `uv run python3 -m pytest tests/blueprint/ -v` — confirms all pre-existing tests remain green.

## Change Strategy
- Migration/rollout sequence: CI template change propagates to new consumer repos at init time and to existing consumers at next blueprint upgrade. Pre-commit hook change takes effect immediately after `pre-commit install` (or on next pre-commit auto-update).
- Backward compatibility policy: All changes are additive; no existing hooks, CI steps, or Make targets are removed or modified.
- Rollback plan: Revert `scripts/templates/consumer/init/.github/workflows/ci.yml.tmpl` (two lines removed), revert `validate_contract.py` (`--bootstrap-drift-only` block removed), revert `blueprint.generated.mk.tmpl` + regenerate, revert both `.pre-commit-config.yaml` files.

## Validation Strategy (Shift-Left)
- Unit checks: `uv run python3 -m pytest tests/blueprint/test_quality_contracts.py -v` — 5 new assertions + all pre-existing assertions green.
- Contract checks: `make infra-validate` — confirms template and Make target structure.
- Integration checks: `make quality-hooks-fast` — confirms pre-commit hook stanza is valid YAML and hook runs successfully.
- E2E checks: not in scope — change is static YAML + CLI flag; no runtime integration paths affected.

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
- Notes: No Make-target contract changes affecting app delivery; all listed targets are pre-existing and unaffected by this work item.

## Documentation Plan (Document Phase)
- Blueprint docs updates: Review `docs/blueprint/ci/` or equivalent for a CI workflow reference; add a note about the draft-PR skip in consumer CI template if absent.
- Consumer docs updates: None required — the CI template change is self-documenting; no consumer runbook changes.
- Mermaid diagrams updated: None required — the architecture.md diagrams capture the data flow.
- Docs validation commands:
  - `make docs-build`
  - `make docs-smoke`

## Publish Preparation
- PR context file: `pr_context.md`
- Hardening review file: `hardening_review.md`
- Local smoke gate (HTTP route/filter changes): N/A — no HTTP route or filter scope.
- Publish checklist:
  - include requirement/contract coverage
  - include key reviewer files
  - include validation evidence + rollback notes

## Operational Readiness
- Logging/metrics/traces: none — no script paths affecting structured output change.
- Alerts/ownership: none.
- Runbook updates: none required.

## Risks and Mitigations
- Risk 1: `quality-validate-bootstrap-template-drift` commit hook adds latency for commits touching `.pre-commit-config.yaml` or `Makefile`. Mitigation: the hook runs `validate_contract.py --bootstrap-drift-only` which loads only the contract and calls a single sync function; expected runtime <2s, comparable to existing commit hooks.
- Risk 2: `make/blueprint.generated.mk.tmpl` is a generated-file template; after adding the new target, the generated `make/blueprint.generated.mk` must be regenerated in the same commit to avoid drift. Mitigation: regenerate immediately after editing the template; `make infra-validate` catches any residual drift.
