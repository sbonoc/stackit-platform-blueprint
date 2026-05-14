# ADR: Versioned Consumer-Side Workarounds Catalogue

**Status:** proposed
**Date:** 2026-05-14
**Issue:** #268
**Spec:** `specs/2026-05-14-issue-268-consumer-workarounds-catalogue/`

## Context

When the blueprint ships a release with known upstream defects, every consumer that upgrades to that release independently rediscovers the same defects, hand-applies the same workarounds, and carries unique drift until the upstream fix lands. During the `dhe-marketplace` v1.7.0 → v1.10.0 upgrade, four upstream defects (#258, #259, #260, #261) each required a consumer-side workaround discovered by trial-and-error, costing ~30 minutes of extra upgrade time.

The blueprint already tracks its own bugs (they have issue numbers), but has no mechanism to communicate known workarounds to consumers via the upgrade pipeline. This ADR decides how to close that gap.

## Decision Drivers

- Eliminate per-consumer rediscovery cost for known defects.
- Workarounds must be applied automatically (no consumer action required) and reverted automatically when the fix lands.
- Mechanism must not increase manual intervention; the pipeline must remain fully scriptable.
- Catalogue must be co-located with the skill so consumers receive updates on upgrade.

## Options Considered

### Option A: Versioned catalogue inside the skill tree (chosen)
Ship `workarounds/manifest.yaml` at `.agents/skills/blueprint-consumer-upgrade/workarounds/` alongside per-version action files. Pipeline Stage 1c reads the manifest, applies matching entries, writes `artifacts/blueprint/workarounds_applied.json`. Stage 2c handles post-apply patches on blueprint-managed files.

**Pros:** Co-located with the skill; propagated to consumers on upgrade automatically; machine-readable manifest enables automatic revert; auditability via `workarounds_applied.json`.

**Cons:** Adds complexity to the pipeline (new stage, new artefact, revert logic); `python_script` action kind introduces executable code in the skill tree.

### Option B: Workarounds documented in release notes only
Human-readable release notes document each known workaround. Consumers apply manually.

**Rejected:** Humans miss release notes. The pipeline knows the version; automation is strictly preferable. This option preserves the per-consumer rediscovery problem.

### Option C: Ship workarounds as full code patches in the consumer's blueprint-managed file tree (mirror-sync style)
Ship workaround patches as part of the blueprint source so the upgrade apply step (Stage 2) picks them up automatically.

**Rejected:** Blurs blueprint-managed vs consumer-customised boundaries. Hard to revert when the upstream fix lands. Couples the workaround lifecycle to the blueprint release cycle rather than to the defect lifecycle.

### Option D: Consumer's `blueprint/contract.yaml` declares its own workarounds
Each consumer declares the workarounds it has applied in its own contract.

**Rejected:** Defeats the catalogue purpose; every consumer must still discover and declare workarounds individually.

## Decision

**Option A** — versioned catalogue inside the skill tree, with pipeline Stage 1c for pre-apply workarounds and Stage 2c for post-apply workarounds (pending Q-1 resolution on `apply_phase` model).

## Manifest Schema (v1)

```yaml
schema_version: 1
versions:
  v1.10.0:
    workarounds:
      - id: "258"
        upstream_issue: https://github.com/sbonoc/stackit-platform-blueprint/issues/258
        title: "source-tree coverage gap — 4 unclassified source files"
        applies_when: always
        action_kind: contract_merge
        action_path: workarounds/v1.10.0/258_source_coverage_gap.yaml
        apply_phase: before_apply
        landed_in: null        # to be set when next release tag is cut
      - id: "260"
        upstream_issue: https://github.com/sbonoc/stackit-platform-blueprint/issues/260
        title: "template-smoke skip for generated-consumer repos"
        applies_when:
          repo_mode: generated-consumer
        action_kind: patch
        action_path: workarounds/v1.10.0/260_template_smoke_skip.patch
        apply_phase: after_apply
        landed_in: null
```

## `apply_phase` Model (decided by owner comment on PR #292, 2026-05-14)

Two-phase execution resolves the ordering conflict between consumer-owned and blueprint-managed file patches:

- `before_apply` — Stage 1c, runs before Stage 2 (apply). Use for `contract_merge` (consumer-owned `blueprint/contract.yaml`) and any workarounds that must be in place before Stage 2 reads the contract.
- `after_apply` — Stage 2c, runs after Stage 2. Use for `patch` or `python_script` on blueprint-managed files (e.g. `scripts/lib/blueprint/*.py`), which Stage 2 would overwrite if patched before apply.

## Revert Lifecycle

1. Consumer upgrades from vX.Y.0 to vX.Y.1 (where fix lands).
2. Stage 1c loads `workarounds_applied.json`; finds workaround entry with `status: applied`.
3. Engine checks `landed_in >= target_version`; calls `revert()`.
4. Logs: `Stage 1c: reverted workaround #258 (landed in vX.Y.1)`.
5. Removes entry from `workarounds_applied.json`.

## `workarounds_applied.json` Schema

```json
{
  "catalogue_version": 1,
  "target_blueprint_version": "v1.10.0",
  "applied_at": "2026-05-14T10:00:00Z",
  "entries": [
    {
      "id": "258",
      "title": "source-tree coverage gap",
      "action_kind": "contract_merge",
      "apply_phase": "before_apply",
      "status": "applied"
    }
  ]
}
```

## Security Posture

`python_script` workarounds execute code committed to the blueprint repo, which is already trusted (consumers execute make targets, shell scripts, and Python helpers from the blueprint on every upgrade). No additional trust boundary is introduced. Subprocess env is limited to a curated allowlist per NFR-SEC-001. See open question Q-3 for discussion of an optional explicit opt-in flag.

## Consequences

- Pipeline gains Stage 1c and optionally Stage 2c; total pipeline step count increases from 10 to 11 (or 12).
- `artifacts/blueprint/workarounds_applied.json` becomes a new artefact that must be committed alongside the upgrade result.
- Blueprint maintainers MUST bump `landed_in` in the manifest when a defect fix is tagged, or workarounds will never auto-revert.
- Initial catalogue ships the 4 known v1.10.0 workarounds (#258–#261) with `landed_in: null`; a follow-up commit sets these values once the next release tag is cut.

## Resolved Decisions (PR #292, 2026-05-14)

- Q-1 (apply_phase): Option A — `apply_phase` field with Stage 1c (before_apply) and Stage 2c (after_apply).
- Q-2 (failure policy): Option C — per action-kind: `contract_merge` fatal, `patch` non-fatal, `python_script` fatal.
- Q-3 (python_script trust): Option A — inherit blueprint trust; no consumer opt-in flag required.
- Q-4 (landed_in): Option A — ship v1.10.0 entries with `landed_in: null`; bump in next release PR.
