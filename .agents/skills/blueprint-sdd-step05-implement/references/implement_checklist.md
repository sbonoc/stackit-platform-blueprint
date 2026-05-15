# Implementation Checklist

- Confirm SPEC_READY: true is set in spec.md before writing any code.
- Read Implementation Stack Profile from spec.md (backend stack, frontend stack, test automation profile).
- Determine test commands: prefer canonical Make targets; use raw test runner as fallback for new apps.
- Follow slice order defined in plan.md.
- For each slice:
  - Write ALL failing tests first — confirm each fails with expected error.
  - Do not write implementation code before confirming tests fail.
  - Write implementation to make tests pass.
  - Run targeted tests — confirm all pass (make backend-test-unit or make touchpoints-test-unit).
  - Run full unit suite — confirm no regressions (make test-unit-all).
  - Mark tasks [x] in tasks.md.
  - Commit red tests and green implementation as separate commits.
- For filter/payload-transform changes: positive-path assertions with matching fixture values required.
- For HTTP route/query scope: run make test-smoke-all-local and record pass/fail in pr_context.md.
- Translate reproducible pre-commit failures into failing tests first, then fix.
- Run minimum validation bundle for the change type declared in spec.md.
- All commits go to the existing Draft PR branch.
- Confirm no new PR was opened.

## Per-Slice Definition-of-Done Gates (Guardrails #13–#15)

### Guardrail #13 — API response field coverage (HTTP-scope slices only)
- [ ] For any slice that adds or modifies fields on a response schema: a backend
      integration test using FastAPI `TestClient` MUST assert ALL response contract
      fields are present and non-null/non-empty for a fixture with real (non-empty) data.
- [ ] Asserting only a 200 response or non-empty body MUST NOT satisfy this gate.
- [ ] `make test-smoke-all-local` MUST NOT be used as a substitute for this assertion.

### Guardrail #14 — Vue component test per rendering branch (Vue SFC slices only)
- [ ] For any Vue SFC rendering change: enumerate which Vitest Browser Mode component
      test covers each rendering branch touched — including fallback, degraded, and
      error paths.
- [ ] The slice MUST NOT be declared done if any added or modified rendering branch is
      absent from the component test suite.

### Guardrail #15 — Pact consumer + provider (HTTP-scope slices that modify API contracts)
- [ ] A Pact consumer interaction asserting the new/modified field shape MUST be written
      in the same slice.
- [ ] Same-repo provider: provider verification MUST pass in the same slice.
- [ ] Cross-repo provider: generated pact file MUST be committed; slice-done report MUST
      record "Pact provider verification: deferred to provider repo <name>".
- [ ] A slice that extends an API contract without a Pact consumer interaction MUST NOT
      be declared done.

## Step 3 — Local Smoke Gate (HTTP and UI-rendering scope — REQUIRED)
- [ ] For HTTP route / filter / query scope: `make test-smoke-all-local` passes.
- [ ] For HTTP route + UI rendering scope: `make test-smoke-all-local` passes AND Vitest
      Browser Mode component test suite green.
- [ ] Pass/fail result recorded in `pr_context.md` Validation Evidence.
- [ ] PR MUST NOT be opened until this step passes.
