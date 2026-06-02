# Consumer Quality Gates

This guide explains how to extend the blueprint quality gate hierarchy using the
two consumer extension targets delivered by blueprint upgrade.

## Overview

Blueprint defines a standard quality gate hierarchy (`quality-ci-fast`,
`quality-ci-strict`, `quality-ci-blueprint`, pre-push hooks). To plug custom
test tiers into this hierarchy without touching blueprint-managed files, use
the two extension stub targets:

| Target | When it runs | Where to override |
|---|---|---|
| `quality-consumer-pre-push` | pre-push (always) | `make/platform.mk` |
| `quality-consumer-ci` | final step of `quality-ci-blueprint` (CI) | `make/platform.mk` |

Both targets default to no-op (`@true`). Consumers who do not override them see
no behavior change.

## How to Override

Add overrides to `make/platform.mk` (consumer-owned, never overwritten on
blueprint upgrade):

```makefile
# make/platform.mk

quality-consumer-pre-push:
	@$(MAKE) backend-test-unit
	@$(MAKE) touchpoints-test-unit

quality-consumer-ci:
	@$(MAKE) touchpoints-test-component
```

Override bodies can call any Make target available in the repo.

## Tier Placement

| Tier | Target | Guidance |
|---|---|---|
| Tier 1 (pre-push, fast) | `quality-consumer-pre-push` | Unit tests that finish in seconds. Runs before every push. Keep it fast. |
| Tier 2 (CI, component) | `quality-consumer-ci` | Component or integration tests acceptable to run only in CI. |

## Why This Pattern

- **Upgrade-safe**: Both targets are defined in `make/blueprint.generated.mk`
  (blueprint-managed). Overrides live in `make/platform.mk` (consumer-owned).
  Blueprint upgrades never overwrite `platform.mk`, so overrides accumulate
  without merge conflicts.
- **No pre-commit file edits required**: Adding hooks to `.pre-commit-config.yaml`
  directly causes merge conflicts on upgrade. The `quality-consumer-pre-push` hook
  calls `make quality-consumer-pre-push` — consumers extend the hook by overriding
  the target, not by editing the YAML.

## Rollback

Remove the override bodies from `make/platform.mk`. The stubs revert to `@true`
(no-op) on next make invocation.

## Template-Seeded Pre-Push Hooks (added in blueprint 2026-06-01 / issue #358)

Five file-scoped pre-push hooks were added to the bootstrap template. Consumers
on an earlier template version can backport them manually by adding the following
stanzas to `.pre-commit-config.yaml` (in the `repo: local` section, before the
`quality-consumer-pre-push` hook):

```yaml
- id: touchpoints-test-unit-pre-push
  name: touchpoints unit tests (pre-push)
  language: system
  entry: make touchpoints-test-unit
  pass_filenames: false
  stages: [pre-push]
  files: ^apps/touchpoints/.*\.(ts|vue|tsx)$
  always_run: false
- id: touchpoints-test-contracts-pre-push
  name: touchpoints contract tests (pre-push)
  language: system
  entry: make touchpoints-test-contracts
  pass_filenames: false
  stages: [pre-push]
  files: ^(apps/touchpoints/.*\.(ts|vue|tsx)|apps/packages/api-client/src/.*\.ts|tests/touchpoints/contracts/.*\.py)$
  always_run: false
- id: backend-test-unit-pre-push
  name: backend unit tests (pre-push)
  language: system
  entry: make backend-test-unit
  pass_filenames: false
  stages: [pre-push]
  files: ^(apps/backend/|tests/backend/).*\.py$
  always_run: false
- id: backend-test-contracts-pre-push
  name: backend contract tests (pre-push)
  language: system
  entry: make backend-test-contracts
  pass_filenames: false
  stages: [pre-push]
  files: ^(apps/backend/|tests/backend/).*\.py$
  always_run: false
- id: touchpoints-test-integration-pre-push
  name: touchpoints integration tests (pre-push)
  language: system
  entry: make touchpoints-test-integration
  pass_filenames: false
  stages: [pre-push]
  files: ^(apps/touchpoints/.*\.(ts|vue|tsx)|apps/packages/api-client/src/.*\.ts)$
  always_run: false
```

Each hook sets `always_run: false` so it is skipped when no matching files are
staged for the push. Consumers without a `tests/backend/` directory or without
a Vitest / Pact setup see no behavioral change — the relevant make targets exit
0 when the test directory is absent.

> **Deduplication note:** If your `quality-consumer-pre-push` override in `make/platform.mk`
> already calls `make touchpoints-test-unit`, `make backend-test-unit`, or any of the other
> four targets directly, those lanes will run twice on pushes that touch matching files — once
> from the file-scoped hook and once from the always-run consumer hook. Remove the duplicate
> calls from your `quality-consumer-pre-push` override after upgrading to avoid the redundancy.
