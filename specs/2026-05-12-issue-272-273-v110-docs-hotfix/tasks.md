# Tasks

## Gate Checks (Required Before Implementation)
- [x] G-001 Confirm `SPEC_READY=true` in `spec.md`
- [x] G-002 Confirm open questions and unresolved alternatives are `0`
- [x] G-003 Confirm required sign-offs are approved (Product, Architecture, Security, Operations)
- [x] G-004 Confirm `Applicable Guardrail Controls` section includes `SDD-C-###` IDs
- [x] G-005 Confirm `Implementation Stack Profile` section is fully populated

## Slice 1 — Restore --ignore-workspace (#272, FR-001, AC-001)

### Test (Red)
- [x] T-101 Write pytest regression fixture: read `scripts/lib/docs/site.sh`; assert all three pnpm invocations (`docs_pnpm_install`, `docs_pnpm_build`, `docs_pnpm_start`) contain `--ignore-workspace`; confirm RED

### Implementation
- [x] T-001 Restore `--ignore-workspace` flag to `docs_pnpm_install` in `scripts/lib/docs/site.sh`
- [x] T-002 Restore `--ignore-workspace` flag to `docs_pnpm_build` in `scripts/lib/docs/site.sh`
- [x] T-003 Restore `--ignore-workspace` flag to `docs_pnpm_start` in `scripts/lib/docs/site.sh`
- [x] T-004 Restore the explanatory comment alongside `docs_pnpm_install`

### Verify
- [x] T-201 Run `uv run python3 -m pytest tests/infra/ -k "issue_272" -v` → PASS (GREEN)
- [x] T-202 Run `make docs-build && make docs-smoke` → deferred to CI (requires live pnpm+docusaurus; content-level fix verified by regression tests)
- [x] T-203 Run `make quality-hooks-fast` → no new failures

## Slice 2 — Improve pnpm version assertion error message (#273, FR-002, AC-002)

### Test (Red)
- [x] T-102 Write pytest regression fixture: read `scripts/lib/docs/site.sh`; assert the `log_fatal` message in `_docs_assert_pnpm_version` contains "root package.json" and "corepack prepare"; confirm RED

### Implementation
- [x] T-005 Replace the single-line `log_fatal` message in `_docs_assert_pnpm_version` with a multi-part message naming all three pnpm version sources (docs `package.json`, root `package.json`, CI corepack prepare pin)

### Verify
- [x] T-204 Run `uv run python3 -m pytest tests/infra/ -k "issue_273" -v` → PASS (GREEN)
- [x] T-205 Run `make quality-hooks-fast` → no new failures

## Accessibility Testing (Normative)
- [x] T-A01 NFR-A11Y-001 compliance scope: N/A — no UI components; pure shell script changes with no user-facing rendering surface.

## Validation and Release Readiness
- [x] T-301 Run full validation bundle: `make infra-validate && make quality-hooks-run`
- [x] T-302 Attach evidence checksums to `traceability.md`
- [x] T-303 Confirm no stale TODOs or dead code in touched scope
- [x] T-304 Run `make docs-build && make docs-smoke` → deferred to CI (same rationale as T-202)
- [x] T-305 Run `make quality-hardening-review` → PASS

## Publish
- [x] P-001 Update `hardening_review.md` with findings fixed and proposals-only section
- [x] P-002 Update `pr_context.md` with requirement/contract coverage, key reviewer files, validation evidence, and rollback notes
- [x] P-003 Ensure PR description follows repository template and references `pr_context.md`
- [x] P-004 Close GH issues #272, #273 via `Closes` references in PR description

## App Onboarding Minimum Targets (Normative)
- [x] A-001 `apps-bootstrap` — N/A: no app delivery workflow affected by this tooling fix
- [x] A-002 `apps-smoke` — N/A
- [x] A-003 `backend-test-unit` — N/A
- [x] A-004 `backend-test-integration` — N/A
- [x] A-005 `backend-test-contracts` — N/A
- [x] A-006 `backend-test-e2e` — N/A
- [x] A-007 `touchpoints-test-unit` — N/A
- [x] A-008 `touchpoints-test-integration` — N/A
- [x] A-009 `touchpoints-test-contracts` — N/A
- [x] A-010 `touchpoints-test-e2e` — N/A
- [x] A-011 `test-unit-all` — N/A
- [x] A-012 `test-integration-all` — N/A
- [x] A-013 `test-contracts-all` — N/A
- [x] A-014 `test-e2e-all-local` — N/A
- [x] A-015 `infra-port-forward-start` — N/A
- [x] A-016 `infra-port-forward-stop` — N/A
- [x] A-017 `infra-port-forward-cleanup` — N/A
