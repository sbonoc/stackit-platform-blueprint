# PR Context

## Summary

`make blueprint-upgrade-consumer` was silently dropping consumer-added pre-commit hooks on every upgrade because `.pre-commit-config.yaml` is classified as `required-file` (blueprint-owned) and the upgrade engine's 3-way `git merge-file` merge is structurally unaware of YAML hook semantics. When the blueprint source also changed the file for a new release, triage recommended `take_source`, discarding consumer additions with no warning. This PR adds a YAML-aware hook-preserving merge in `upgrade_consumer.py`: it parses both source and target with `yaml.safe_load`, identifies hook IDs present in the consumer but absent from the blueprint, and appends them verbatim after the last blueprint hook in the merged output. A parse-failure fallback routes to the existing `git merge-file` path with a WARNING log. The `upgrade_summary.md` artifact gains a "Preserved Consumer Hooks" section listing every preserved hook ID for operator audit. Blueprint ownership of `.pre-commit-config.yaml` is preserved (safety hooks still propagate on upgrade); consumer additions now survive automatically.

## Requirement Coverage

| Requirement | Implementation | Test |
|---|---|---|
| FR-001 — YAML-aware merge intercept | `upgrade_consumer.py`: `_PRECOMMIT_CONFIG_PATH` intercept in `_apply_entries` | T-106 (`test_t106_classify_returns_merge_required_for_consumer_diverged`) |
| FR-002 — consumer-only hook identification + append | `upgrade_consumer.py`: `_yaml_merge_precommit_hooks()` hook-id diff + append | T-101 (`test_t101_consumer_only_hook_survives`) |
| FR-003 — original hook order preserved | `_yaml_merge_precommit_hooks()`: consumer-only hooks appended in target list order | T-103 (`test_t103_multiple_consumer_hooks_all_preserved_in_order`) |
| FR-004 — YAML parse failure fallback | `PrecommitYamlParseError` sentinel; caught in `_apply_entries` → `_three_way_merge` + stderr WARNING | T-104 (`test_t104_yaml_parse_failure_raises_sentinel`, `test_t104_malformed_source_raises_sentinel`) |
| FR-005 — preflight action unchanged | `_classify_entries` already returns `merge-required`; no change | T-106 |
| FR-006 — summary lists preserved hook IDs | `preserved_precommit_hooks` list returned from `_apply_entries`, passed to `_write_summary` | T-108 (`test_t108_write_summary_lists_preserved_hooks`) |
| FR-007 — bootstrap template drift gate unaffected | No changes to `scripts/templates/blueprint/bootstrap/.pre-commit-config.yaml` | Pre-commit `quality-validate-bootstrap-template-drift` |
| FR-008 — positive-path test with fixture | `tests/blueprint/test_upgrade_precommit_merge.py` + `tests/blueprint/fixtures/upgrade_precommit/` | T-101 through T-108 |
| NFR-SEC-001 — `yaml.safe_load` only | `_yaml_merge_precommit_hooks()` uses `yaml.safe_load` exclusively | T-104 (parse path) |
| NFR-OBS-001 — structured log per preserved hook | `print(f"[precommit-merge] preserved consumer hooks: ...", file=sys.stderr)` | T-108 (summary contains hook ID) |
| NFR-REL-001 — idempotency | `existing_ids` set in `_yaml_merge_precommit_hooks` prevents duplicate insertion | T-105, T-107 |
| NFR-OPS-001 — summary section | `_write_summary` "Preserved Consumer Hooks" section; "no consumer-only hooks detected" when empty | T-108 |
| AC-001 — consumer hook survives | `_yaml_merge_precommit_hooks` returns merged string containing consumer hook ID | T-101 |
| AC-002 — appended after last blueprint hook | `consumer_pos > last_blueprint_pos` assertion | T-102 |
| AC-003 — multiple hooks in order | pos1 < pos2 ordering assertion | T-103 |
| AC-004 — parse failure raises sentinel | `assertRaises(PrecommitYamlParseError)` | T-104 |
| AC-005 — idempotency | second_pass == first_pass | T-105 |
| AC-006 — classify returns merge-required | `entries[0].action == ACTION_MERGE_REQUIRED` | T-106 |
| AC-007 — no duplication on second upgrade | `count == 1` assertion | T-107 |
| AC-008 — summary lists hook IDs | summary_text contains hook ID and "Preserved Consumer Hooks" | T-108 |

## Key Reviewer Files

- `scripts/lib/blueprint/upgrade_consumer.py` — core change: `PrecommitYamlParseError`, `_yaml_merge_precommit_hooks()`, intercept in `_apply_entries`, updated `_write_summary` signature + body. All logic is additive; the `.pre-commit-config.yaml` intercept is gated by `entry.path == _PRECOMMIT_CONFIG_PATH` so no other file paths are affected.
- `tests/blueprint/test_upgrade_precommit_merge.py` — 9 tests (T-101 through T-108, T-104 tested twice for source and target malformed). All pass; T-106 uses real git repos via tempdir helpers.
- `tests/blueprint/fixtures/upgrade_precommit/` — 4 YAML fixtures representing baseline, single consumer hook, multi consumer hook, and structurally-invalid target.
- `docs/platform/consumer/consumer_quality_gates.md` — "No pre-commit file edits required" note updated to reflect upgrade-safe hook additions as of v1.12.3.
- `docs/platform/architecture/decisions/ADR-issue-346-upgrade-precommit-clobber.md` — decision record with flowchart; status: approved.
- `tests/blueprint/test_upgrade_consumer.py` — two existing callers of `_apply_entries` updated from 3-tuple to 4-tuple unpack (no logic change).

## Validation Evidence

```
# Full blueprint test suite — all pass
uv run python3 -m pytest tests/blueprint/ -q
→ 1490 passed, 42 subtests passed in 156s

# New precommit merge tests — all pass
uv run python3 -m pytest tests/blueprint/test_upgrade_precommit_merge.py -q
→ 9 passed in 0.31s

# SDD governance gate
make quality-sdd-check
→ [quality-sdd-check] validated SDD assets, readiness gates, and language policy (exit 0)

# Docs check
make quality-docs-check-changed
→ [test-pyramid] OK — exit 0

# Bootstrap template docs sync
uv run python3 scripts/lib/docs/sync_blueprint_template_docs.py
→ summary: quality-docs-sync-blueprint-template (created=0 updated=0 removed=0 skipped=17)
```

## Risk and Rollback

**Blast radius:** Scoped to the `_apply_entries` path for `.pre-commit-config.yaml` only. All other file types follow the existing code paths unchanged. The `_PRECOMMIT_CONFIG_PATH == ".pre-commit-config.yaml"` gate is a string equality check — no glob or pattern matching.

**Regression risk:** Low. The fallback to `_three_way_merge` on `PrecommitYamlParseError` ensures that any consumer with a malformed `.pre-commit-config.yaml` gets the same behavior as before this PR.

**YAML round-trip:** `yaml.safe_load` + `yaml.dump` normalises whitespace and drops inline comments within hook blocks. This is accepted (documented in ADR consequences). Hook semantics are fully expressed as key:value fields; no comment-dependent behavior.

**Rollback:** Revert `upgrade_consumer.py` changes (remove `_PRECOMMIT_CONFIG_PATH`, `PrecommitYamlParseError`, `_yaml_merge_precommit_hooks`, and the intercept in `_apply_entries`; revert `_write_summary` signature; restore 3-tuple returns). No contract schema or required-file classification changes were made — rollback is a pure code revert.

**Feature flag:** None. The YAML-aware merge activates automatically for `.pre-commit-config.yaml` on the `ACTION_MERGE_REQUIRED` path. Consumers that have not added any hooks see identical behavior (zero consumer-only hooks → `source_content` returned verbatim).

## Deferred Proposals

1. **Allowlist-based upgrade conflict triage override** — allow `blueprint/contract.yaml` to declare per-path triage preferences (e.g. `"required-file-merge-preferred": true`) to generalise this fix to other required files with consumer-local amendments. Parked — trigger: `on-scope: blueprint` — requires contract schema change; out of scope for targeted bug fix.

2. **Incremental tag-to-tag upgrade mode (Issue #168)** — consumer hooks added in intermediate releases could be tracked per-release. Parked — trigger: `after: issue-168` — blocked on the incremental upgrade track.

3. **Consumer migration guide** — emit a warning when a consumer hook that was previously explicit is now part of the blueprint baseline, to guide cleanup after a blueprint release absorbs it. Parked — trigger: `on-scope: blueprint` — useful UX improvement; revisit when touching upgrade operator experience.
