# ADR-20260422: Upgrade Preflight Stale Module Target Detection and Postgres ESO Key Correction (Issues #118, #137)

## Status
Approved

## Context

Two independent contract drift hazards:

### Issue #137 — Postgres ESO key mismatch

`blueprint/modules/postgres/module.contract.yaml` lists `POSTGRES_DB` in `spec.outputs.produced`. However, the postgres ExternalSecret (`infra/gitops/platform/base/security/runtime-external-secrets-core.yaml`) emits `secretKey: POSTGRES_DB_NAME`, and `scripts/lib/infra/postgres.sh` reads `POSTGRES_DB_NAME` throughout. The module contract doc key is a typo; the runtime behaviour is consistent and correct. The mismatch causes silent divergence between governance metadata and operational reality.

### Issue #118 — Stale make target references after module disable

`render_makefile.sh:makefile_module_phony_suffix` and `makefile_module_target_block` gate each module's `.PHONY` entries and target blocks on `is_module_enabled`. When an operator disables an optional module (e.g. postgres), its module-specific targets disappear from `make/blueprint.generated.mk`. Consumer CI workflows and makefile recipes that previously referenced those targets retain stale invocations. `upgrade_consumer.py` currently detects *missing required* targets (targets the blueprint contract mandates) but does not detect *stale references* to targets that were removed because the module is disabled.

## Decision

### Issue #137 — one-line key correction

Change `POSTGRES_DB` → `POSTGRES_DB_NAME` in `blueprint/modules/postgres/module.contract.yaml` `spec.outputs.produced`. No consumer-facing change: the actual ESO secret key and all scripts already use `POSTGRES_DB_NAME` correctly. Add a contract test asserting the module output key matches the ESO manifest `secretKey`.

**Option A (selected)**: Direct one-line correction in the module contract YAML; regression test to prevent recurrence.

**Option B**: Generate the module outputs list from the ESO contract at runtime so keys are always derived from a single source. Rejected: requires significant cross-pipeline coupling for a one-line typo; the module contract `outputs.produced` field is documentation/governance metadata, not a generated artefact.

### Issue #118 — stale reference detection

Add `_collect_stale_module_target_actions` to `upgrade_consumer.py`. The helper:
1. Reads `make/blueprint.generated.mk` to determine which `infra-<module>-*` targets are currently absent (because the module is disabled).
2. Derives the expected target names for each known module from `render_makefile.sh`'s embedded lists (captured as a static mapping in the helper).
3. Scans the files already covered by `BLUEPRINT_MAKE_TARGET_REFERENCE_PATHS` (CI workflow) and `_collect_platform_make_paths` (consumer make surfaces) for literal occurrences of each absent target name.
4. Emits a `RequiredManualAction` for each stale reference, including the file path and target name in the reason string.
5. Is gated on generated-consumer repo mode; in template-source mode all module targets can be legitimately present.

**Option A (selected)**: New bounded helper in `upgrade_consumer.py`; scoped to existing reference paths; static mapping of module→target-names (mirrors `render_makefile.sh`).

**Option B**: Parse `render_makefile.sh` dynamically to extract module→target-name mappings. Rejected: shell parsing from Python is fragile; the static mapping is authoritative and change-controlled by the same repo.

## Consequences
- `blueprint/modules/postgres/module.contract.yaml` governance metadata now matches the runtime ESO secret key `POSTGRES_DB_NAME`; contract summaries and schema validators reflect correct output key names.
- `make blueprint-upgrade-consumer-preflight` surfaces stale `infra-<module>-*` references in consumer CI and make files after a module is disabled, giving operators explicit cleanup instructions before the next CI run fails silently.
- Detection is bounded to defined reference paths; false positives from unrelated files are not a concern.
- Template-source repos (including this repo) are not affected by the stale-reference detection gate.
- The `should_skip_eso_contract_check()` local-lite workaround in `reconcile_eso_runtime_secrets.sh` is orthogonal and unchanged.
