# ADR — Pre-push Shift-left Hook Triad (issue #358)

- Status: approved
- Date: 2026-06-01
- Deciders: platform-team
- Spec: specs/2026-06-01-issue-358-touchpoints-contracts-pre-push/spec.md
- ADR technical decision sign-off: approved

## Context

Issue #358 was filed by an agent from `sbonoc/dhe-marketplace` requesting a `touchpoints-test-contracts-pre-push` hook in the blueprint template. Investigation of `dhe-marketplace` revealed that the repo carries three consumer-local pre-push hooks that are not seeded by the blueprint template:

| Hook ID | Make target | Files scope | Consumer postmortem |
|---|---|---|---|
| `touchpoints-test-unit-pre-push` | `make touchpoints-test-unit` | `^apps/touchpoints/.*\.(ts\|vue\|tsx)$` | PR #75 |
| `touchpoints-test-contracts-pre-push` | `make touchpoints-test-contracts` | `^(apps/touchpoints/.*\.(ts\|vue\|tsx)\|apps/packages/api-client/src/.*\.ts)$` | (issue #358) |
| `backend-test-unit-pre-push` | `make backend-test-unit` | `^(apps/backend/\|tests/backend/).*\.py$` | PR #78 |

Without these pre-push gates, three regression classes can slip through to CI undetected:

1. **Vitest composable failures** — role-string mismatches and composable behaviour regressions not caught by Python-only backend runs (postmortem: PR #75).
2. **Pact interaction failures** — broken request shapes, missing headers, FFI timing differences between macOS ARM64 and Linux x86_64; the unit lane cannot catch these because it never starts a Pact mock server.
3. **Pytest DSL/query regressions** — OpenSearch query and DSL-structure regressions not caught by frontend-only runs (postmortem: PR #78).

## Decision D-1 — Add all three hooks to the template

**Decided:** Add all three hook stanzas to `scripts/templates/blueprint/bootstrap/.pre-commit-config.yaml` in a single change, in order: `touchpoints-test-unit-pre-push`, `touchpoints-test-contracts-pre-push`, `backend-test-unit-pre-push`.

**Rationale:** Shipping only the contracts hook (the original issue scope) would leave new consumers with an asymmetric template — they would have contract pre-push but not unit pre-push. Both unit hooks are validated by documented postmortems from a production consumer repo. Adding all three in one PR is the correct atomic unit of change.

**Trade-off:** Broader scope than the original issue. Accepted: the postmortem evidence and the template-completeness argument outweigh the scope discipline of staying narrowly on-issue.

## Decision D-2 — File-scoped trigger (`always_run: false`) for all three hooks

**Decided:** All three hooks use `always_run: false` with lane-specific file globs.

**Rationale:** Consistent with every other pre-push hook in the template. Keeps push latency minimal for pushes that do not touch the relevant source files.

**Trade-off:** A regression injected via a dependency update (where no source file is touched) is not caught by any of these gates. An `always_run: true` alternative would cover this at the cost of running all three test lanes on every push regardless of scope.

## Decision D-3 — No `contract.yaml` change

**Decided:** `blueprint/contract.yaml` is not modified.

**Rationale:** Hook additions are quality-gate enhancements to the template only; the three invoked make targets are already in the app onboarding minimum targets contract.

## Decision D-4 — Rollout via standard blueprint upgrade

**Decided:** All three hooks ship in the next minor blueprint version. A backport note is added for consumers running earlier template versions.

**Rationale:** Additive change; no migration tooling required.

## Consequences

- Consumers gain three file-scoped pre-push gates covering the Vitest unit, Pact contract, and pytest unit lanes.
- Consumers without matching files or relevant test directories see no behavioural change (`always_run: false`).
- All three make targets must exit 0 when the relevant test directory is absent; this must be verified during implementation.
