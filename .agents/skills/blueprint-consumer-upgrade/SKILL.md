---
name: blueprint-consumer-upgrade
description: Upgrade existing generated-consumer repositories from https://github.com/sbonoc/stackit-platform-blueprint using the latest stable tag (or an explicit ref) with blueprint preflight, non-destructive apply, and post-upgrade validation/postcheck. Use when asked to run blueprint-resync-consumer-seeds, blueprint-upgrade-consumer-preflight, blueprint-upgrade-consumer, blueprint-upgrade-consumer-validate, or blueprint-upgrade-consumer-postcheck while preserving consumer-owned changes.
---

# Blueprint Consumer Upgrade

## Workflow

1. Verify the repo is a generated-consumer repo and the working tree is clean.
2. Create a dedicated branch (`codex/...`) for the upgrade.
3. Resolve the latest stable tag from `https://github.com/sbonoc/stackit-platform-blueprint` unless the user pins a specific ref.
4. Run consumer-seed resync in inspect mode, then safe-apply mode.
5. Run upgrade preflight and review manual actions before apply mode.
6. Run upgrade plan mode and then apply mode with the same source/ref.
7. Resolve required manual merges if preflight/apply reports blocking actions.
8. Run post-upgrade validation and deterministic postcheck gate.
9. Report selected tag/SHA, changed files, manual actions, and exact commands.
10. Do not commit or push unless the user explicitly requests it.

## Command Sequence

Use these commands from the consumer repo root.

```bash
# 0) branch + clean working tree
git checkout -b codex/upgrade-blueprint-<tag-or-date>
git status --short

# 1) resolve latest stable tag from fixed source
./.agents/skills/blueprint-consumer-upgrade/scripts/resolve_latest_stable_ref.sh
# output: TAG=<tag> and SHA=<sha>

# 2) resync consumer-seeded files
make blueprint-resync-consumer-seeds
BLUEPRINT_RESYNC_APPLY_SAFE=true make blueprint-resync-consumer-seeds

# 3) preflight (plan-only report)
BLUEPRINT_UPGRADE_SOURCE=https://github.com/sbonoc/stackit-platform-blueprint \
BLUEPRINT_UPGRADE_REF=<tag> \
make blueprint-upgrade-consumer-preflight

# 4) plan then apply
BLUEPRINT_UPGRADE_SOURCE=https://github.com/sbonoc/stackit-platform-blueprint \
BLUEPRINT_UPGRADE_REF=<tag> \
make blueprint-upgrade-consumer

BLUEPRINT_UPGRADE_SOURCE=https://github.com/sbonoc/stackit-platform-blueprint \
BLUEPRINT_UPGRADE_REF=<tag> \
BLUEPRINT_UPGRADE_APPLY=true \
make blueprint-upgrade-consumer

# 5) validate + postcheck
make blueprint-upgrade-consumer-validate
make blueprint-upgrade-consumer-postcheck
make infra-validate
make quality-hooks-run
```

## Required Checks

- Treat non-empty `required_manual_actions` in `artifacts/blueprint/upgrade_preflight.json` as blocking.
- Treat reconcile report blocking buckets in `artifacts/blueprint/upgrade/upgrade_reconcile_report.json` as blocking.
- Treat unresolved merge markers as blocking.
- Preserve consumer-owned files; do not force overwrite unless the user explicitly asks.
- Keep source and ref pinned for the whole run (`BLUEPRINT_UPGRADE_SOURCE` + `BLUEPRINT_UPGRADE_REF`).
- Safe-to-continue contract: proceed only when `make blueprint-upgrade-consumer-postcheck` exits `0` and postcheck summary status is `success`.
- Blocked contract: stop and report exact blocked reasons when postcheck exits non-zero.

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
