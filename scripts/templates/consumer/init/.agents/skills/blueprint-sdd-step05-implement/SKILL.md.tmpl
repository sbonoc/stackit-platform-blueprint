---
name: blueprint-sdd-step05-implement
description: Execute SDD Step 6 — implement the work item in TDD slices following plan.md, writing failing tests first then making them green, committing each slice to the existing Draft PR branch. Uses stack-agnostic Make targets derived from the spec's Implementation Stack Profile.
---

# Blueprint SDD Step 06 — Implement

## Step covered

- **Step 6** — Implement

## When to Use

Invoke after `SPEC_READY: true` and plan refinement are complete (Steps 4–5).
Do not start implementation before `SPEC_READY: true` is confirmed in `spec.md`.

## Actor

Software Engineer (invokes agent).

## Determine the test and validation commands first

Before writing any code, read `spec.md` Implementation Stack Profile:

- `Backend stack profile` — determines the backend language and framework.
- `Frontend stack profile` — determines the UI framework and tooling.
- `Test automation profile` — determines the test runner used per lane.

Then derive the canonical commands:

| Lane | Primary command | Fallback (if Make target not yet wired) |
|---|---|---|
| Backend unit | `make backend-test-unit` | Use the test runner for the declared `Backend stack profile` |
| Backend integration | `make backend-test-integration` | Use the test runner for the declared `Backend stack profile` |
| Touchpoints unit | `make touchpoints-test-unit` | Use the test runner for the declared `Frontend stack profile` |
| Touchpoints integration | `make touchpoints-test-integration` | Use the test runner for the declared `Frontend stack profile` |
| All unit | `make test-unit-all` | Run both backend and touchpoints unit lanes |
| Local smoke (HTTP scope) | `make test-smoke-all-local` | Not replaceable — required for HTTP route/filter/query scope |

**Test runner examples by profile (fallback only):**

| Stack profile | Unit test runner | Integration test runner |
|---|---|---|
| `python_plus_fastapi_pydantic_v2` | `python3 -m pytest tests/ -q -m unit` | `python3 -m pytest tests/ -q -m integration` |
| `vue_router_pinia_onyx` | `npx vitest run --reporter=verbose` | `npx vitest run --reporter=verbose` |
| `playwright_pact` | `npx playwright test` | `npx playwright test` |

Always prefer Make targets. Use the raw test runner only when the Make target
does not yet exist for a new application being onboarded.

## Guardrails

1. Implementation MUST NOT start before `SPEC_READY: true` in `spec.md`.
2. Read the `Implementation Stack Profile` in `spec.md` before writing any code
   or test — derive the correct test commands from the declared profiles.
3. Write ALL failing tests for a slice before writing any implementation code.
   Confirm each test fails with the expected error message.
4. Do not commit green tests without the corresponding implementation in the
   same commit — the red slice exists only to prove test correctness.
5. For filter or payload-transform changes: require positive-path unit assertions
   with matching fixture/request values. Empty-result-only assertions are insufficient.
6. For HTTP route/query/filter/new-endpoint scope: run `make test-smoke-all-local`
   and capture the pass/fail result as test evidence in `pr_context.md`.
7. Translate reproducible pre-commit smoke/deterministic-check failures into
   failing automated tests first, then turn them green with the fix. Document
   deterministic exception rationale and follow-up owner when a true exception applies.
8. All commits go to the existing Draft PR branch — no new PR is opened.
9. Mark each task `[x]` in `tasks.md` as it completes.
10. Respect the pyramid: unit > 60%, integration ≤ 30%, e2e ≤ 10%.
    Do not duplicate behavior across pyramid levels.

## Workflow

```
0. Read Implementation Stack Profile from spec.md.
   Determine the correct test commands for this work item's stack.

For each slice in plan.md (follow the defined order):

SLICE N — FAILING TESTS (red)
1. Write all new unit and integration tests for this slice.
2. Run the targeted test command — confirm each new test FAILS:
   make backend-test-unit          # or the appropriate lane
   # If the Make target doesn't exist yet for a new app, use the stack's
   # native test runner as a fallback (see table above).
3. Do NOT write any implementation code yet.
4. Commit the red test file:
   git add tests/...
   git commit -m "test(<slug>): slice N — failing tests (red)"
   git push

SLICE N — IMPLEMENTATION (green)
5. Write the implementation to make the failing tests pass.
6. Run targeted test command — confirm all new tests pass.
7. Run the full unit suite to confirm no regressions:
   make test-unit-all
8. Mark tasks complete in tasks.md.
9. Commit implementation + updated tasks.md:
   git add <implementation files> specs/YYYY-MM-DD-<slug>/tasks.md
   git commit -m "feat(<slug>): slice N — <brief description>"
   git push

Repeat for each slice in plan.md order.
```

## Minimum validation bundles by change type

After all implementation slices are complete, run the bundle matching the
change type declared in `spec.md` (from AGENTS.md):

| Change type | Commands |
|---|---|
| Governance / docs / contracts only | `make quality-hooks-run` · `make infra-validate` |
| Infra / runtime wrapper changes | `make infra-validate` · `make infra-smoke` · `make infra-audit-version` |
| App delivery / build / deploy changes | `make apps-bootstrap` · `make apps-smoke` · `make apps-audit-versions` |
| HTTP route / filter / query scope | `make test-smoke-all-local` (record pass/fail in `pr_context.md`) |

## Special cases

### Filter / payload-transform changes

Positive-path assertion MUST verify that a request with a matching fixture
value returns the expected record and that output fields are preserved. An
assertion that only tests the empty-result case is not sufficient.

### HTTP route / query scope

Run local smoke test after implementation:
```bash
make test-smoke-all-local
```
Capture the pass/fail output and record it in `pr_context.md` Validation Evidence.

### Reproducible pre-commit failures

If `make quality-hooks-fast` or a smoke assertion fails deterministically
before the fix:
1. Write a failing automated test that reproduces the failure.
2. Confirm the test fails (red).
3. Fix the root cause — the test turns green.
4. If a true exception applies (e.g., environment-only failure), document the
   rationale and a follow-up owner in `pr_context.md` Deferred Proposals.

## Required Report Format

Return per slice:

1. Stack profile read from spec.md (backend, frontend, test automation).
2. Test commands determined for this work item.
3. Slice name and description.
4. Tests written (count) and confirmed-red result.
5. Implementation files changed.
6. Full-suite regression result.
7. Tasks marked complete in tasks.md (task IDs).
8. Commit SHA pushed.

After all slices:

9. Minimum validation bundle run and result.
10. Any open exception rationale documented?

## References

- Implementation checklist: `references/implement_checklist.md`
