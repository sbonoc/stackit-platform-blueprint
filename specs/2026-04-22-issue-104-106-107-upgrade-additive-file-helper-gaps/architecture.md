# Architecture

## Context
- Work item: issue-104-106-107-upgrade-additive-file-helper-gaps
- Owner: bonos
- Date: 2026-04-22

## Stack and Execution Model
- Backend stack profile: python_plus_fastapi_pydantic_v2
- Frontend stack profile: none (infra/tooling change only)
- Test automation profile: pytest_vitest_playwright_pact
- Agent execution model: single-agent

## Problem Statement
- What needs to change and why:
  Three related upgrade defects affect generated-consumer repositories:
  1. **#104 — additive-conflict mis-classification**: `upgrade_consumer.py` emits `action=conflict` when baseline content is unavailable (`baseline_content_available=false`), even when the file was simply introduced after the baseline ref and has no true 3-way merge conflict. This bloats the conflict count and forces avoidable manual work on operators.
  2. **#106/#107 — missing platform helper distribution**: `scripts/lib/platform/apps/runtime_workload_helpers.py` and `scripts/lib/platform/auth/argocd_repo_credentials_json.py` are never distributed to generated-consumer repos. Root cause: `scripts/lib/platform/` is a protected root (skipped by upgrade), and neither file is in `required_files`. Both are pure blueprint-authored JSON-parsing utilities (not consumer-editable logic) placed in the wrong namespace.
- Scope boundaries:
  - `scripts/lib/blueprint/upgrade_consumer.py` — classification logic for baseline-absent files
  - `scripts/lib/platform/apps/runtime_workload_helpers.py` → relocate to `scripts/lib/infra/`
  - `scripts/lib/platform/auth/argocd_repo_credentials_json.py` → relocate to `scripts/lib/infra/`
  - `scripts/bin/platform/apps/smoke.sh` and `scripts/bin/platform/auth/reconcile_argocd_repo_credentials.sh` — caller path updates only
  - `scripts/bin/quality/check_infra_shell_source_graph.py` — guard for future missing-helper regressions
- Out of scope:
  - Other `scripts/lib/platform/**` files not involved in these issues
  - Upgrade engine, preflight, postcheck, or resync flows beyond classification fix
  - Consumer-editable platform logic
  - Full audit of all `scripts/bin/platform/**` Python helper references (guard covers future cases)

## Bounded Contexts and Responsibilities
- **Upgrade classification context** (`scripts/lib/blueprint/upgrade_consumer.py`): owns the `_classify_entries` logic. The defect is in the baseline-absent branch: when `baseline_content is None` and both source and target files exist, the code unconditionally emits `ACTION_CONFLICT`. The fix compares source vs target content directly at this point to distinguish already-in-sync from truly-diverged additive files.
- **Helper distribution context** (namespace relocation): both helpers are pure blueprint-authored utilities with no expected consumer customization. Moving them from `scripts/lib/platform/` to `scripts/lib/infra/` brings them under the blueprint-managed directory root so the upgrade engine automatically distributes them to consumer repos.
- **Guard validation context** (`scripts/bin/quality/check_infra_shell_source_graph.py`): extend the existing shell source-graph checker to also detect `python3 "$ROOT_DIR/scripts/lib/..."` invocations in `scripts/bin/platform/**` that point to paths absent in the repository. This blocks future regressions.

## High-Level Component Design

### Classification fix (#104)
When `baseline_content is None` and both source and target files exist, replace the unconditional `ACTION_CONFLICT` with a direct source-vs-target comparison:
- `source_content == target_content` → `ACTION_SKIP` / `OPERATION_NONE` (additive file already at source version; no action needed)
- `source_content != target_content` → `ACTION_MERGE_REQUIRED` / `OPERATION_MERGE` with reason "additive file: not present at baseline ref; target diverges from source; manual merge advisory" (counted in `manual_merge`, not `conflict`)

True 3-way merge conflicts (where `baseline_content` IS available) remain unchanged.

### Helper relocation (#106/#107)
Move:
- `scripts/lib/platform/apps/runtime_workload_helpers.py` → `scripts/lib/infra/runtime_workload_helpers.py`
- `scripts/lib/platform/auth/argocd_repo_credentials_json.py` → `scripts/lib/infra/argocd_repo_credentials_json.py`

`scripts/lib/infra/` is already declared in `blueprint/contract.yaml` `script_contract.blueprint_managed_roots`, so files placed there enter the upgrade candidate set automatically. No contract.yaml change is required.

Update callers:
- `scripts/bin/platform/apps/smoke.sh`: update helper path reference
- `scripts/bin/platform/auth/reconcile_argocd_repo_credentials.sh`: update helper path reference

### Guard validation
Extend `check_infra_shell_source_graph.py` to detect `python3 "$ROOT_DIR/..."` script invocations in `scripts/bin/platform/**` shell scripts that reference paths absent from the repository root. Fail the fast quality lane when any such reference is found.

## Integration and Dependency Edges
- Upstream dependencies:
  - `scripts/lib/blueprint/upgrade_reconcile_report.py` — `ACTION_MERGE_REQUIRED` entries already flow into `consumer_owned_manual_review` bucket; no change needed
  - `blueprint/contract.yaml` `blueprint_managed_roots` — `scripts/lib/infra/` is already a managed root; no contract change required for helper relocation
- Downstream dependencies:
  - `scripts/bin/platform/apps/smoke.sh` — path update only
  - `scripts/bin/platform/auth/reconcile_argocd_repo_credentials.sh` — path update only
  - Upgrade plan/preflight JSON schemas — `ACTION_MERGE_REQUIRED` already valid; no schema change
  - `quality-infra-shell-source-graph-check` make target — invokes the guard; no target change needed
- Data/API/event contracts touched: upgrade plan/apply JSON entries: `action` field values shift from `conflict` to `skip` or `merge-required` for baseline-absent additive paths

## Non-Functional Architecture Notes
- Security: no secret or auth surface touched; helper relocation is pure path change
- Observability: upgrade metrics already emit `action` and `reason` per entry; reclassification is automatically reflected in existing metrics
- Reliability and rollback:
  - Classification fix is backward-compatible: fewer conflicts emitted, never more
  - Helper relocation: generated-consumer repos that already have the helpers at `scripts/lib/platform/` paths keep them; callers will fail with file-not-found until they upgrade and get new `scripts/lib/infra/` paths. Repos without the helpers are in the same state as before (broken until upgrade). No regression for already-working repos.
- Monitoring/alerting: no alerting surface change

## Risks and Tradeoffs
- Risk 1: Repos that manually copied helpers to `scripts/lib/platform/` will have stale copies after upgrade; callers will now reference `scripts/lib/infra/`. Mitigation: document that old `scripts/lib/platform/` copies are safe to remove after upgrade.
- Tradeoff 1: Relocating helpers to `scripts/lib/infra/` makes them blueprint-managed (not consumer-editable). This is the correct model for pure JSON-parsing/formatting utilities, and no consumer customization of these files is expected. Consumers who did customize them will lose upgrade protection for that customization — risk is low.
