# ADR: Make Target Override-Point Variables for Consumer Customisation

- **Status:** proposed
- **ADR technical decision sign-off:** pending
- **Date:** 2026-04-30
- **Issues:** https://github.com/sbonoc/stackit-platform-blueprint/issues/241
- **Work item:** `specs/2026-04-30-issue-241-make-override-warnings/`

## Context

`make/blueprint.generated.mk` is included first in the consumer root `Makefile`,
before the consumer-owned `make/platform.mk`. When a consumer needs to customise
the behaviour of a blueprint-managed target (for example, changing `spec-scaffold`'s
default `--track` value from `blueprint` to `consumer`, or redirecting
`blueprint-uplift-status` to a consumer-owned enrichment script), they must
re-define the entire target in `platform.mk`. GNU Make detects the re-definition
and emits:

```
make/platform.mk:N: warning: overriding commands for target 'spec-scaffold'
make/blueprint.generated.mk:M: warning: ignoring old commands for target 'spec-scaffold'
```

GNU Make provides no per-target suppression mechanism for these warnings. The
warning pair appears on every `make` invocation (including `make help`) and adds
noise to CI logs. Consumers cannot suppress the warnings without restructuring the
entire include order.

Two targets are commonly affected:
- `spec-scaffold` — blueprint defaults `--track blueprint`; consumer legitimately
  defaults to `--track consumer` (different skeleton set, different branch prefix)
- `blueprint-uplift-status` — blueprint calls
  `scripts/bin/blueprint/uplift_status.sh`; consumer may need a consumer-owned
  script that calls through or enriches the output with consumer-specific context

## Decision

**Expose `?=` override-point variables in `blueprint.generated.mk` for each
customisable recipe value. Consumers override the variable with `:=` in
`platform.mk` instead of re-defining the target.**

### Variables added

```makefile
# In blueprint.generated.mk (rendered from template)
SPEC_SCAFFOLD_DEFAULT_TRACK ?= blueprint
BLUEPRINT_UPLIFT_STATUS_SCRIPT ?= scripts/bin/blueprint/uplift_status.sh
```

### Recipe changes

```makefile
spec-scaffold: ## Scaffold SDD work-item documents ...
    ...
    @python3 scripts/bin/blueprint/spec_scaffold.py \
        --slug "$(SPEC_SLUG)" \
        --track "$(or $(SPEC_TRACK),$(SPEC_SCAFFOLD_DEFAULT_TRACK))" \
        ...

blueprint-uplift-status: ## Report blueprint uplift convergence status ...
    @$(BLUEPRINT_UPLIFT_STATUS_SCRIPT)
```

### Consumer usage (no target re-definition required)

```makefile
# make/platform.mk (consumer-owned, included after blueprint.generated.mk)
SPEC_SCAFFOLD_DEFAULT_TRACK := consumer
BLUEPRINT_UPLIFT_STATUS_SCRIPT := scripts/bin/platform/blueprint/uplift_status.sh
```

### Why `?=` works with this include order

The consumer root `Makefile` includes `blueprint.generated.mk` first, then
`platform.mk`. When `blueprint.generated.mk` is processed, `?=` records the
default only if the variable is not yet defined. When `platform.mk` is processed
next, `:=` unconditionally overrides the value. The target recipe body is evaluated
at recipe-expansion time (not at parse time), so it sees the final value of the
variable — the consumer's override — without any re-definition of the target.

## Options Considered

### Option A (selected): `?=` configuration variables in `blueprint.generated.mk`

- Minimal change: two variable declarations, two recipe token substitutions
- Idiomatic GNU Make — `?=` / `:=` pattern is the standard override mechanism
- No structural change to include order or target definition
- Fully backward compatible: consumers not setting the variable see identical behaviour
- Consumer change: set a variable, remove the old target re-definition

### Option B: Restructure include order (platform-first, blueprint-second)

- Would require changing the root `Makefile` template to include `platform.mk`
  before `blueprint.generated.mk`
- Consumer targets defined in `platform.mk` would then shadow blueprint targets
  without warnings — but would also require blueprint targets to use `?=` late-
  binding throughout, which is a broader structural change
- Higher blast radius; risk of breaking existing targets that assume blueprint-first
  ordering
- Not selected

### Option C: Global `--warn-undefined-variables` suppression

- Not target-specific; suppresses legitimate variable-undefined warnings that are
  useful for diagnosing consumer misconfiguration
- Not selected

## Consequences

- **Positive:** consumers eliminate override warnings by switching from target
  re-definition to variable override — a one-line change in `platform.mk`
- **Positive:** blueprint-managed targets remain intact; upgrade cycles do not
  produce merge conflicts in `platform.mk` for these customisation points
- **Positive:** the `?=` default values match the existing hardcoded values —
  zero behavior change for consumers who do not set the variables
- **Neutral:** the override-point surface is intentionally minimal (two targets);
  additional targets require separate work items when consumer override needs are
  identified
- **Negative:** none identified
