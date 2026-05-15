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
- ADR path: docs/blueprint/architecture/decisions/ADR-issue-296-workaround-manifest-action-path-check.md
- ADR status: approved
- SPEC_READY_EXCEPTION: none
- authorized-by: none

## Applicable Guardrail Controls (Normative)
- Applicable control IDs: SDD-C-001, SDD-C-002, SDD-C-003, SDD-C-004, SDD-C-005, SDD-C-006, SDD-C-007, SDD-C-008, SDD-C-009, SDD-C-010, SDD-C-011, SDD-C-012, SDD-C-016, SDD-C-017, SDD-C-019, SDD-C-020, SDD-C-021
- Control exception rationale: SDD-C-013 N/A — no runtime service capability; SDD-C-014 N/A — no local runtime baseline; SDD-C-015 N/A — no app delivery workflow impact; SDD-C-018 N/A — no consumer workaround lifecycle; SDD-C-022 N/A — no HTTP route scope; SDD-C-023 N/A — no filter/payload-transform logic

## Implementation Stack Profile (Normative)
- Backend stack profile: python-tooling-only (no FastAPI; pure Python CLI/checker script)
- Frontend stack profile: none
- Test automation profile: pytest-unit (tests/blueprint/)
- Agent execution model: single-agent
- Managed service preference: stackit-managed-first
- Managed service exception rationale: N/A — tooling-only change; no runtime service involved
- Runtime profile: local-first-docker-desktop-kubernetes
- Local Kubernetes context policy: docker-desktop-preferred
- Local provisioning stack: crossplane-plus-helm
- Runtime identity baseline: eso-plus-argocd-plus-keycloak
- Local-first exception rationale: N/A — tooling-only scope; no runtime deployment

## Objective
- Business outcome: A blueprint maintainer committing a manifest entry with a typo in `action_path` receives a CI failure immediately rather than discovering the error at consumer upgrade time after the release is shipped.
- Success metric: `make quality-workaround-manifest-check` exits non-zero within 1 second when any `action_path` in `manifest.yaml` does not resolve to an existing file, and exits zero for the current valid manifest.

## Normative Requirements

### Functional Requirements (Normative)

- FR-001 The `quality-workaround-manifest-check` Make target MUST exist in `make/blueprint.generated.mk` and MUST invoke `scripts/bin/quality/check_workaround_manifest.py` via `uv run python3`.
- FR-002 `scripts/bin/quality/check_workaround_manifest.py` MUST read `.agents/skills/blueprint-consumer-upgrade/workarounds/manifest.yaml`, iterate every `action_path` value across all version blocks, resolve each path relative to the skill root (`.agents/skills/blueprint-consumer-upgrade/`), and exit non-zero with a descriptive error message for each missing file.
- FR-003 `quality-workaround-manifest-check` MUST be wired into `scripts/bin/quality/hooks_fast.sh` via an unconditional `run_check` call.
- FR-004 A pytest test in `tests/blueprint/test_workaround_manifest_check.py` MUST verify: (a) the checker exits 0 for a manifest whose `action_path` files all exist, (b) the checker exits non-zero and prints a descriptive error for a manifest with a missing `action_path` file, and (c) all real v1.10.0 entries in the live manifest resolve to existing files in the repository.
- FR-005 `quality-workaround-manifest-check` MUST be added to the `.PHONY` target list in `make/blueprint.generated.mk` and its template counterpart `scripts/templates/blueprint/bootstrap/make/blueprint.generated.mk.tmpl`.

### Non-Functional Requirements (Normative)

- NFR-PERF-001 The checker MUST complete in under 1 second for the current manifest (4 entries, 4 file existence checks).
- NFR-MAINT-001 The checker MUST read `manifest.yaml` via `yaml.safe_load` directly — it MUST NOT import or depend on `scripts/lib/blueprint/upgrade_workarounds.py` to avoid coupling the gate to engine internals.
- NFR-ADDITIVE-001 No existing quality checks in `hooks_fast.sh` MUST be removed or altered by this work item.
- NFR-SEC-001 The checker MUST NOT execute any file content — it MUST only check file existence via `Path.exists()`.
- NFR-OBS-001 The checker MUST print `[quality-workaround-manifest-check]`-prefixed output to stdout on success and stderr on failure, consistent with the existing checker convention.
- NFR-REL-001 If `manifest.yaml` is absent, the checker MUST exit non-zero with a clear error message rather than raising an unhandled exception.
- NFR-OPS-001 The Make target MUST be self-documenting via an inline `## <description>` comment following the existing pattern in `make/blueprint.generated.mk`.
- NFR-A11Y-001 N/A — no UI or frontend changes.

## Normative Option Decision
- Option A: Standalone Python checker script (`check_workaround_manifest.py`) invoked via a dedicated Make target and wired into `hooks_fast.sh`.
- Option B: Extend `check_sdd_assets.py` with a new workaround-manifest section.
- Selected option: OPTION_A
- Rationale: The workaround catalogue is a bounded artefact (`blueprint-consumer-upgrade` skill) with no dependency on SDD assets. A standalone checker keeps `check_sdd_assets.py` focused on SDD governance and makes the workaround gate independently testable and independently skippable if the skill is absent in future.

## Contract Changes (Normative)
- Config/Env contract: none
- API contract: none
- OpenAPI / Pact contract path: none
- Event contract: none
- Make/CLI contract: `quality-workaround-manifest-check` added to `make/blueprint.generated.mk` and blueprint.generated.mk.tmpl; wired into `quality-hooks-fast`
- Docs contract: none

## Blueprint Upstream Defect Escalation (Normative)
- Upstream issue URL: none
- Temporary workaround path: none
- Replacement trigger: none
- Workaround review date: none

## Normative Acceptance Criteria

- AC-001 `make quality-workaround-manifest-check` exits 0 against the current `manifest.yaml` (all 4 v1.10.0 entries have valid `action_path` files).
- AC-002 `make quality-workaround-manifest-check` exits non-zero and prints a `[quality-workaround-manifest-check]`-prefixed error to stderr when a manifest entry references a non-existent `action_path`.
- AC-003 `make quality-hooks-fast` summary includes `quality-workaround-manifest-check  PASS`.
- AC-004 `pytest tests/blueprint/test_workaround_manifest_check.py` passes, covering: valid manifest exit 0, missing file exit non-zero with error output, all real v1.10.0 entries exist.
- AC-005 `make quality-hooks-fast` passes end-to-end without introducing new failures.

## Informative Notes (Non-Normative)
- Context: The workaround catalogue was introduced in issue #268 (PR #292). The `action_path` CI gate was explicitly deferred from that scope to keep the initial delivery self-contained. The v1.10.0 entries were manually verified at the time of authoring.
- Tradeoffs: Option A (standalone checker) adds a new script file vs. Option B (extend check_sdd_assets.py) which would keep the checker count low but conflate unrelated governance domains. Option A wins on separation of concerns.
- Clarifications: none

## Explicit Exclusions
- Validating the semantic correctness of workaround action files (e.g., YAML schema, patch syntax) — path existence only.
- Adding `quality-workaround-manifest-check` to `quality-hooks-run` or `quality-ci-blueprint` — `hooks_fast.sh` wiring is sufficient; slow/CI gate wiring is out of scope.
- Checking that `landed_in` fields are valid version tags — out of scope.
