# Architecture — Generalize Consumer-Seeded Feature Gates

## Context Metadata
- Work item: 2026-05-07-generalize-consumer-seeded-feature-gates
- Owner: Platform Engineering
- Date: 2026-05-07

## Context

The blueprint's init engine (`make blueprint-init-repo`) seeds a fixed set of files into every
consumer repo via `consumer_seeded_paths`. Once seeded, those files are permanently consumer-owned
— the upgrade engine hard-skips the entire `consumer_seeded` class forever.

Two separate bespoke mechanisms exist for conditional init-time file management:

1. **`optional_modules`** — gates infra/Terraform/Helm/ArgoCD scaffold paths. Seeded paths are in
   `conditional_scaffold`. Not relevant here; these are blueprint-managed resources, not
   consumer-owned.

2. **`app_catalog_scaffold_contract`** — gates `feature_gated` paths (`apps/catalog/`,
   `apps/catalog/manifest.yaml`, `apps/catalog/versions.lock`) and validates domain-specific
   manifest markers, test-lane targets, and docs paths. Its path-pruning logic lives in
   `init_repo_contract.py:resolve_app_catalog_scaffold_contract()`.

Neither mechanism addresses the new need: **optionally seeding a subset of `consumer_seeded` paths
based on a feature flag**. The Claude AI integration (PR #252) introduced two GH Actions workflow
files (`.github/workflows/claude.yml`, `.github/workflows/claude-code-review.yml`) that should be
consumer-seeded but only when the consumer opts in.

Adding a second bespoke resolver alongside `resolve_app_catalog_scaffold_contract` would duplicate
the same env-var-gated pruning pattern a second time.

## Decision

Introduce a **generic `consumer_seeded_feature_gates` list** in `blueprint/contract.yaml`. Each
entry declares one gate: an ID, enable flag, default state, description, and the list of
`consumer_seeded` paths to prune when the gate is disabled.

The init engine resolves all gates at init time and prunes disabled-gate paths after the normal
`consumer_seeded` seeding pass — identical to the app_catalog pruning flow, but generic.

The `app_catalog_scaffold_contract` section remains unchanged. It gates `feature_gated` paths (not
`consumer_seeded`) and carries domain-specific validation (manifest markers, test lanes, docs
paths) that has no analog in the new generic mechanism.

## Bounded Context

This change is scoped entirely to the **blueprint init subsystem**:

- `blueprint/contract.yaml` — schema addition (new top-level `consumer_seeded_feature_gates` list)
- `scripts/lib/blueprint/init_repo_contract.py` — new resolver + updated seeding function
- `scripts/bin/blueprint/validate_contract.py` — new structural validator for the gates list
- `scripts/bin/blueprint/seed_feature.py` — new CLI backing the `blueprint-seed-feature` Make target
- `make/blueprint.generated.mk` — new `blueprint-seed-feature` target
- `scripts/templates/consumer/init/.github/workflows/` — two new `.tmpl` files
- `tests/blueprint/` — unit tests

No changes to:
- Upgrade engine (`upgrade_consumer.py`) — the paths are in `consumer_seeded`, already hard-skipped
- `app_catalog_scaffold_contract` validation — orthogonal domain
- `optional_modules` — orthogonal scope

## Module Structure

```
blueprint/contract.yaml
  └─ consumer_seeded_feature_gates:         ← NEW generic list
       - id: claude_ai_integration          ← first gate (Claude workflows)
         enable_flag: CLAUDE_AI_ENABLED
         enabled_by_default: false
         description: ...
         consumer_seeded_paths_when_enabled:
           - .github/workflows/claude.yml
           - .github/workflows/claude-code-review.yml

scripts/lib/blueprint/init_repo_contract.py
  └─ resolve_consumer_seeded_feature_gates()  ← NEW: reads list, returns [(id, enabled, paths)]
  └─ seed_consumer_owned_files()              ← UPDATED: prune disabled-gate paths after seeding

scripts/bin/blueprint/validate_contract.py
  └─ _validate_consumer_seeded_feature_gates()  ← NEW: structural validator

scripts/bin/blueprint/seed_feature.py         ← NEW: CLI backing the Make target
  └─ fetches blueprint source at BLUEPRINT_UPGRADE_REF
  └─ resolves gate by ID from fetched source
  └─ renders + writes gate paths to consumer repo

make/blueprint.generated.mk                   ← UPDATED: add blueprint-seed-feature target

scripts/templates/consumer/init/.github/workflows/
  └─ claude.yml.tmpl                ← NEW
  └─ claude-code-review.yml.tmpl    ← NEW
```

## Flows

```mermaid
flowchart TD
    A[make blueprint-init-repo] --> B[seed_consumer_owned_files]
    B --> C[Seed ALL consumer_seeded_paths from templates]
    C --> D[resolve_consumer_seeded_feature_gates]
    D --> E{For each gate}
    E -->|enabled| F[Keep paths as-is]
    E -->|disabled| G[Prune gate paths from consumer repo]
    F --> H[Continue]
    G --> H
    H --> I[Init complete]
```

Caption: Init-time seeding flow — gate resolution inserts a conditional prune step after the
fixed consumer_seeded seeding pass.

```mermaid
flowchart TD
    A["make blueprint-seed-feature FEATURE=<id>"] --> B[Read BLUEPRINT_UPGRADE_REF from blueprint/repo.init.env]
    B --> C[Fetch blueprint source at pinned ref into tempdir]
    C --> D[Read consumer_seeded_feature_gates from fetched contract]
    D --> E{Gate ID found?}
    E -->|no| F[Exit non-zero with diagnostic]
    E -->|yes| G[Render gate paths from fetched templates]
    G --> H[Write rendered files to consumer repo]
    H --> I[Done]
```

Caption: `blueprint-seed-feature` flow for existing consumers adopting a gate post-init — always
uses the consumer's pinned blueprint ref, never touches files outside the target gate.

## Diagram Type Rationale

`flowchart TD` — control flow within the init script is the primary concern; no cross-service
interactions or state machines involved.

## ADR

`docs/blueprint/architecture/decisions/ADR-2026-05-07-generalize-consumer-seeded-feature-gates.md`
— Status: proposed
