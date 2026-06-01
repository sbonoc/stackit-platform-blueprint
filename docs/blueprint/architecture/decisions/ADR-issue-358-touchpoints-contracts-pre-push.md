# ADR — Touchpoints Contract Test Pre-push Hook (issue #358)

- Status: proposed
- Date: 2026-06-01
- Deciders: platform-team
- Spec: specs/2026-06-01-issue-358-touchpoints-contracts-pre-push/spec.md
- ADR technical decision sign-off: pending

## Context

The blueprint seeds consumer repos with a `.pre-commit-config.yaml` template via `scripts/templates/blueprint/bootstrap/.pre-commit-config.yaml`. Consumer repos with the touchpoints module have the Pact HTTP consumer contract lane available via `make touchpoints-test-contracts`, but the baseline template provides no pre-push hook that runs it.

Without a pre-push gate two regression classes can slip through to CI undetected:

1. **Logic regressions** — a changed request shape, missing header, or broken Pact matcher causes the mock server to reject the interaction. The unit lane (`touchpoints-test-unit`) does not start a Pact mock server and cannot catch this.
2. **Environment-dependent failures** — contract tests using a native FFI library (e.g. Rust tokio via napi-rs) exhibit timing differences between macOS ARM64 (developer machines) and Linux x86_64 (CI runners); a test that passes locally can fail consistently on CI.

The first signal of either regression class is a CI failure on the remote branch, creating avoidable review latency and noise.

## Decision D-1 — Add `touchpoints-test-contracts-pre-push` hook to the template

**Decided:** Add the following hook stanza to `scripts/templates/blueprint/bootstrap/.pre-commit-config.yaml`:

```yaml
- id: touchpoints-test-contracts-pre-push
  name: touchpoints contract tests (pre-push)
  language: system
  entry: make touchpoints-test-contracts
  pass_filenames: false
  stages: [pre-push]
  files: ^(apps/touchpoints/.*\.(ts|vue|tsx)|apps/packages/api-client/src/.*\.ts)$
  always_run: false
```

**Rationale:** The hook is narrowly scoped to files that can break Pact consumer interactions (touchpoints TypeScript/Vue source and the api-client source). `always_run: false` ensures the hook is a no-op for pushes that do not touch these paths, preserving push latency for unrelated commits. Consumers without a `tests/contracts/` directory are unaffected because `make touchpoints-test-contracts` exits 0 when the test directory is absent.

**Trade-off:** A broken matcher injected via a dependency update (where no touchpoints source file is touched) will not be caught by this gate. An `always_run: true` alternative would cover this at the cost of running contract tests on every push. The file-scoped trigger is selected for consistency with all other template hooks that use file-scope triggers rather than always-run.

## Decision D-2 — No `contract.yaml` change

**Decided:** `blueprint/contract.yaml` is not modified.

**Rationale:** The hook addition is a quality-gate enhancement to the template only. It does not introduce a new module, contract field, or capability that consumers must declare or configure. The `touchpoints-test-contracts` make target is already in the app onboarding minimum targets contract; the hook is a delivery mechanism for that target, not a new contract surface.

## Decision D-3 — Rollout via standard blueprint upgrade

**Decided:** The hook ships in the next minor blueprint version. Consumers upgrade via the standard blueprint upgrade flow. A backport note is added to the upgrade documentation for consumers with Pact contract tests running earlier template versions.

**Rationale:** No special migration tooling is required because the change is additive. Consumers that do not upgrade retain no pre-push gate but do not regress. Consumers that do upgrade gain the gate without any manual configuration step.

## Consequences

- Consumers with touchpoints module and Pact contract tests gain a local pre-push gate that catches both regression classes before the remote branch is updated.
- Consumers without matching files or without a `tests/contracts/` directory see no behavioural change.
- The `touchpoints-test-contracts` make target must exit 0 when the contracts directory is absent; this must be verified during implementation and, if not already the case, a guard must be added.
