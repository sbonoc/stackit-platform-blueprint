# Specification

## Spec Readiness Gate (Blocking)
- SPEC_READY: true
- Open questions count: 0
- Unresolved alternatives count: 0
- Unresolved TODO markers count: 0
- Pending assumptions count: 0
- Open clarification markers count: 0
- Product sign-off: approved
- Architecture sign-off: approved
- Security sign-off: approved
- Operations sign-off: approved
- Missing input blocker token: none
- ADR path: docs/blueprint/architecture/decisions/ADR-20260423-issue-56-app-version-contract-checks.md
- ADR status: approved

## Applicable Guardrail Controls (Normative)
- Applicable control IDs: SDD-C-005, SDD-C-006, SDD-C-009, SDD-C-010, SDD-C-011
- Control exception rationale: none

## Implementation Stack Profile (Normative)
- Backend stack profile: python_plus_fastapi_pydantic_v2
- Frontend stack profile: vue_router_pinia_onyx
- Test automation profile: pytest_vitest_playwright_pact
- Agent execution model: specialized-subagents-isolated-worktrees
- Managed service preference: stackit-managed-first
- Managed service exception rationale: none
- Runtime profile: local-first-docker-desktop-kubernetes
- Local Kubernetes context policy: docker-desktop-preferred
- Local provisioning stack: crossplane-plus-helm
- Runtime identity baseline: eso-plus-argocd-plus-keycloak
- Local-first exception rationale: none

## Objective
- Business outcome: Generated-consumer repos cannot silently pass `make apps-audit-versions` while their catalog artifacts (`versions.lock`, `manifest.yaml`) reflect stale pinned versions. After this change, the audit detects and reports any mismatch between canonical version shell vars and catalog artifact values.
- Success metric: A consumer whose `apps/catalog/versions.lock` has a stale `FASTAPI_VERSION` value triggers a non-zero exit from `make apps-audit-versions` and a log-level contract check failure; `make apps-smoke` also fails when lock and manifest are inconsistent.

## Normative Requirements

### Functional Requirements (Normative)
- FR-001 `apps-audit-versions` MUST, when `apps/catalog/versions.lock` exists, verify that each tracked shell var's value matches the value in the lock file (exact `VAR=value` match), and report the file path and expected snippet for any mismatch.
- FR-002 `apps-audit-versions` MUST, when `apps/catalog/manifest.yaml` exists, verify that each tracked shell var's expected version value is present under its canonical YAML key in the manifest, and report the file path and expected line for any mismatch.
- FR-003 `apps-audit-versions` MUST increment the aggregate `failures` counter and emit an `apps_version_contract_check_total` metric for the contract check result (skipped when no catalog files exist).
- FR-004 `apps-audit-versions-cached` MUST include `apps/catalog/versions.lock` and `apps/catalog/manifest.yaml` in its cache fingerprint when those files exist, so that a change to any catalog file invalidates the cache.
- FR-005 `apps-smoke` MUST, when `APP_CATALOG_SCAFFOLD_ENABLED=true`, verify that the values in `apps/catalog/versions.lock` and `apps/catalog/manifest.yaml` are mutually consistent (consistency check) after the existing structural validate step.
- FR-006 The version contract checker MUST run without PyYAML — manifest checks use regex line-matching against the known manifest structure.
- FR-007 All contract check failures MUST report: the file path, the expected snippet, and what was actually found (or "not found" if the key is absent).

### Non-Functional Requirements (Normative)
- NFR-SEC-001 The checker reads only local files via `pathlib`; no network access, no subprocess calls, no shell injection vectors.
- NFR-OBS-001 `apps_version_contract_check_total` metric emitted per contract check invocation with status label; contract check counts added to `apps_version_audit_summary_total`.
- NFR-REL-001 When catalog files do not exist (generated consumer with `APP_CATALOG_SCAFFOLD_ENABLED=false`), all contract checks are skipped without error; audit proceeds normally.
- NFR-OPS-001 Human-readable report printed to stdout listing each check result (pass/fail, file, expected snippet, actual value); non-zero exit when any check fails.

## Normative Option Decision
- Option A: New Python script `version_contract_checker.py` with two modes (`catalog-check`, `consistency`), invoked from shell scripts via `run_cmd python3`.
- Option B: Inline bash checks using `grep`/`awk` in `audit_versions.sh`.
- Selected option: Option A
- Rationale: Python provides deterministic regex matching, testable pure functions, and structured output without fragile shell string handling. Follows the established Python-core + shell-invocation pattern (`catalog_scaffold_renderer.py`, `uplift_status.py`).

## Contract Changes (Normative)
- Config/Env contract: no new env vars; existing `APP_CATALOG_SCAFFOLD_ENABLED` gates catalog checks in smoke.
- API contract: none.
- Event contract: none.
- Make/CLI contract: no new targets; `apps-audit-versions`, `apps-smoke` behavior extended (non-breaking when catalog files absent).
- Docs contract: none (no consumer-facing doc changes).

## Blueprint Upstream Defect Escalation (Normative)
- Upstream issue URL: https://github.com/sbonoc/stackit-platform-blueprint/issues/56
- Temporary workaround path: none
- Replacement trigger: none
- Workaround review date: none

## Normative Acceptance Criteria
- AC-001 `check_versions_lock` returns a failing result when `versions.lock` contains a different value than expected for a tracked var.
- AC-002 `check_manifest_yaml` returns a failing result when the manifest YAML does not contain the expected `yaml_key: value` line for a tracked var.
- AC-003 `check_catalog_consistency` returns a failing result when a lock var value does not match the corresponding manifest YAML value.
- AC-004 When `apps/catalog/versions.lock` has a stale `FASTAPI_VERSION`, `make apps-audit-versions` exits non-zero (tested via Python unit tests with temp files, not live make invocation).
- AC-005 When neither catalog file exists, `audit_versions.sh` skips contract checks and `apps_version_contract_check_total` is not emitted (contract_checks_run=0).
- AC-006 `audit_versions_cached.sh` fingerprint includes catalog files when they exist and excludes them when absent.
- AC-007 `apps-smoke` (catalog enabled) exits non-zero when `versions.lock` and `manifest.yaml` are inconsistent (tested via Python unit tests).

## Informative Notes (Non-Normative)
- Context: This closes the contract gap described in GitHub issue #56 comment from 2026-04-02, where a `PyJWT==2.10.1` addition passed `apps-audit-versions` until the consumer manually updated all 6 contract surfaces.
- Tradeoffs: Text-based manifest matching (not PyYAML parse) is chosen for zero additional runtime dependencies and determinism given the fixed known manifest schema.
- Clarifications: none

## Explicit Exclusions
- Source file checks (`apps/backend/pyproject.toml`, `apps/touchpoints/package.json`) are excluded: those files are consumer-provided and not scaffolded by the blueprint; file-level source checks belong in consumer-owned CI, not the blueprint contract.
- New canonical version variables (e.g., `UVICORN_VERSION`, `HTTPX_VERSION`) are excluded: adding new vars requires corresponding scaffold template changes and a separate SDD work item.
