# ADR-2026-05-07 — Generalize Consumer-Seeded Feature Gates

**Status:** proposed
**Date:** 2026-05-07
**Work item:** `specs/2026-05-07-generalize-consumer-seeded-feature-gates/`

## Context

The blueprint seeds a fixed set of consumer-owned files at `make blueprint-init-repo` via
`consumer_seeded_paths`. Adding the Claude AI integration workflows (PR #252) requires those files
to be optional — seeded only when the consumer opts in via an environment variable flag.

Two existing bespoke mechanisms exist (`optional_modules`, `app_catalog_scaffold_contract`) but
neither is a fit: `optional_modules` gates infra scaffold paths; `app_catalog_scaffold_contract`
gates `feature_gated` paths with domain-specific validation. Adding a third bespoke resolver
would duplicate the same env-var-gated pruning pattern without abstraction.

## Decision

Introduce a generic `consumer_seeded_feature_gates` list in `blueprint/contract.yaml`. Each entry
is a named, flag-controlled gate that pruning its `consumer_seeded_paths_when_enabled` from the
consumer repo at init time when disabled.

The `app_catalog_scaffold_contract` section remains unchanged — it gates `feature_gated` paths
and has domain-specific validation with no analog in the new mechanism.

## Consequences

**Positive:**
- Future optional seeded files follow a single declared pattern instead of adding bespoke resolvers
- Consumer opt-in is explicit and documented in the contract
- Backward compatible: existing consumers without the gate env var get `enabled_by_default: false`
  behavior (paths pruned) — they never had the files, so no regression

**Negative:**
- Consumers that already manually added the Claude workflows will see no conflict (consumer-seeded
  paths are never touched by upgrade), but the gate has no effect on them post-init

## Alternatives Rejected

**Migrate `app_catalog_scaffold_contract` into the new list:** rejected because app_catalog carries
domain-specific manifest-marker and test-lane validation that has no generic counterpart. Merging
would either bloat the generic schema or lose validation.

**Bespoke resolver per gate (status quo for app_catalog):** rejected because it duplicates the
env-var resolution and pruning logic with no reuse.
