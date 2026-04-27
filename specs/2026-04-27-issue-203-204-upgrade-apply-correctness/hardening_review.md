# Hardening Review

## Repository-Wide Findings Fixed
- Finding 1: Bug #203 — prune guard only covered `base/apps/`; consumer-renamed manifests in overlay trees (e.g. `infra/gitops/platform/environments/local/`) were silently deleted during `make blueprint-upgrade-consumer BLUEPRINT_UPGRADE_ALLOW_DELETE=true`, breaking `kustomize build`. Fixed by `_is_kustomization_referenced`.
- Finding 2: Bug #204 — `git merge-file` can emit byte-identical duplicate Terraform blocks without conflict markers, producing syntactically invalid `.tf` files. Fixed by `_tf_deduplicate_blocks` post-merge scan.

## Observability and Diagnostics Changes
- Metrics/logging/tracing updates: `apply` artifact JSON gains `tf_dedup_count` and `consumer_kustomization_ref_count` counters (NFR-OPS-001); `deduplication_log` array records block type+label+path for each auto-removed duplicate (NFR-OBS-001); `ApplyResult.reason` records removed block keys inline.
- Operational diagnostics updates: malformed `kustomization.yaml` during prune guard evaluation is logged as a `warning:` to stderr (NFR-REL-001); no exception propagates.

## Architecture and Code Quality Compliance
- SOLID / Clean Architecture / Clean Code / DDD checks: Three-layer prune guard stack is now documented explicitly. Each guard is additive and self-describing (no enumerate-and-maintain path list). `_tf_deduplicate_blocks` is pure (no I/O); wiring is in `_apply_entries` only. New functions are co-located with related logic.
- Test-automation and pyramid checks: TDD red→green followed per slice. 10 new unit/integration tests added. All 83 tests green. Positive and negative paths covered for both guards (AC-001–006). Mock-based unit tests for the apply-loop TF dedup cases keep test execution fast without git repo setup.
- Documentation/diagram/CI/skill consistency checks: ADR flowchart updated in previous step; schema updated to include `merged-deduped` enum value and required summary counters; schema validates apply artifacts end-to-end.

## Proposals Only (Not Implemented)
- none
