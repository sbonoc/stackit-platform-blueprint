# ADR: Issues #263 + #264 + #266 — Pipeline/Engine Correctness: Baseline Version Tracking, Exit Code Disambiguation, and Apply Default

- **Status**: approved
- **Date**: 2026-05-12
- **Issues**: #263, #264, #266
- **Work item**: `specs/2026-05-12-issue-263-264-266-pipeline-engine-correctness/`
- **ADR technical decision sign-off**: approved

## Context

Three independent correctness bugs in the scripted upgrade pipeline were confirmed during a real consumer upgrade (sbonoc/dhe-marketplace v1.7.0 → v1.10.0, PR #62). The upgrade produced 88 conflicts, required manual stage invocation, and wasted approximately 5 additional minutes on a silent plan-only run.

**Issue #263 — Wrong baseline ref for 3-way merge:**
`_resolve_baseline_ref` in `upgrade_consumer.py` reads `template_version` from `blueprint/contract.yaml`. That field is set at repo init and never advanced. A consumer initialized from v1.0.0 who has successfully applied upgrades through v1.8.3 still resolves v1.0.0 as the baseline for every subsequent upgrade. The 3-way merge has no anchor for files added between v1.0.0 and v1.8.3, producing "baseline content unavailable" conflicts. The fix is to track `last_applied_version` separately and advance it after each successful postcheck.

**Issue #264 — Pipeline always aborts when Stage 2 has conflicts:**
The engine exits 1 when conflicts are present (expected behavior). GNU make wraps any recipe `exit 1` as make's own `exit 2`. The pipeline checks `if [[ "$stage2_rc" -gt 1 ]]`, which fires for every conflict scenario (2 > 1 is always true), aborting Stages 3–10. The downstream stages — contract resolver, conflict auto-resolution, coverage fetch, mirror sync, docs regen, gate chain — never run. The fix is to have the engine exit 0 for conflicts (using the artifact to carry the result) and have the pipeline read the artifact status.

**Issue #266 — Pipeline defaults to plan-only:**
`upgrade_consumer.sh` defaults `BLUEPRINT_UPGRADE_APPLY=false`. `upgrade_consumer_pipeline.sh` invokes `make blueprint-upgrade-consumer-apply` without overriding this default, so every pipeline run is silently plan-only unless the user exports `BLUEPRINT_UPGRADE_APPLY=true` explicitly. The pipeline is named `blueprint-upgrade-consumer` (not `blueprint-upgrade-consumer-plan`); the distinction is meaningless when both default to plan-only.

## Decision

### #263 — Track `last_applied_version` as a separate contract field

Add an optional `last_applied_version` field to `TemplateBootstrapContract` (defaulting to empty string). Update `_resolve_baseline_ref` to prefer `last_applied_version` candidates over `template_version` candidates. After a successful `make blueprint-upgrade-consumer-postcheck`, write `last_applied_version` to `blueprint/contract.yaml` with the `upgrade_ref` from `upgrade_apply.json`. Existing consumers without the field fall back to `template_version` until their next successful postcheck. `upgrade_version_pin_diff.py` receives the same update.

### #264 — Engine exits 0 for conflicts; pipeline reads artifact status (Option A)

Change `upgrade_consumer.py`: when `args.apply and conflict_count > 0`, set `apply_payload["status"] = "conflicts"` and `return 0`. Non-zero exit is reserved for true engine errors (merge markers, clone failure, write errors, contract load failure). Add `"conflicts"` to the `upgrade_apply.schema.json` status enum. Update the pipeline Stage 2 logic to read `upgrade_apply.json` status and abort only when `stage2_rc != 0 AND status != "conflicts"`.

### #266 — Pipeline defaults `BLUEPRINT_UPGRADE_APPLY=true`

Add `set_default_env BLUEPRINT_UPGRADE_APPLY true` to `upgrade_consumer_pipeline.sh` before Stage 2. Propagate `BLUEPRINT_UPGRADE_APPLY` explicitly in the Stage 2 make invocation env prefix. Emit a `[PIPELINE]` banner before Stage 2 when `BLUEPRINT_UPGRADE_APPLY=false` is explicitly set. Update the usage block. The standalone `upgrade_consumer.sh` retains `BLUEPRINT_UPGRADE_APPLY=false` for backward compatibility with direct callers.

## Alternatives Considered

### #263 — Alternatives
- **Derive from git history**: find the latest blueprint upgrade commit tag from `git log`. Rejected: fragile across squash-merges and rebases; requires canonical commit message format.
- **Bump `template_version` on every upgrade**: rejected; field is documented as immutable (original generation version) and referenced by init guards.

### #264 — Option B: pipeline reads artifact, engine keeps exit 1
Keep engine exit 1 for conflicts; pipeline inspects `upgrade_apply.json` first and ignores make exit code when status equals "conflicts". Rejected in favour of Option A: both options require adding "conflicts" to the schema. Option A produces correct Unix semantics (0 = completed successfully, even if with work remaining; non-zero = error). Option B keeps a misleading exit code that conflicts with standard tooling expectations.

### #266 — Rename pipeline target
Rename `blueprint-upgrade-consumer` to `blueprint-upgrade-consumer-apply` and add a new `-plan` wrapper. Rejected: high blast radius (breaks existing callers and consumer habits); the productivity issue is addressed adequately by changing the default with a banner.

## Consequences

- `make blueprint-upgrade-consumer` now applies by default. Callers relying on the plan-only default MUST set `BLUEPRINT_UPGRADE_APPLY=false` explicitly or switch to `make blueprint-upgrade-consumer-preflight`.
- `make blueprint-upgrade-consumer-apply` exit code changes from 1 (conflicts) to 0 (conflicts). Callers checking the exit code directly MUST migrate to reading `upgrade_apply.json#status`.
- `blueprint/contract.yaml` gains a new optional field `last_applied_version`; consumers do not need to add it manually — postcheck writes it on first success.
- The `upgrade_apply.json` schema gains a third `status` enum value `"conflicts"`.
