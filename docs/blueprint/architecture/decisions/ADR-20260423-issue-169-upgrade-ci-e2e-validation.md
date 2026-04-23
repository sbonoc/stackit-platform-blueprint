# ADR-20260423-issue-169-upgrade-ci-e2e-validation: Dedicated upgrade CI job using pytest fixture matrix

## Metadata
- Status: approved
- Date: 2026-04-23
- Owners: bonos
- Related spec path: specs/2026-04-23-issue-169-upgrade-ci-e2e-validation/spec.md

## Business Objective and Requirement Summary
- Business objective: Validate the full consumer upgrade flow on every push to the main branch as a dedicated, visible CI gate so upgrade regressions are surfaced before any release tag is published.
- Functional requirements summary: New shell script `ci_upgrade_validate.sh` + make target `quality-ci-upgrade-validate` + CI job `upgrade-e2e-validation` triggered on push events; JUnit XML artifact uploaded to GitHub Actions.
- Non-functional requirements summary: No external network calls; `set -euo pipefail`; locally runnable; no new Python abstractions.
- Desired timeline: 2026-04-23.

## Decision Drivers
- Driver 1: The upgrade fixture matrix test (`test_upgrade_fixture_matrix.py`) currently runs inside `infra-contract-test-fast`, which is buried in the `blueprint-quality` CI job. There is no dedicated upgrade validation signal visible in the GitHub Actions job list.
- Driver 2: Issue #169 is the Phase 1 foundation for Phase 2 correctness gates (#162, #163) which will add new checks to the upgrade CI job. A dedicated job provides the extension point.
- Driver 3: The `quality-ci-check-sync` drift guard (which validates `.github/workflows/ci.yml`) requires that any new CI job is rendered by `render_ci_workflow.py` and governed by the same drift detection. A dedicated job entry is the clean architectural boundary.

## Options Considered
- Option A: New `ci_upgrade_validate.sh` wraps `python3 -m pytest tests/blueprint/test_upgrade_fixture_matrix.py` — reuses existing test infrastructure, no duplicate fixture setup logic.
- Option B: New Python driver script sets up temp repos independently and calls Python upgrade scripts directly, matching the style of `template_smoke.sh`.

## Decision
- Selected option: Option A
- Rationale: Option A reuses the existing, validated `test_upgrade_fixture_matrix.py` without duplicating the ~80 lines of temp-repo fixture setup logic (git init, fixture copy, contract.yaml patching, template materialization). The pytest runner handles the full fixture lifecycle. Option B would reproduce logic already maintained in the test module and introduce a second fixture-setup path to keep in sync. Phase 2 extensions (#162, #163) add new test modules to the pytest invocation in `ci_upgrade_validate.sh` — the extensibility point is the pytest file list, not a custom driver.

## Consequences
- Positive: Upgrade validation is visible as a separate CI job with a dedicated artifact; Phase 2 issues can add new pytest modules without touching the CI workflow definition; no new Python abstractions introduced.
- Negative: `test_upgrade_fixture_matrix.py` runs twice on main pushes (once in `hooks_fast` via `infra-contract-test-fast`, once in the new dedicated job). This is an intentional trade-off for visibility and artifact upload.
- Neutral: The new job runs on push-to-main only (not PRs); PRs already get upgrade coverage via `infra-contract-test-fast` inside `blueprint-quality`.

## Diagram

```
Before:
  blueprint-quality job
    quality-ci-blueprint
      quality-hooks-fast
        infra-contract-test-fast
          test_upgrade_fixture_matrix.py  ← buried, no artifact

After:
  blueprint-quality job
    quality-ci-blueprint
      quality-hooks-fast
        infra-contract-test-fast
          test_upgrade_fixture_matrix.py  (unchanged, runs on PRs + push)

  upgrade-e2e-validation job  ← new, push-only
    quality-ci-upgrade-validate
      ci_upgrade_validate.sh
        pytest test_upgrade_fixture_matrix.py --junitxml ...
    upload-artifact: upgrade-validate-junit
```
