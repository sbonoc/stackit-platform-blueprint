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
- ADR path: docs/blueprint/architecture/decisions/ADR-20260422-issue-104-106-107-upgrade-additive-file-helper-gaps.md
- ADR status: approved

## Applicable Guardrail Controls (Normative)
- Applicable control IDs: SDD-C-001, SDD-C-002, SDD-C-003, SDD-C-004, SDD-C-005, SDD-C-006, SDD-C-007, SDD-C-008, SDD-C-009, SDD-C-010, SDD-C-011, SDD-C-012, SDD-C-013, SDD-C-014, SDD-C-015, SDD-C-016, SDD-C-017, SDD-C-018, SDD-C-019, SDD-C-020, SDD-C-021
- Control exception rationale: none

## Implementation Stack Profile (Normative)
- Backend stack profile: python_plus_fastapi_pydantic_v2
- Frontend stack profile: none
- Test automation profile: pytest_vitest_playwright_pact
- Agent execution model: single-agent
- Managed service preference: stackit-managed-first
- Managed service exception rationale: none (no managed service involved)
- Runtime profile: local-first-docker-desktop-kubernetes
- Local Kubernetes context policy: docker-desktop-preferred
- Local provisioning stack: crossplane-plus-helm
- Runtime identity baseline: eso-plus-argocd-plus-keycloak
- Local-first exception rationale: none (infra/tooling change only; no local runtime execution required)

## Objective
- Business outcome: generated-consumer upgrade validation MUST NOT emit false conflict signals for additive blueprint-required files, and generated-consumer repos MUST receive all Python helper files required by distributed platform scripts after upgrade.
- Success metric: `blueprint-upgrade-consumer-preflight` conflict count does not include baseline-absent additive files; `make infra-smoke` and `make auth-reconcile-argocd-repo-credentials` succeed in upgraded generated-consumer repos without missing-helper errors.

## Normative Requirements

### Functional Requirements (Normative)

#### Additive-file conflict classification (#104)
- FR-001 `scripts/lib/blueprint/upgrade_consumer.py` `_classify_entries` MUST NOT emit `action=conflict` when `baseline_content` is unavailable and both source and target files exist.
- FR-002 when baseline content is unavailable and source content is identical to target content, the entry MUST be classified as `action=skip` with `operation=none` and reason "additive file already at source version; safe to take".
- FR-003 when baseline content is unavailable and source content differs from target content, the entry MUST be classified as `action=merge-required` with `operation=merge` and reason "additive file: not present at baseline ref; target diverges from source; manual merge advisory".
- FR-004 `action=conflict` MUST be reserved exclusively for cases where `baseline_content` is available and a 3-way merge produces unresolvable markers.

#### Missing platform helper distribution (#106/#107)
- FR-005 `scripts/lib/platform/apps/runtime_workload_helpers.py` MUST be relocated to `scripts/lib/infra/runtime_workload_helpers.py`.
- FR-006 `scripts/lib/platform/auth/argocd_repo_credentials_json.py` MUST be relocated to `scripts/lib/infra/argocd_repo_credentials_json.py`.
- FR-007 `scripts/bin/platform/apps/smoke.sh` MUST reference the helper at `scripts/lib/infra/runtime_workload_helpers.py`.
- FR-008 `scripts/bin/platform/auth/reconcile_argocd_repo_credentials.sh` MUST reference the helper at `scripts/lib/infra/argocd_repo_credentials_json.py`.
- FR-009 the fast quality lane MUST fail when any `python3 "$ROOT_DIR/scripts/lib/..."` invocation in `scripts/bin/platform/**` references a path absent from the repository.

### Non-Functional Requirements (Normative)
- NFR-SEC-001 the classification change MUST NOT introduce new secret or auth surface exposure.
- NFR-OBS-001 upgrade plan/apply entries MUST continue to emit `action`, `reason`, and `baseline_content_available` fields; reclassified entries MUST use the same field schema as existing `merge-required` entries.
- NFR-REL-001 the classification fix MUST be backward-compatible: for any path previously classified as `merge-required`, the new behavior MUST NOT reclassify it as `conflict`.
- NFR-OPS-001 the missing-helper guard MUST emit a deterministic human-readable error identifying the offending script path and the missing helper path when triggered.

## Normative Option Decision
- Option A: relocate helpers to `scripts/lib/infra/` (blueprint-managed root; automatic upgrade distribution)
- Option B: add helpers to `required_files` in `contract.yaml` (upgrade distributes, but contradicts platform-editable semantics for the `scripts/lib/platform/` directory root)
- Selected option: OPTION_A
- Rationale: `scripts/lib/infra/` is already declared as a `blueprint_managed_roots` entry so files placed there automatically enter the upgrade candidate set without any contract.yaml change. The helpers are pure JSON-parsing utilities with no expected consumer customization; the `scripts/lib/platform/` namespace is semantically wrong for them. Option B would create a contract inconsistency between `required_files` ownership and the `platform_editable_roots` declaration.

## Contract Changes (Normative)
- Config/Env contract: none
- API contract: none
- Event contract: none
- Make/CLI contract: none (existing `quality-infra-shell-source-graph-check` target covers the new guard without requiring a new target)
- Docs contract: AGENTS.decisions.md MUST record the helper namespace correction and classification fix rationale

## Blueprint Upstream Defect Escalation (Normative)
- Upstream issue URL: none (this IS the upstream fix)
- Temporary workaround path: none
- Replacement trigger: none
- Workaround review date: none

## Normative Acceptance Criteria
- AC-001 `blueprint-upgrade-consumer-preflight` MUST NOT list `scripts/bin/infra/contract_test_fast.sh` (or any other additive file with matching source/target content) under `conflicts`.
- AC-002 when source content differs from target content for a baseline-absent file, the entry MUST appear under `manual_merge` (not `conflicts`) in preflight output.
- AC-003 a generated-consumer repo upgraded to the fixed version MUST contain `scripts/lib/infra/runtime_workload_helpers.py` and `scripts/lib/infra/argocd_repo_credentials_json.py`.
- AC-004 `DRY_RUN=false make infra-smoke` MUST NOT emit helper-file-not-found for `runtime_workload_helpers.py` in an upgraded generated-consumer repo.
- AC-005 `make auth-reconcile-argocd-repo-credentials` MUST NOT emit helper-file-not-found for `argocd_repo_credentials_json.py` in an upgraded generated-consumer repo.
- AC-006 `make quality-infra-shell-source-graph-check` MUST fail when a `scripts/bin/platform/**` shell script references a missing Python helper under `scripts/lib/`.
- AC-007 automated tests MUST cover: additive-file skip classification, additive-file merge-required classification, and the missing-helper guard triggering on an absent path.

## Informative Notes (Non-Normative)
- Context: all three issues were first observed during a real upgrade to blueprint v1.0.8. The missing-helper defects (#106/#107) share the same root cause: Python utilities were introduced in `scripts/lib/platform/` (a protected root) instead of `scripts/lib/infra/` (a blueprint-managed root), so the upgrade engine never distributed them.
- Tradeoffs: relocating the helpers makes them blueprint-managed, which removes the ability for consumers to override them. Given their pure-utility nature (kubectl JSON parsing, ArgoCD credential formatting), this tradeoff is acceptable.

## Explicit Exclusions
- Full audit of all `scripts/bin/platform/**` Python helper references beyond the two identified in #106/#107 (guard covers future cases automatically)
- Resync or postcheck flow changes beyond the classification fix
- Consumer-editable platform logic migration
