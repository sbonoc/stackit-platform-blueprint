---
name: blueprint-sdd-step05-implement
description: Execute SDD Step 6 — implement the work item in TDD slices following plan.md, writing failing tests first then making them green, committing each slice to the existing Draft PR branch. Uses stack-agnostic Make targets derived from the spec's Implementation Stack Profile.
blueprint-version: 1.0.0
---

# Blueprint SDD Step 05 — Implement

## Step covered

- **Step 6** — Implement

## When to Use

Invoke after `SPEC_READY: true` and plan refinement are complete (Steps 4–5).
Do not start implementation before `SPEC_READY: true` is confirmed in `spec.md`.

## Actor

Software Engineer (invokes agent).

## Per-Slice Gate vs Pre-PR Gate (MUST follow)

- The **per-slice gate** is `make test-unit-all` (or the lane-specific runner derived from the spec's `Implementation Stack Profile`). Run after every code edit within a slice. Fast, targeted, no infra cost.
- The **slice-batch / pre-PR gate** is `make quality-hooks-fast`. Run at the boundary between slices (before starting the next) and once more immediately before publishing. NOT run after every individual code edit.

> Quality-hooks usage policy (per-slice vs pre-PR gate, keep-going env, force-full): see AGENTS.md § Quality Hooks — Inner-Loop and Pre-PR Usage.

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
13. API response field coverage: for any HTTP-scope slice that adds or modifies fields
    on a response schema, a backend integration test MUST assert that ALL fields
    declared in the response contract are present and non-null/non-empty in the HTTP
    response for a fixture with real (non-empty) data. Asserting only that the handler
    returns 200 or that the response is not empty MUST NOT satisfy this gate. This
    assertion MUST be implemented using FastAPI `TestClient` (no live cluster, no
    port-forward) — it is a pyramid-level integration test, not a smoke test. The local
    smoke gate (`make test-smoke-all-local`) is a separate, coarser reachability gate
    and MUST NOT be used as a substitute for this field-coverage assertion.
14. Vue component test per rendering branch: for any Vue SFC rendering change (new
    component, modified template, or touched conditional branch), before marking the
    slice done the step05 invocation MUST enumerate which Vitest Browser Mode component test
    covers each rendering branch touched — including fallback, degraded, and error paths.
    A slice MUST NOT be declared done if any rendering branch that was added or modified
    is absent from the component test suite.
15. Pact consumer + provider (same-slice, same-repo): for any HTTP-scope slice that
    adds or modifies fields on an API response contract (TypeScript type, Pydantic
    schema, or OpenAPI spec): (a) a Pact consumer interaction asserting the new/modified
    field shape MUST be written in the same slice; (b) when the provider lives in the
    same repository, provider verification MUST pass in the same slice; (c) when the
    provider lives in a separate repository, the generated pact file MUST be committed
    and the slice-done report MUST explicitly record "Pact provider verification:
    deferred to provider repo <name>". A slice that extends an API contract without a
    Pact consumer interaction MUST NOT be declared done.
16. Spec-value regression tests (FR-005): for every FR or AC naming exact enumerated
    values, field defaults, required option sets, or specific behavioural postconditions,
    at least one test MUST exist that would fail if any named spec-enumerated value were
    absent, wrong, or reordered. A slice MUST NOT be declared done if any spec-named
    constant is untested. Coverage MUST include enumerated option sets, field defaults,
    behavioural postconditions, and required/forbidden fields.
17. Union types for spec-enumerated fields (FR-006): any field whose allowed values are
    named in `spec.md` as `EXACTLY ONE OF: ...` MUST use a stack-native union/enum type
    in implementation code. Using a plain primitive type (`string`, `str`, `String`) for
    such a field is a checklist failure. See the Per-profile examples table below.
18. Single source of truth for enum constants (FR-007): spec-enumerated value sets MUST
    be defined as a named constant in one canonical location per stack (TypeScript `as const`
    array/object, Python module-level `Literal` or tuple, Kotlin companion-object set,
    Go `const` block for scalars or package-level `var` slice for enumerated sets). All template option arrays, composable/store defaults, validation
    logic, and test fixtures MUST import the constant — inline literal repetition MUST NOT
    appear in more than one source file. Inline literal repetition is a checklist failure.
19. Mandatory automated rendered-output coverage for critical user journeys (FR-008): every
    feature that introduces or modifies a user-facing flow (form, wizard, multi-step
    interaction) MUST have at least one automated test that (a) exercises the critical path
    in a real browser against the running application or component, AND (b) asserts what
    the user sees at each step (field labels, option values, rendered state) — not only what
    the API receives. A Vitest Browser Mode component test satisfies this guardrail when its
    assertions enumerate every rendered spec-enumerated value reachable through the critical
    path. When the critical path crosses route boundaries OR depends on auth/session state
    OR spans more than one mounted root component, an additional Playwright cross-page E2E
    test MUST be added. The test MUST be part of the automated quality gate.
20. V-gate classification enforcement: when `spec.md` sets `has-user-facing-flow: true`,
    `E2E gate classification` MUST be `automated` in the same spec. The `make quality-sdd-check`
    gate enforces this; a failing check blocks the PR. Do NOT lower `has-user-facing-flow` to
    `false` to avoid the gate if the work item genuinely introduces or modifies a user-facing flow —
    that misclassifies the spec and defeats the purpose of the gate. Write the automated Playwright
    tests as Guardrail 19 requires. `has-user-facing-flow: false` is correct only when the work
    item's scope truly does not introduce or modify any user-facing flow (for example, a pure
    backend or infrastructure change).

## Per-profile union-type and SSOT-constant idioms

Apply the idioms below for Guardrails 17 and 18. When a new `Implementation Stack Profile`
is introduced, this table MUST be updated in the same commit.

| Profile | Union/enum type idiom | SSOT constant idiom |
|---|---|---|
| TypeScript (`vue_router_pinia_onyx`) | `'a' \| 'b' \| 'c'` literal union or `z.enum(['a','b','c'])` | `export const MY_VALUES = ['a', 'b', 'c'] as const` in a domain module; type derived via `typeof MY_VALUES[number]` |
| Python (`python_plus_fastapi_pydantic_v2`) | `Literal["a", "b", "c"]` field annotation | module-level `MY_VALUES: tuple[str, ...] = ("a", "b", "c")` or `class MyEnum(str, Enum)` |
| Kotlin (Ktor) | `enum class MyType { A, B, C }` or `sealed class` | `companion object { val ALL = setOf(A, B, C) }` |
| Go (Gin) | typed `const` block with `type MyType string` alias | package-level `var AllowedValues = []MyType{A, B, C}` |

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

## 3. Local smoke gate (HTTP and UI-rendering scope)

This step is REQUIRED and non-optional for HTTP and UI-rendering scope. A PR MUST NOT
be opened until it passes.

For **HTTP route / filter / query scope**: run `make test-smoke-all-local` and capture
the pass/fail result in `pr_context.md` Validation Evidence.

For **HTTP route + UI rendering scope**: BOTH of the following MUST pass before the PR
is opened:
- `make test-smoke-all-local` — REQUIRED, non-optional
- Vitest Browser Mode component test suite green (all rendering branches covered by
  Guardrail #14 enumeration) — REQUIRED

## After All Slices Complete

Run these steps in order after the last slice is committed:

### 1. Minimum validation bundle

Run the bundle matching the change type declared in `spec.md` (from AGENTS.md):

| Change type | Commands |
|---|---|
| Governance / docs / contracts only | `make quality-hooks-run` · `make infra-validate` |
| Infra / runtime wrapper changes | `make infra-validate` · `make infra-smoke` · `make infra-audit-version` |
| App delivery / build / deploy changes | `make apps-bootstrap` · `make apps-smoke` · `make apps-audit-versions` |
| HTTP route / filter / query scope | `make test-smoke-all-local` — REQUIRED, non-optional (record pass/fail in `pr_context.md`) |
| HTTP route + UI rendering scope | `make test-smoke-all-local` — REQUIRED, non-optional · Vitest Browser Mode component test suite green — REQUIRED (record pass/fail in `pr_context.md`) |

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

### Reproducible pre-commit failures

If a smoke assertion or deterministic quality check fails deterministically
before the fix (discovered during the pre-PR `make quality-hooks-fast` run or via
a smoke test):
1. Write a failing automated test that reproduces the failure.
2. Confirm the test fails (red).
3. Fix the root cause — the test turns green.
4. If a true exception applies (e.g., environment-only failure), document the
   rationale and a follow-up owner in `pr_context.md` Deferred Proposals.

Note: `make quality-hooks-fast` is the slice-batch / pre-PR gate — run it at
slice boundaries and before publishing, not after every individual code edit.

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


## Required Output Schema

The structured payload below is the implementation report the skill returns
to the orchestrator and carries on the `phase: implement` C7 lifecycle event.

```yaml jsonschema
$schema: "http://json-schema.org/draft-07/schema#"
title: BlueprintSddStep05ImplementOutput
description: Structured implementation report produced at the end of SDD step 05.
type: object
additionalProperties: false
required:
  - ticket_id
  - stack_profile
  - test_commands
  - slices
  - validation_bundle_result
  - traceability_result
properties:
  ticket_id:
    type: string
  stack_profile:
    type: object
    additionalProperties: false
    required:
      - backend
      - frontend
      - test_automation
    properties:
      backend:
        type: string
      frontend:
        type: string
      test_automation:
        type: string
  test_commands:
    type: array
    items:
      type: string
  slices:
    type: array
    items:
      type: object
      additionalProperties: false
      required:
        - name
        - tests_written_count
        - red_confirmed
        - implementation_files
        - regression_result
        - commit_sha
      properties:
        name:
          type: string
        description:
          type: string
        tests_written_count:
          type: integer
          minimum: 0
        red_confirmed:
          type: boolean
        implementation_files:
          type: array
          items:
            type: string
        regression_result:
          type: string
          enum:
            - pass
            - fail
        tasks_completed:
          type: array
          items:
            type: string
        commit_sha:
          type: string
  validation_bundle_result:
    type: string
    enum:
      - pass
      - fail
      - not-applicable
  exception_rationale:
    type: string
  traceability_result:
    type: string
    enum:
      - clean
      - gaps-found
  expert_verdicts:
    type: array
    description: >-
      Per-expert verdict array merged by the orchestrator from the step05
      panel invocations (ADR-issue-364 § 4 dispatches a 5-expert panel at
      step05 in sequential-lens convergence mode). Each row is keyed by
      expert_slug per ADR-issue-364 § 6 and is carried on the C7
      outcome_details.expert_verdicts[] field per FR-007.
    items:
      type: object
      additionalProperties: false
      required:
        - verdict
        - findings
      oneOf:
        - required: [expert_slug_blueprint]
        - required: [expert_slug_extension]
      properties:
        expert_slug_blueprint:
          type: string
          description: >-
            Blueprint-baseline expert persona slug (sealed enum from
            ADR-issue-364 § 9). EXACTLY ONE OF this field OR
            `expert_slug_extension` MUST be populated per row (oneOf above).
            Pre-amendment verdicts that carried a flat `expert_slug` field
            MUST be tolerated by the orchestrator's merge layer and treated
            identically to `expert_slug_blueprint` when the value matches the
            blueprint-baseline enum (backwards-compatibility rule per
            design-contracts.md § C7 F-12 amended 2026-06-19).
        expert_slug_extension:
          type: string
          description: >-
            Consumer-overlay extension expert persona slug (open string from
            the consumer overlay's allowlist; per design-contracts.md § C7
            F-12 amendment 2026-06-19). EXACTLY ONE OF this field OR
            `expert_slug_blueprint` MUST be populated per row.
        verdict:
          type: string
          enum:
            - pass
            - revise
            - block
        findings:
          type: array
          items:
            type: object
```

## C7 Emission

At the end of this step, emit a C7 lifecycle event. Resolve variable values
from session context: `TICKET_ID` — the GitHub issue number; `SKILL_BASENAME`
— the `name:` value from this SKILL.md frontmatter; `OWNER_TEAM` — the GitHub
team slug owning this repository (e.g. `platform-team`); `WORK_ITEM_SLUG` —
the spec directory basename.

**Autonomous factory path (orchestrator #361):** the orchestrator emits the
C7 event after merging all expert verdicts into `outcome_details.expert_verdicts[]`.
It uses the `--extension-json` flag to attach the compact per-expert summary
(one `ExpertVerdictSummary` row per dispatched expert, per ADR-issue-364 § 9)
and `outcome_details.routing_keys` (per design-contracts § C7). The
orchestrator MUST NOT emit the event before all verdicts are collected and
merged.

**Local-CLI path (human-assisted, `local-cli` emitter):** the operator runs
this step without a panel. The `--extension-json` flag is omitted; the emitted
event will not carry `outcome_details.expert_verdicts[]`. This is expected —
expert-panel attribution is absent from local-CLI step events. If the
operator ran expert consultations manually they MAY author the extension JSON
and pass it via `--extension-json`, but this is not required.

```sh
uv run python3 scripts/bin/sdd/c7_emit.py emit \
  --ticket "$TICKET_ID" \
  --phase "implement" \
  --skill "$SKILL_BASENAME" \
  --owner-team "$OWNER_TEAM" \
  --slug "$WORK_ITEM_SLUG"
```

Stage and commit the emitted JSONL — this commit is part of the authorized
skill workflow and must land immediately so the audit record is durable:

```sh
git add "artifacts/c7/$WORK_ITEM_SLUG.jsonl"
git diff --cached --quiet || {
  git commit -m "chore($WORK_ITEM_SLUG): emit C7 lifecycle event"
  git push
}
```

Set `BLUEPRINT_SDD_C7_EMIT=0` to suppress; exactly one `c7-emission-opted-out` event is written per work-item slug (subsequent opted-out steps write nothing — the guard above skips the commit in that case).
**The LLM MUST NOT write events directly — invoke the helper only.**
