# ADR-2026-05-07 — Generalize Consumer-Seeded Feature Gates

**Status:** approved
**Date:** 2026-05-07
**Work item:** `specs/2026-05-07-generalize-consumer-seeded-feature-gates/`
**ADR technical decision sign-off:** approved

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
is a named, flag-controlled gate that prunes its `consumer_seeded_paths_when_enabled` from the
consumer repo at init time when disabled.

A new `blueprint-seed-feature FEATURE=<gate-id>` Make target is added to consumer repos
(propagated via the blueprint-managed Makefile layer). It fetches the blueprint source at the
consumer's pinned `BLUEPRINT_UPGRADE_REF`, resolves the named gate, renders its templates, and
writes the files to the consumer repo — allowing existing consumers to adopt a gate post-init
without re-seeding the full consumer-owned file set.

A new `blueprint-feature-gate-status` Make target (and `scripts/bin/blueprint/feature_gate_status.py`)
reads the consumer's local `blueprint/contract.yaml`, detects adoption for each gate (via
`BLUEPRINT_UPGRADE_SOURCE` / `enable_flag` in `repo.init.env`, or physical presence of any gate
path), and upserts entries into `AGENTS.backlog.md`. Open entries (`[ ]`) signal unadopted gates;
adopted gates have their entries marked done (`[x]`). The script exits 0 always — it is
informational. `upgrade_consumer_postcheck.sh` calls it as a non-blocking step after emitting
postcheck metrics, so consumers and coding agents learn about new optional features automatically
after each upgrade without blocking the gate result.

The `blueprint-consumer-upgrade` skill runbook is updated to include gate-status discovery as
Step 6 of the upgrade workflow, with explicit instructions for agents to run
`make blueprint-seed-feature FEATURE=<id>` for each open backlog entry.

The `app_catalog_scaffold_contract` section remains unchanged — it gates `feature_gated` paths
and has domain-specific validation with no analog in the new mechanism.

## Consequences

**Positive:**
- Future optional seeded files follow a single declared pattern instead of adding bespoke resolvers
- Consumer opt-in is explicit and documented in the contract
- Backward compatible: existing consumers without the gate env var get `enabled_by_default: false`
  behavior (paths pruned) — they never had the files, so no regression
- Post-init adoption is deterministic: `make blueprint-seed-feature` fetches from the pinned ref
  and writes only gate-scoped files; no re-seeding of the full consumer-owned set required
- Feature discovery is automatic: `make blueprint-feature-gate-status` (and the postcheck hook)
  upserts machine-readable `AGENTS.backlog.md` entries, visible to both humans and coding agents
  without requiring any manual contract inspection

**Negative:**
- Consumers that already manually added the Claude workflows will see no conflict (consumer-seeded
  paths are never touched by upgrade), but the gate has no effect on them post-init
- `blueprint-feature-gate-status` writes to `AGENTS.backlog.md`; consumers without that file get
  it created. Consumers who prefer not to have the file must opt out manually (no suppress flag)

## Alternatives Rejected

**Migrate `app_catalog_scaffold_contract` into the new list:** rejected because app_catalog carries
domain-specific manifest-marker and test-lane validation that has no generic counterpart. Merging
would either bloat the generic schema or lose validation.

**Bespoke resolver per gate (status quo for app_catalog):** rejected because it duplicates the
env-var resolution and pruning logic with no reuse.
