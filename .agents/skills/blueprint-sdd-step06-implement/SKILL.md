---
name: blueprint-sdd-step06-implement
description: Execute SDD Step 6 — implement the work item in TDD slices following plan.md, writing failing tests first then making them green, committing each slice to the existing Draft PR branch.
---

# Blueprint SDD Step 06 — Implement

## Step covered

- **Step 6** — Implement

## When to Use

Invoke after `SPEC_READY: true` and plan refinement are complete (Steps 4–5).
Do not start implementation before `SPEC_READY: true` is confirmed in `spec.md`.

## Actor

Software Engineer (invokes agent).

## Guardrails

1. Implementation MUST NOT start before `SPEC_READY: true` in `spec.md`.
2. Write ALL failing tests for a slice before writing any implementation code.
   Confirm each test fails with the expected error message.
3. Do not commit green tests without the corresponding implementation in the
   same commit — the red slice exists only to prove test correctness.
4. For filter or payload-transform changes: require positive-path unit assertions
   with matching fixture/request values. Empty-result-only assertions are insufficient.
5. For HTTP route/query/filter/new-endpoint scope: require local smoke via
   `make test-smoke-all-local` and capture pass/fail as test evidence in `pr_context.md`.
6. Translate reproducible pre-commit smoke/deterministic-check failures into
   failing automated tests first, then turn them green with the fix. Document
   deterministic exception rationale and follow-up owner when a true exception applies.
7. All commits go to the existing Draft PR branch — no new PR is opened.
8. Mark each task `[x]` in `tasks.md` as it completes.

## Workflow

```
For each slice in plan.md (follow the defined order):

SLICE N — FAILING TESTS (red)
1. Write all new unit and integration tests for this slice.
2. Run the targeted test command — confirm each new test FAILS:
   python3 -m pytest tests/<module>/ -v -k "<slice-marker>"
3. Do NOT write any implementation code yet.
4. Commit the red test file:
   git add tests/...
   git commit -m "test(<slug>): slice N — failing tests (red)"
   git push

SLICE N — IMPLEMENTATION (green)
5. Write the implementation to make the failing tests pass.
6. Run targeted tests — confirm all pass.
7. Run full suite — confirm no regressions:
   python3 -m pytest tests/ -q
8. Mark tasks complete in tasks.md.
9. Commit implementation + updated tasks.md:
   git add <implementation files> specs/YYYY-MM-DD-<slug>/tasks.md
   git commit -m "feat(<slug>): slice N — <brief description>"
   git push

Repeat for each slice in plan.md order.
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

If `make quality-hooks-fast` or a `curl`/smoke assertion fails deterministically
before the fix:
1. Write a failing automated test that reproduces the failure.
2. Confirm the test fails (red).
3. Fix the root cause — the test turns green.
4. If a true exception applies (e.g., environment-only failure), document the
   rationale and a follow-up owner in `pr_context.md` Deferred Proposals.

## Required Report Format

Return per slice:

1. Slice name and description.
2. Tests written (count) and confirmed-red result.
3. Implementation files changed.
4. Full-suite regression result (pass/fail counts).
5. Tasks marked complete in tasks.md (task IDs).
6. Commit SHA pushed.

After all slices:

7. Overall: all tasks complete in tasks.md? (yes/no)
8. Any open exception rationale documented?

## Useful Commands

```bash
python3 -m pytest tests/<module>/ -v -k "<marker>"   # targeted
python3 -m pytest tests/ -q                           # full suite
make quality-hooks-fast
make test-smoke-all-local                              # HTTP route scope only
```

## References

- Implementation checklist: `references/implement_checklist.md`
