---
name: blueprint-consumer-upgrade
description: Upgrade existing generated-consumer repositories using the deterministic scripted pipeline (make blueprint-upgrade-consumer). Use when asked to upgrade, resync, or apply a new blueprint version to a consumer repository. The pipeline handles all 10 stages automatically and produces a residual report covering only items requiring human decision.
---

# Blueprint Consumer Upgrade

The upgrade is fully scripted. The agent's role is: set the ref, run the pipeline, read the report, apply prescribed actions, and commit.

## Workflow (6 steps)

1. **Set ref.** Resolve the target tag or accept it from the user input. Create a dedicated branch.
2. **Run pipeline.** Execute the scripted upgrade pipeline end-to-end.
3. **Read residual report.** Open `artifacts/blueprint/upgrade-residual.md`.
4. **Apply prescribed actions.** For each item in the report, apply the action listed (Remove/Add/Classify/Review). Do not skip items — every item has a prescribed action.
5. **Confirm clean.** Re-run `make quality-hooks-run` to confirm no remaining issues.
6. **Commit and open PR.** Use the standard PR packager skill (`/blueprint-sdd-step07-pr-packager`).

## Command Sequence

```bash
# Step 1 — branch + resolve ref
git checkout -b codex/upgrade-blueprint-<tag>
./.agents/skills/blueprint-consumer-upgrade/scripts/resolve_latest_stable_ref.sh
# output: TAG=<tag>

# Step 2 — run the scripted pipeline
BLUEPRINT_UPGRADE_SOURCE=https://github.com/sbonoc/stackit-platform-blueprint \
BLUEPRINT_UPGRADE_REF=<tag> \
make blueprint-upgrade-consumer

# Step 3 — read the residual report
cat artifacts/blueprint/upgrade-residual.md

# Step 5 — confirm clean after applying prescribed actions
make quality-hooks-run
```

## What the Pipeline Does

The `make blueprint-upgrade-consumer` target runs 10 scripted stages automatically:

| Stage | What happens |
|-------|-------------|
| 1 | Pre-flight: clean working tree, valid ref, parseable contract |
| 2 | Apply with delete (`BLUEPRINT_UPGRADE_ALLOW_DELETE=true` by default) |
| 3 | Contract resolver: preserve identity, merge required_files, drop matching prune globs |
| 4 | Auto-resolve non-contract conflicts (blueprint-managed files take source content) |
| 5 | Coverage gap detection and file fetch from local git clone |
| 6 | Bootstrap template mirror sync |
| 7 | Make target validation for new/changed docs (warnings only) |
| 8 | Generated reference docs regeneration |
| 9 | Gate chain: `make infra-validate` then `make quality-hooks-run` |
| 10 | Residual report (always emitted, even on partial failure) |

## Override: Non-Destructive Mode

To disable the default delete behavior (Stage 2):

```bash
BLUEPRINT_UPGRADE_SOURCE=https://github.com/sbonoc/stackit-platform-blueprint \
BLUEPRINT_UPGRADE_REF=<tag> \
BLUEPRINT_UPGRADE_ALLOW_DELETE=false \
make blueprint-upgrade-consumer
```

## Individual Stages (Standalone)

Existing individual make targets remain independently callable:

```bash
make blueprint-upgrade-consumer-apply     # Stage 2 only (plan/apply engine)
make blueprint-upgrade-consumer-preflight # Plan-only preflight report
make blueprint-upgrade-consumer-validate  # Post-upgrade validation
make blueprint-upgrade-consumer-postcheck # Deterministic convergence gate
make blueprint-upgrade-fresh-env-gate     # Fresh-environment smoke gate
```

## Optional Module Handling

### How Modules Work in Consumer Repos

Blueprint optional modules have two separate concerns that are easy to confuse:

| Artifact | Location | Source-only? | Purpose |
|----------|----------|--------------|---------|
| Module authoring metadata | `blueprint/modules/{module}/module.contract.yaml` | YES — removed by `blueprint-init-repo` | Blueprint authoring only; consumers never see this |
| Scaffold templates | `scripts/templates/infra/bootstrap/{module}/` | **NO** — present in all consumer repos | Used by `make infra-bootstrap` to create enabled scaffold |
| Runtime contract | `blueprint/contract.yaml` | **NO** — present in all consumer repos | `optional_modules` section drives `is_module_enabled` decisions |

**Key insight:** `blueprint/modules/` being removed from consumer repos does NOT block consumers from enabling modules. Consumers enable a module by setting the module's `enable_flag` environment variable (or via `blueprint/contract.yaml` `enabled_by_default`). At runtime, `make infra-bootstrap` reads `is_module_enabled` against the contract and creates scaffold from `scripts/templates/infra/bootstrap/` using create-if-missing semantics.

### Scaffold Presence Contract

| Path pattern | When module disabled | When module enabled |
|---|---|---|
| `infra/cloud/stackit/terraform/modules/{module}/` | ABSENT | PRESENT (created by `make infra-bootstrap`) |
| `infra/local/helm/{module}/` | ABSENT | PRESENT (created by `make infra-bootstrap`) |
| `tests/infra/modules/{module}/` | ABSENT | PRESENT (created by `make infra-bootstrap`) |
| `infra/gitops/argocd/optional/${ENV}/{module}.yaml` | ABSENT | PRESENT (created by `make infra-bootstrap`) |
| `docs/platform/modules/{module}/README.md` | PRESENT | PRESENT (always seeded — product catalog) |

`blueprint-init-repo` enforces the ABSENT state on first init by pruning all `paths_required_when_enabled` paths for disabled modules. `make infra-bootstrap` enforces the PRESENT state for enabled modules. `make infra-validate` catches template drift (enabled scaffold that diverges from the template source).

### After Upgrade Apply (Step 4a — Always Run)

```bash
make infra-bootstrap
```

Run unconditionally after every upgrade apply. This is safe — `make infra-bootstrap` uses create-if-missing semantics for existing files, so it will not overwrite consumer-customised scaffold. It serves two purposes:

1. **Newly enabled modules:** Creates scaffold for any module the consumer has since enabled.
2. **Drift resolution reseeds:** When template drift is found (see below), the resolution is to delete the stale file and re-run `make infra-bootstrap` to reseed from the updated template.

### Disabled Module Cleanup (Step 4b — Only When Modules Were Disabled)

```bash
# make infra-destroy-disabled-modules
```

This step is intentionally commented out in the command sequence. Run it only when modules have been explicitly disabled since the last upgrade. It removes scaffold for disabled modules. Do not run speculatively — it is destructive.

### Template Drift Resolution

`make infra-validate` (step 6) reports template drift: enabled module scaffold files whose content has diverged from the blueprint template. When drift is found for an enabled module:

1. Delete the stale scaffold file(s) reported by `make infra-validate`.
2. Re-run `make infra-bootstrap` to reseed from the updated template.
3. Re-run `make infra-validate` to confirm the drift is cleared.

Do not manually edit scaffold files to match the template — reseed via `make infra-bootstrap` instead, so create-if-missing semantics apply and no consumer customisation is lost unexpectedly.

### Keycloak Is Mandatory

Keycloak is not an optional module. It is always rendered in `infra/gitops/argocd/core/` and is never governed by `is_module_enabled`. Do not apply optional module logic to Keycloak paths.

## Required Checks

- Treat non-empty `required_manual_actions` in `artifacts/blueprint/upgrade_preflight.json` as blocking.
- Treat reconcile report blocking buckets in `artifacts/blueprint/upgrade/upgrade_reconcile_report.json` as blocking. `conflicts_unresolved` reflects files that still contain active `<<<<<<<` markers in the working tree; once markers are cleared the count drops automatically — auto-merged and manually-resolved files are not counted.
- Treat unresolved merge markers as blocking — clear all `<<<<<<<` / `=======` / `>>>>>>>` markers in affected files before re-running the postcheck.
- Treat behavioral check failures as blocking — `make blueprint-upgrade-consumer-postcheck` validates
  shell function interfaces and command signatures that may have changed during the upgrade; a non-zero
  exit signals a behavioral regression and the upgrade MUST NOT be declared complete until it is resolved.
  The symbol resolver suppresses case-label alternation tokens (`token|)`) and bare-word elements inside
  `local`/`declare`/`readonly`/`typeset` array blocks (`var=(`) to prevent false positives.
- Preserve consumer-owned files; do not force overwrite unless the user explicitly asks.
- Keep source and ref pinned for the whole run (`BLUEPRINT_UPGRADE_SOURCE` + `BLUEPRINT_UPGRADE_REF`).
- Safe-to-continue contract: proceed only when `make blueprint-upgrade-consumer-postcheck` exits `0` AND `make blueprint-upgrade-fresh-env-gate` exits `0`. Both must pass before the upgrade is declared complete.
- Blocked contract: stop and report exact blocked reasons when postcheck or fresh-env-gate exits non-zero. `fresh_env_gate.json` includes a `divergences` array; each entry with `path`/`worktree_checksum`/`working_tree_checksum` keys identifies an artifact whose content differs between the clean worktree and the local working tree — inspect those paths to find the root cause.

## Governance Context

`AGENTS.md` is the canonical policy source for behavioral and code changes triggered during upgrade execution. Sections that apply:

- `§ Blueprint Contract Precedence` — `blueprint/contract.yaml` governs ownership boundaries; consumer-owned platform surfaces must be preserved through the upgrade.
- `§ Mandatory Workflow` — any behavioral or code change required by upgrade findings MUST follow SDD order before implementation begins.
- `§ SDD Readiness Gate (Mandatory Before Implementation)` — upgrade-triggered work items must reach `SPEC_READY: true` before implementation code is written.
- `§ Dependency and Versioning Mandates` — version pins introduced or changed by the upgrade must meet the strict latest-stable policy.
- `§ Minimum Validation Bundles by Change Type` — blueprint upgrades are classified as infrastructure changes; the full validation bundle (postcheck + fresh-env-gate) must pass before declaring the upgrade complete.

> If `AGENTS.md` changes any of the above sections, update this block to reflect the affected sections.

## SDD Guardrails

- Treat consumer `AGENTS.md` as the governance source for lifecycle and contracts.
- If upgrade findings require behavioral/code changes, execute SDD order exactly:
  `Discover -> High-Level Architecture -> Specify -> Plan -> Implement -> Verify -> Document -> Operate`.
- During `Discover`, `High-Level Architecture`, `Specify`, and `Plan`, do not fill gaps with assumptions.
- Keep `SPEC_READY=false` until missing inputs are resolved explicitly; if unresolved, mark the work item `BLOCKED_MISSING_INPUTS`.
- Require applicable `SDD-C-###` control IDs in `spec.md` for each non-trivial change triggered by upgrade work.

## Reporting Format

Always return:

1. Selected blueprint ref: tag + commit SHA.
2. Auto-applied updates.
3. Manual merges and rationale.
4. Remaining required actions (if any).
5. Validation commands run and outcome.
6. Suggested next step.

## References

- Manual merge checklist: `references/manual_merge_checklist.md`
