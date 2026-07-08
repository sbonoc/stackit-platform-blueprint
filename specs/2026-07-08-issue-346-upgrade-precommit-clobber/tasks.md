# Tasks

## Gate Checks (Required Before Implementation)
- [ ] G-001 Confirm `SPEC_READY=true` in `spec.md`
- [ ] G-002 Confirm open questions and unresolved alternatives are `0`
- [ ] G-003 Confirm required sign-offs are approved
- [ ] G-004 Confirm `Applicable Guardrail Controls` section includes `SDD-C-###` IDs
- [ ] G-005 Confirm `Implementation Stack Profile` section is fully populated

## Implementation
- [ ] T-001 Add `PrecommitYamlParseError` exception class in `upgrade_consumer.py`
- [ ] T-002 Add `_yaml_merge_precommit_hooks(source_content, target_content) -> str` function in `upgrade_consumer.py`
- [ ] T-003 Modify `_apply_entries` in `upgrade_consumer.py` to intercept `.pre-commit-config.yaml` + `ACTION_MERGE_REQUIRED` with the YAML-aware merge path and fallback to `_three_way_merge` on `PrecommitYamlParseError`
- [ ] T-004 Modify `_write_summary` to include "Preserved Consumer Hooks" section with merged hook IDs

## Test Automation
- [ ] T-101 [AC-001] test that consumer-only hook survives merge — `tests/blueprint/test_upgrade_precommit_merge.py::test_consumer_hook_survives_merge`
- [ ] T-102 [AC-002] test that consumer hook is appended AFTER last blueprint hook — `tests/blueprint/test_upgrade_precommit_merge.py::test_consumer_hook_appended_after_blueprint_hooks`
- [ ] T-103 [AC-003] test that multiple consumer hooks are all preserved in order — `tests/blueprint/test_upgrade_precommit_merge.py::test_multiple_consumer_hooks_preserved_in_order`
- [ ] T-104 [AC-004] test that malformed YAML raises `PrecommitYamlParseError` — `tests/blueprint/test_upgrade_precommit_merge.py::test_malformed_yaml_raises_parse_error`
- [ ] T-105 [AC-005] test merge idempotency — `tests/blueprint/test_upgrade_precommit_merge.py::test_merge_is_idempotent`
- [ ] T-106 [AC-006] test `_classify_entries` produces `merge-required` for consumer-diverged `.pre-commit-config.yaml` — `tests/blueprint/test_upgrade_precommit_merge.py::test_classify_entries_merge_required_for_consumer_hooks`
- [ ] T-107 [AC-007] test no hook duplication on second upgrade — `tests/blueprint/test_upgrade_precommit_merge.py::test_no_hook_duplication_on_second_upgrade`
- [ ] T-108 [AC-008] test upgrade_summary lists preserved hook IDs — `tests/blueprint/test_upgrade_precommit_merge.py::test_summary_lists_preserved_hook_ids`
- [ ] T-109 Create test fixtures: `tests/blueprint/fixtures/upgrade_precommit/source_baseline.yaml`, `target_consumer_added.yaml`, `target_consumer_added_multi.yaml`, `target_malformed.yaml`

## Accessibility Testing
- [ ] T-A01 N/A — no user-facing UI (`has-user-facing-flow: false`; `NFR-A11Y-001: N/A — no user-facing UI`)

## Validation and Release Readiness
- [ ] T-201 Run `uv run python3 -m pytest tests/blueprint/ -q` — all pass
- [ ] T-202 Run `make quality-sdd-check` — all pass
- [ ] T-203 Confirm no stale TODOs/dead code/drift
- [ ] T-204 Run `make docs-build` and `make docs-smoke`
- [ ] T-205 Run `make quality-hardening-review` (if applicable)

## Publish
- [ ] P-001 Update `hardening_review.md`
- [ ] P-002 Update `pr_context.md` with test evidence and rollback notes
- [ ] P-003 Ensure PR description references `pr_context.md`

## App Onboarding Minimum Targets (Normative)
- [ ] A-001 N/A — this work item does not add or modify any app onboarding make targets
