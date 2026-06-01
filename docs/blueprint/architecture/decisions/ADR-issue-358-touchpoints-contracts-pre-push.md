# ADR — Pre-push Shift-left Hook Quintet (issue #358)

- Status: approved
- Date: 2026-06-01
- Deciders: platform-team
- Spec: specs/2026-06-01-issue-358-touchpoints-contracts-pre-push/spec.md
- ADR technical decision sign-off: approved

## Context

Issue #358 was filed by an agent from `sbonoc/dhe-marketplace` requesting a `touchpoints-test-contracts-pre-push` hook in the blueprint template. Investigation of `dhe-marketplace` revealed that the repo carries consumer-local pre-push hooks not seeded by the blueprint template. Scope was expanded to include all five lanes for a complete shift-left pattern:

| Hook ID | Make target | Files scope | Consumer postmortem |
|---|---|---|---|
| `touchpoints-test-unit-pre-push` | `make touchpoints-test-unit` | `^apps/touchpoints/.*\.(ts\|vue\|tsx)$` | PR #75 |
| `touchpoints-test-contracts-pre-push` | `make touchpoints-test-contracts` | `^(apps/touchpoints/.*\.(ts\|vue\|tsx)\|apps/packages/api-client/src/.*\.ts)$` | (issue #358) |
| `backend-test-unit-pre-push` | `make backend-test-unit` | `^(apps/backend/\|tests/backend/).*\.py$` | PR #78 |
| `backend-test-contracts-pre-push` | `make backend-test-contracts` | `^(apps/backend/\|tests/backend/).*\.py$` | (pattern symmetry) |
| `touchpoints-test-integration-pre-push` | `make touchpoints-test-integration` | `^(apps/touchpoints/.*\.(ts\|vue\|tsx)\|apps/packages/api-client/src/.*\.ts)$` | (pattern symmetry) |

Without these pre-push gates, five regression classes can slip through to CI undetected:

1. **Vitest composable failures** — role-string mismatches and composable behaviour regressions not caught by Python-only backend runs (postmortem: PR #75).
2. **Pact interaction failures** — broken request shapes, missing headers, FFI timing differences between macOS ARM64 and Linux x86_64; the unit lane cannot catch these because it never starts a Pact mock server.
3. **Pytest DSL/query regressions** — OpenSearch query and DSL-structure regressions not caught by frontend-only runs (postmortem: PR #78).
4. **Pact provider verification regressions** — Pact provider test failures that slip past unit-only runs.
5. **Integration-lane API-client regressions** — API-client and touchpoints integration test failures that require a live server and are not caught by unit or contract stubs.

## Decision D-1 — Add all five hooks to the template

**Decided:** Add all five hook stanzas to `scripts/templates/blueprint/bootstrap/.pre-commit-config.yaml` in a single change, in order: `touchpoints-test-unit-pre-push`, `touchpoints-test-contracts-pre-push`, `backend-test-unit-pre-push`, `backend-test-contracts-pre-push`, `touchpoints-test-integration-pre-push`.

**Rationale:** Shipping only the contracts hook (the original issue scope) would leave new consumers with an asymmetric template. Both unit hooks are validated by documented postmortems from a production consumer repo. Adding all five delivers the complete shift-left pattern in one atomic PR.

**Trade-off:** Broader scope than the original issue. Accepted: the postmortem evidence and the template-completeness argument outweigh the scope discipline of staying narrowly on-issue.

## Decision D-2 — File-scoped trigger (`always_run: false`) for all five hooks

**Decided:** All five hooks use `always_run: false` with lane-specific file globs.

**Rationale:** Consistent with every other pre-push hook in the template. Keeps push latency minimal for pushes that do not touch the relevant source files.

**Trade-off:** A regression injected via a dependency update (where no source file is touched) is not caught by any of these gates. An `always_run: true` alternative would cover this at the cost of running all five test lanes on every push regardless of scope.

## Decision D-3 — No `contract.yaml` change

**Decided:** `blueprint/contract.yaml` is not modified.

**Rationale:** Hook additions are quality-gate enhancements to the template only; the five invoked make targets are already in the app onboarding minimum targets contract.

## Decision D-4 — Rollout via standard blueprint upgrade

**Decided:** All five hooks ship in the next minor blueprint version. A backport note is added for consumers running earlier template versions.

**Rationale:** Additive change; no migration tooling required.

## Decision D-5 — Expand from three to five hooks (pattern symmetry)

**Decided:** `backend-test-contracts-pre-push` and `touchpoints-test-integration-pre-push` are promoted from deferred proposals to normative scope and implemented in the same PR.

**Rationale:** Both hooks follow the identical `always_run: false` + file-scope pattern. The backend-contracts hook covers the same Python surface as the backend-unit hook (FR-003) and requires no additional file-scope reasoning. The touchpoints-integration hook covers the same TypeScript + api-client surface as the contracts hook (FR-002), making the pattern pair symmetric across both test lanes. Shipping all five in one atomic change avoids partial template states that would require a follow-up PR with identical structural effort.

**Trade-off:** Slightly wider PR scope; no new implementation risk introduced since all five make targets pre-exist in `make/platform.mk`.

## Consequences

- Consumers gain five file-scoped pre-push gates covering the Vitest unit, Pact contract, pytest unit, Pact provider, and touchpoints integration lanes.
- Consumers without matching files or relevant test directories see no behavioural change (`always_run: false`).
- All five make targets must exit 0 when the relevant test directory is absent; verified during implementation (T-004).
