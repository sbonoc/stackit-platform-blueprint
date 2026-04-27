---
name: blueprint-sdd-step05-implement
description: Execute SDD Step 6 — implement the work item in TDD slices following plan.md, writing failing tests first then making them green, committing each slice to the existing Draft PR branch. Uses stack-agnostic Make targets derived from the spec's Implementation Stack Profile.
---

# Blueprint SDD Step 05 — Implement

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

## Stack-specific test isolation

Apply the patterns below to keep tests fast and fully decoupled from live
dependencies. These are mandatory defaults — deviate only with documented rationale.

### Vue / Nuxt (`vue_router_pinia_onyx` profile)

- Use `@vue/test-utils` for component tests. Test **public interfaces only**: props,
  emitted events, and rendered DOM output. Do not assert on private component state or
  internal refs.
- For components that require Nuxt context use `@nuxt/test-utils` with
  `mountSuspended` or `renderSuspended` — never plain `mount` against a real Nuxt
  runtime in a unit test.
- Mock composables and Nuxt auto-imports with `mockNuxtImport` so tests are
  independent of Nuxt's runtime module resolution.
- Use the **Pact Stub Server** for integration tests that exercise API call paths.
  Do not point unit or component tests at a live backend service.

### Python / FastAPI (`python_plus_fastapi_pydantic_v2` profile)

- Test endpoints with FastAPI's `TestClient` (backed by `httpx`) — no real server
  socket is bound and no network round-trip occurs.
- Isolate domain and application logic from infrastructure adapters using
  `unittest.mock` or the `pytest-mock` `mocker` fixture.
- Unit tests MUST NOT make real HTTP calls or open real database connections.
  Use in-memory repositories or fixture-injected fakes for integration tests.

### Kotlin / Ktor

- Use `MockEngine` for HTTP client tests — simulates responses without a network
  connection.
- Use `testApplication` for server-side tests — no real port is bound, keeping tests
  fast and parallelisable.
- Test application and domain logic without the Ktor engine wherever the dependency
  direction allows.

### Go / Gin

- Use `net/http/httptest` (`httptest.NewRecorder` + `httptest.NewServer`) for handler
  and endpoint tests without starting a full server.
- Keep handler unit tests free of real database or external service calls; inject
  interface stubs or use `testify/mock` for collaborators.

### Pact contract lane (`playwright_pact` profile — `*-test-contracts` Make targets)

- **Consumer side (Vue/Nuxt):** write interaction tests against the Pact Mock Server.
  The generated `.json` pact files are the contract artefacts — commit them to source
  control and reference them in `spec.md` under Contract Impacts.
- **Provider side (Python/Go/Kotlin):** verify published contracts using the Pact
  Verifier in the `backend-test-contracts` lane. No live frontend is required.
- A Pact contract test MUST replace — not supplement — any E2E test that exists solely
  to verify API integration across service boundaries.

## Governance Context

`AGENTS.md` is the canonical policy source for this skill. Sections that apply in this phase:

- `§ Cross-Cutting Guardrails (Must Be Captured in Discover + Specify)` — all guardrails declared in `spec.md` apply during implementation; architecture style, observability, security, API-contract-first, and managed-service-first constraints are enforced here, not only reviewed later.
- `§ Architecture and Design Mandates` — domain → application → infrastructure → presentation layering; no outer-layer imports into inner layers.
- `§ Testing and Quality Ratios` — pyramid target: unit > 60%, integration ≤ 30%, e2e ≤ 10%; mocks over live dependencies; ≥ 70% line coverage; CI pipeline under 15 min.
- `§ Contract Testing Standards` — Pact is the standard for API integration; consumer generates contracts, provider verifies; Pact Stub Server during FE development.
- `§ Feature-Flag Test Matrix (Mandatory)` — any behavior gated by `OBSERVABILITY_ENABLED` must be covered for both flag states.
- `§ Hardening Review Gate` — architecture compliance, observability baseline, and security controls are evaluated in the next step; implementation must produce evidence that satisfies those checks.
- `§ Minimum Validation Bundles by Change Type` — run the matching bundle after all slices complete.

> If `AGENTS.md` changes any of the above sections, update this block to reflect the affected sections.

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
11. Architecture compliance: follow SOLID, Clean Architecture, Clean Code, and DDD
    principles as mandated in `§ Architecture and Design Mandates` (AGENTS.md).
    New modules follow the domain → application → infrastructure → presentation
    layering; no cross-boundary shortcuts are allowed.
12. Observability: new code paths MUST emit structured log entries for significant
    operations; add metrics or trace spans where the declared observability baseline
    in `spec.md` requires coverage.

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

## After All Slices Complete

Run these steps in order after the last slice is committed:

### 1. Minimum validation bundle

Run the bundle matching the change type declared in `spec.md` (from AGENTS.md):

| Change type | Commands |
|---|---|
| Governance / docs / contracts only | `make quality-hooks-run` · `make infra-validate` |
| Infra / runtime wrapper changes | `make infra-validate` · `make infra-smoke` · `make infra-audit-version` |
| App delivery / build / deploy changes | `make apps-bootstrap` · `make apps-smoke` · `make apps-audit-versions` |
| HTTP route / filter / query scope | `make test-smoke-all-local` (record pass/fail in `pr_context.md`) |

### 2. Traceability Verification

Run the `blueprint-sdd-traceability-keeper` skill for this work item. Resolve any
blocking gaps. If `traceability.md` was updated to fix gaps, commit those changes
before closing this skill:

```bash
git add specs/YYYY-MM-DD-<slug>/traceability.md
git commit -m "feat(<slug>): update traceability — post-implementation gaps resolved"
git push
```

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
11. Traceability keeper result (gaps found / clean).

## References

- Implementation checklist: `references/implement_checklist.md`
