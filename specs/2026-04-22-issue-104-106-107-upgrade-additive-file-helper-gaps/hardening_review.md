# Hardening Review

## Repository-Wide Findings Fixed
- Finding 1: `_classify_entries` emitted `action=conflict` for baseline-absent (additive) files where no common ancestor exists, causing false-positive conflict counts in upgrade preflight. Fixed by restructuring the content-comparison block to call `resolve_baseline_content` before the source==target check, then emitting `action=skip` or `action=merge-required` based on content equality and baseline availability.
- Finding 2: `scripts/lib/platform/apps/runtime_workload_helpers.py` and `scripts/lib/platform/auth/argocd_repo_credentials_json.py` placed in `scripts/lib/platform/` (a protected root, never distributed by the upgrade engine). Fixed by relocating both files to `scripts/lib/infra/` (a blueprint-managed root, automatically distributed) and updating the two caller shell scripts.
- Finding 3: No guard existed to catch missing `python3 "$ROOT_DIR/scripts/lib/..."` references in `scripts/bin/platform/**`. Fixed by extending `check_infra_shell_source_graph.py` with `_validate_platform_python_refs`.

## Observability and Diagnostics Changes
- Metrics/logging/tracing updates: upgrade plan/apply entries for reclassified paths now emit `action=skip` or `action=merge-required` instead of `action=conflict`; `baseline_content_available=false` and `reason` fields are present in both cases. Upgrade metrics (`conflict_count`, `manual_merge_count`) automatically reflect the reclassification.
- Operational diagnostics updates: `_validate_platform_python_refs` emits a deterministic human-readable error identifying both the offending script path and the missing helper path when the guard fires (NFR-OPS-001).

## Architecture and Code Quality Compliance
- SOLID / Clean Architecture / Clean Code / DDD checks:
  - Single-responsibility: `_validate_platform_python_refs` is a focused, standalone function; no logic merged into existing `_validate_required_edges`.
  - Open/closed: guard extensibility is implicit in the regex scan — new platform scripts are covered automatically.
  - Clean Code: restructured classification block uses explicit if/else branches with one responsibility per branch; no nested ternary or ambiguous fall-through.
- Test-automation and pyramid checks:
  - Three new unit tests in `tests/blueprint/test_upgrade_consumer.py` (`AdditiveFileClassificationTests`): positive-path skip, merge-required classification, baseline-present regression guard. All exercise the classification function end-to-end via the CLI script.
  - Three new integration tests in `tests/infra/test_tooling_contracts.py` (`PlatformPythonHelperGuardTests`): smoke.sh helper ref existence, reconcile_argocd_repo_credentials.sh helper ref existence, guard script end-to-end pass.
  - No test added for the old platform helper paths: they are deleted and have no regression surface.
- Documentation/diagram/CI/skill consistency checks:
  - `AGENTS.decisions.md` updated with classification fix and helper relocation rationale.
  - `AGENTS.backlog.md` items #104/#106/#107 marked done.
  - ADR already written and approved at `docs/blueprint/architecture/decisions/ADR-20260422-issue-104-106-107-upgrade-additive-file-helper-gaps.md`.

## Proposals Only (Not Implemented)
- Proposal 1: audit all `scripts/bin/platform/**` Python helper references for correctness beyond the two identified in #106/#107. Not implemented; the new guard makes this a continuous automated check rather than a one-time audit.
