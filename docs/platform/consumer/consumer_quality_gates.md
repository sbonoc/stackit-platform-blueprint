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
