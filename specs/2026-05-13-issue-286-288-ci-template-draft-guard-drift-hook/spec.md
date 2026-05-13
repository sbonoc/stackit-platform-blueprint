# Specification

## Spec Readiness Gate (Blocking)
<!-- SPEC_PRODUCT_READY=true: intake gate — Product sign-off only; unlocks agent ADR drafting.
     SPEC_READY=true: implementation gate — all sign-offs required; unlocks coding. -->
- SPEC_READY: true
- SPEC_PRODUCT_READY: true
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
- ADR path: docs/blueprint/architecture/decisions/ADR-issue-286-288-ci-template-draft-guard-drift-hook.md
- ADR status: approved

## Applicable Guardrail Controls (Normative)
- Applicable control IDs: SDD-C-001, SDD-C-002, SDD-C-003, SDD-C-004, SDD-C-005, SDD-C-006, SDD-C-007, SDD-C-008, SDD-C-009, SDD-C-010, SDD-C-011, SDD-C-012, SDD-C-016, SDD-C-017, SDD-C-019, SDD-C-020, SDD-C-021, SDD-C-024
- Control exception rationale:
  - SDD-C-013 (STACKIT managed services): N/A — CI/quality tooling only; no runtime capability changes
  - SDD-C-014 (local-first runtime baseline): N/A — no local Kubernetes provisioning scope
  - SDD-C-015 (app onboarding make targets): N/A — no app delivery workflow scope
  - SDD-C-018 (blueprint upstream defect escalation): N/A — this work item IS the upstream blueprint fix
  - SDD-C-022 (HTTP route/filter smoke): N/A — no HTTP route or filter logic
  - SDD-C-023 (positive-path filter/transform test): N/A — no filter or payload-transform logic

## Implementation Stack Profile (Normative)
- Backend stack profile: python_plus_fastapi_pydantic_v2
- Frontend stack profile: none — no frontend components; CI YAML and Makefile template changes only
- Test automation profile: pytest_vitest_playwright_pact
- Agent execution model: specialized-subagents-isolated-worktrees
- Managed service preference: stackit-managed-first
- Managed service exception rationale: N/A — no runtime provisioning scope
- Runtime profile: local-first-docker-desktop-kubernetes
- Local Kubernetes context policy: docker-desktop-preferred
- Local provisioning stack: crossplane-plus-helm
- Runtime identity baseline: eso-plus-argocd-plus-keycloak
- Local-first exception rationale: N/A — no local runtime provisioning; blueprint tooling and template changes only

## Objective
- Business outcome: New consumer repos bootstrapped from the blueprint template skip CI on draft PRs (matching blueprint's own CI behavior since v1.10.0), and blueprint developers receive commit-time feedback when tracked root-level managed files drift from their bootstrap template counterparts.
- Success metric: (1) Consumer `ci.yml.tmpl` contains the draft-PR types filter and job-level guard. (2) `make quality-validate-bootstrap-template-drift` exits non-zero on drift and zero on parity. (3) All new pytest assertions green; `make quality-hooks-fast` and `make infra-validate` pass.

## Normative Requirements

### Functional Requirements (Normative)

- FR-001 (issue #288): `scripts/templates/consumer/init/.github/workflows/ci.yml.tmpl` MUST include `types: [opened, synchronize, reopened, ready_for_review]` on the `pull_request` event trigger, matching blueprint's own `.github/workflows/ci.yml` since commit `dd4e3f9e` (v1.10.0).

- FR-002 (issue #288): `scripts/templates/consumer/init/.github/workflows/ci.yml.tmpl` `quality-fast` job MUST include `if: github.event_name == 'push' || github.event.pull_request.draft == false` guard, matching blueprint's own `.github/workflows/ci.yml`.

- FR-003 (issue #286): A `quality-validate-bootstrap-template-drift` Make target MUST exist in `scripts/templates/blueprint/bootstrap/make/blueprint.generated.mk.tmpl` (and regenerated `make/blueprint.generated.mk`) and MUST invoke `validate_contract.py --bootstrap-drift-only` to run only `_validate_bootstrap_template_sync`.

- FR-004 (issue #286): `.pre-commit-config.yaml` and `scripts/templates/blueprint/bootstrap/.pre-commit-config.yaml` MUST each include a commit-stage hook with id `quality-validate-bootstrap-template-drift` that fires when any tracked root-level managed file or its bootstrap template counterpart changes, using the `files:` pattern `^(\.dockerignore|\.gitignore|\.editorconfig|\.pre-commit-config\.yaml|Makefile|scripts/templates/blueprint/bootstrap/)`.

- FR-005 (issue #286): `scripts/bin/blueprint/validate_contract.py` MUST accept a `--bootstrap-drift-only` flag that runs only `_validate_bootstrap_template_sync`, exits 0 on parity, and exits 1 on drift or contract load error; output MUST follow the `[infra-validate] error: bootstrap template drift detected for <file>` format produced by the existing full-validation path.

### Non-Functional Requirements (Normative)

- NFR-SEC-001: The `quality-validate-bootstrap-template-drift` pre-commit hook MUST use `language: system` and `entry: make quality-validate-bootstrap-template-drift`; MUST NOT introduce remote code execution, shell injection surface, or credential exposure.

- NFR-OBS-001: N/A — commit-time pre-commit output is sufficient for developer diagnostics; no structured logs, metrics, or traces are required for this tool-layer change.

- NFR-REL-001: Both FR-001/FR-002 and FR-003/FR-004/FR-005 changes MUST be additive; no existing pre-commit hooks, CI steps, or Make targets MUST be removed or modified in behavior.

- NFR-OPS-001: N/A — no runbook changes required; drift error messages from `validate_contract.py` are self-explanatory (`bootstrap template drift detected for <file>; sync with <template>`).

- NFR-A11Y-001: N/A — CI/quality tooling only; no UI components (NFR-A11Y-001 infrastructure exception).

## Normative Option Decision

### Issue #286 — `quality-validate-bootstrap-template-drift` implementation path

- Option A: Add `--bootstrap-drift-only` flag to `validate_contract.py`, exposing the existing `_validate_bootstrap_template_sync` function as a standalone fast check invocable by the pre-commit hook and Make target. Follows the `--branch-only` precedent in the same script.
- Option B: Create a dedicated thin wrapper script `scripts/bin/blueprint/validate_bootstrap_drift.sh` that calls `validate_contract.py` with full validation and filters output. Requires a new file and diverges from the existing fast-path pattern.
- Selected option: OPTION_A
- Rationale: Option A re-uses the established `--branch-only` pattern in `validate_contract.py`; keeps drift-check logic co-located with other contract validators; avoids introducing an additional script file; the `--bootstrap-drift-only` flag name mirrors `--branch-only` making the CLI consistent.

## Contract Changes (Normative)

- Config/Env contract: none — no new environment variables introduced
- API contract: none — no service API changes
- OpenAPI / Pact contract path: none
- Event contract: none
- Make/CLI contract:
  - New Make target `quality-validate-bootstrap-template-drift` added to `scripts/templates/blueprint/bootstrap/make/blueprint.generated.mk.tmpl` and `make/blueprint.generated.mk`
  - New `--bootstrap-drift-only` CLI flag added to `scripts/bin/blueprint/validate_contract.py`
- Docs contract: none — no doc structure changes

## Blueprint Upstream Defect Escalation (Normative)
- Upstream issue URL: none — this work item IS the upstream blueprint fix for issues #286 and #288
- Temporary workaround path: none
- Replacement trigger: none
- Workaround review date: none

## Normative Acceptance Criteria

- AC-001: `scripts/templates/consumer/init/.github/workflows/ci.yml.tmpl` MUST contain the string `types: [opened, synchronize, reopened, ready_for_review]` on a line following `pull_request:`.

- AC-002: `scripts/templates/consumer/init/.github/workflows/ci.yml.tmpl` `quality-fast` job MUST contain `if: github.event_name == 'push' || github.event.pull_request.draft == false`.

- AC-003: `make quality-validate-bootstrap-template-drift` MUST exit 0 when `.pre-commit-config.yaml` matches `scripts/templates/blueprint/bootstrap/.pre-commit-config.yaml` byte-for-byte (or semantic parity as enforced by the validator).

- AC-004: `make quality-validate-bootstrap-template-drift` MUST exit non-zero and print `[infra-validate] error: bootstrap template drift detected for <file>` when drift is present.

- AC-005: `.pre-commit-config.yaml` MUST contain a hook entry with `id: quality-validate-bootstrap-template-drift`, no `stages:` key (commit-stage default), and a `files:` pattern covering all tracked root-level managed files.

- AC-006: `scripts/templates/blueprint/bootstrap/.pre-commit-config.yaml` MUST contain the same `quality-validate-bootstrap-template-drift` hook as `.pre-commit-config.yaml` (mirror parity).

- AC-007: `uv run python3 -m pytest tests/blueprint/test_quality_contracts.py -v` MUST include green assertions for AC-001, AC-002, AC-005, and AC-006.

- AC-008: `make quality-hooks-fast` MUST pass with zero violations after all changes.

- AC-009: `make infra-validate` MUST pass after all changes.

## Informative Notes (Non-Normative)

- Context: Issue #288 is a v1.10.0 propagation gap — the draft-PR skip was added to the blueprint's own CI in commit `dd4e3f9e` but was not propagated to the consumer init template. Issue #286 is a path-gating gap — `validate_bootstrap_template_sync` runs inside `infra-validate` which is gated by `_QG_INFRA_GATE_PATHS`; root dotfiles like `.pre-commit-config.yaml` don't match any gate prefix so local changes are not checked until CI.
- Tradeoffs: Option A for FR-005 adds a fast path to `validate_contract.py` (similar to `--branch-only`) rather than creating a new script; trade-off is slightly larger contract script, offset by consistency.
- Clarifications: none

## Explicit Exclusions

- Excluded item 1: Updating existing consumer repos that already bootstrapped from the template before this fix — consumers apply this fix on next blueprint upgrade.
- Excluded item 2: Adding the `quality-validate-bootstrap-template-drift` target to `blueprint/contract.yaml` `required_targets` — this target is blueprint-internal quality tooling, not a consumer-contract target.
- Excluded item 3: Exposing `--bootstrap-drift-only` as part of the `infra-validate` gate path fix — the path-gating gap in `_QG_INFRA_GATE_PATHS` is not addressed by this work item; CI continues to use `QUALITY_HOOKS_FORCE_FULL=true` for full coverage.
