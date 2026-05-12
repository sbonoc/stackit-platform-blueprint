# Tasks

## Gate Checks (Required Before Implementation)
- [ ] G-001 Confirm `SPEC_READY=true` in `spec.md`
- [ ] G-002 Confirm open questions and unresolved alternatives are `0`
- [ ] G-003 Confirm required sign-offs are approved (Product, Architecture, Security, Operations)
- [ ] G-004 Confirm `Applicable Guardrail Controls` section includes `SDD-C-###` IDs
- [ ] G-005 Confirm `Implementation Stack Profile` section is fully populated

## Slice 1 — Restore --ignore-workspace (#272, FR-001, AC-001)

### Test (Red)
- [ ] T-101 Write pytest regression fixture: read `scripts/lib/docs/site.sh`; assert all three pnpm invocations (`docs_pnpm_install`, `docs_pnpm_build`, `docs_pnpm_start`) contain `--ignore-workspace`; confirm RED

### Implementation
- [ ] T-001 Restore `--ignore-workspace` flag to `docs_pnpm_install` in `scripts/lib/docs/site.sh`
- [ ] T-002 Restore `--ignore-workspace` flag to `docs_pnpm_build` in `scripts/lib/docs/site.sh`
- [ ] T-003 Restore `--ignore-workspace` flag to `docs_pnpm_start` in `scripts/lib/docs/site.sh`
- [ ] T-004 Restore the explanatory comment alongside `docs_pnpm_install`

### Verify
- [ ] T-201 Run `uv run python3 -m pytest tests/infra/ -k "issue_272" -v` → PASS (GREEN)
- [ ] T-202 Run `make docs-build && make docs-smoke` → PASS
- [ ] T-203 Run `make quality-hooks-fast` → no new failures

## Slice 2 — Improve pnpm version assertion error message (#273, FR-002, AC-002)

### Test (Red)
- [ ] T-102 Write pytest regression fixture: read `scripts/lib/docs/site.sh`; assert the `log_fatal` message in `_docs_assert_pnpm_version` contains "root package.json" and "corepack prepare"; confirm RED

### Implementation
- [ ] T-005 Replace the single-line `log_fatal` message in `_docs_assert_pnpm_version` with a multi-part message naming all three pnpm version sources (docs `package.json`, root `package.json`, CI corepack prepare pin)

### Verify
- [ ] T-204 Run `uv run python3 -m pytest tests/infra/ -k "issue_273" -v` → PASS (GREEN)
- [ ] T-205 Run `make quality-hooks-fast` → no new failures

## Accessibility Testing (Normative)
- [ ] T-A01 NFR-A11Y-001 compliance scope: N/A — no UI components; pure shell script changes with no user-facing rendering surface.

## Validation and Release Readiness
- [ ] T-301 Run full validation bundle: `make infra-validate && make quality-hooks-run`
- [ ] T-302 Attach evidence checksums to `traceability.md`
- [ ] T-303 Confirm no stale TODOs or dead code in touched scope
- [ ] T-304 Run `make docs-build && make docs-smoke` → PASS
- [ ] T-305 Run `make quality-hardening-review` → PASS

## Publish
- [ ] P-001 Update `hardening_review.md` with findings fixed and proposals-only section
- [ ] P-002 Update `pr_context.md` with requirement/contract coverage, key reviewer files, validation evidence, and rollback notes
- [ ] P-003 Ensure PR description follows repository template and references `pr_context.md`
- [ ] P-004 Close GH issues #272, #273 via `Closes` references in PR description

## App Onboarding Minimum Targets (Normative)
- [ ] A-001 `apps-bootstrap` — N/A: no app delivery workflow affected by this tooling fix
- [ ] A-002 `apps-smoke` — N/A
- [ ] A-003 `backend-test-unit` — N/A
- [ ] A-004 `backend-test-integration` — N/A
- [ ] A-005 `backend-test-contracts` — N/A
- [ ] A-006 `backend-test-e2e` — N/A
- [ ] A-007 `touchpoints-test-unit` — N/A
- [ ] A-008 `touchpoints-test-integration` — N/A
- [ ] A-009 `touchpoints-test-contracts` — N/A
- [ ] A-010 `touchpoints-test-e2e` — N/A
- [ ] A-011 `test-unit-all` — N/A
- [ ] A-012 `test-integration-all` — N/A
- [ ] A-013 `test-contracts-all` — N/A
- [ ] A-014 `test-e2e-all-local` — N/A
- [ ] A-015 `infra-port-forward-start` — N/A
- [ ] A-016 `infra-port-forward-stop` — N/A
- [ ] A-017 `infra-port-forward-cleanup` — N/A
