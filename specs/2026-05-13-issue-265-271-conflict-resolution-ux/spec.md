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
- ADR path: docs/blueprint/architecture/decisions/ADR-issue-265-271-conflict-resolution-ux.md
- ADR status: approved

## Applicable Guardrail Controls (Normative)
- Applicable control IDs: SDD-C-002, SDD-C-003, SDD-C-004, SDD-C-005, SDD-C-006, SDD-C-007, SDD-C-008, SDD-C-011, SDD-C-016, SDD-C-017, SDD-C-019, SDD-C-023
- Control exception rationale:
  - SDD-C-001: all requirements are fully derivable from issue evidence and real upgrade data; no missing inputs.
  - SDD-C-009: blueprint-internal tooling; no STACKIT managed service decision required.
  - SDD-C-010: no production service; no operational runbook required.
  - SDD-C-012: no HTTP routes; no curl-based smoke required.
  - SDD-C-013: no STACKIT managed service selection in scope.
  - SDD-C-014: no infra/runtime scope; pure Python + Bash scripts.
  - SDD-C-015: no app delivery impact; app onboarding contract unchanged.
  - SDD-C-018: not an upstream defect workaround; this is net-new functionality.
  - SDD-C-020: not a cross-cutting architectural change touching all SDD phases.
  - SDD-C-021: no contract or delivery-scope ambiguity requiring discovery-level planning gate.
  - SDD-C-022: no HTTP route handlers or filter/query logic in scope.
  - SDD-C-024: no positive-path filter/transform test gate applicable; no HTTP routes changed.

## Implementation Stack Profile (Normative)
- Backend stack profile: blueprint-tooling-python-bash (Python 3 stdlib + existing upgrade engine patterns; no FastAPI/Pydantic runtime)
- Frontend stack profile: none
- Test automation profile: pytest (existing infra test pattern under tests/infra/)
- Agent execution model: single-agent
- Managed service preference: explicit-consumer-exception
- Managed service exception rationale: blueprint-internal tooling scripts only; no STACKIT managed services in scope
- Runtime profile: local-first-docker-desktop-kubernetes
- Local Kubernetes context policy: not-applicable-stackit-runtime
- Local provisioning stack: crossplane-plus-helm
- Runtime identity baseline: custom-approved-exception
- Local-first exception rationale: Python + Bash scripts only; no Docker Desktop, Crossplane, ESO, ArgoCD, or Keycloak runtime involvement

## Objective
- Business outcome: reduce upgrade conflict resolution from ~25 minutes of ad-hoc scripting and manual classification to a single `make blueprint-upgrade-consumer-resolve` invocation that auto-applies all classifiable conflicts and presents a residual table of only the rows requiring human judgement.
- Success metric: on the real 88-conflict upgrade (dhe-marketplace v1.7.0 → v1.10.0), ≥85 conflicts are auto-resolved by the resolve target with zero human decisions required for blueprint-managed-root files; ≤3 rows remain in the residual table for human review.

## Normative Requirements

### Functional Requirements (Normative)

- FR-001: The upgrade engine MUST write `artifacts/blueprint/upgrade_triage.json` after `_apply_entries` completes whenever `conflict_count > 0`.
- FR-002: `upgrade_triage.json` MUST conform to the versioned schema in `scripts/lib/blueprint/schemas/upgrade_triage.schema.json` and MUST include for each conflict entry: `path`, `ownership_class`, `ownership_evidence`, `recommended_action`, `reason`, `source_diff_summary`, `target_diff_from_baseline`.
- FR-003: `recommended_action` MUST be derived from `ownership_class` per the following mapping table (EXACTLY ONE OF per entry):
  - `blueprint-managed-root` → `take_source`
  - `required-file` → `take_source`
  - `init-managed` → `take_source`
  - `conditional-scaffold` → `take_source`
  - `consumer-seeded` → `take_target`
  - `blueprint-managed` (catch-all) → `human_required`
  - any other unrecognised class → `human_required`
- FR-004: `blueprint/contract.yaml` MUST NOT appear in `upgrade_triage.json`; it is owned exclusively by Stage 3 (contract resolver) and MUST be excluded at triage emission time.
- FR-005: `upgrade_triage.json` MUST NOT contain `source_content`, `target_content`, or `baseline_content` fields; these remain in the per-file `.conflict.json` artifacts only.
- FR-006: `make blueprint-upgrade-consumer-resolve` MUST exist as a new make target backed by `scripts/lib/blueprint/upgrade_consumer_resolve.py`.
- FR-007: The resolve script MUST read `upgrade_triage.json`, apply all `take_source`, `take_target`, and `delete` rows by writing the chosen content to the working-tree file, clear the corresponding `.conflict.json` from `artifacts/blueprint/conflicts/`, and write `artifacts/blueprint/upgrade_resolve.json` with per-action results.
- FR-008: After auto-resolution, the resolve script MUST print a single residual table to stdout showing only `human_required` rows, sorted by ownership class then path, with a truncation footer when row count exceeds 20.
- FR-009: The residual table MUST include the auto-resolved count, and per-row: path, ownership class, source diff line summary, target diff line summary.
- FR-010: The resolve script MUST support `INTERACTIVE=true` (or `--interactive` flag) for one-at-a-time prompting of `human_required` rows.
- FR-011: The resolve script MUST support `--accept-source ALL` and `--accept-target ALL` batch flags that apply all `human_required` rows as if the human chose source or target respectively.
- FR-012: The resolve script MUST support `--dry-run` to print planned actions without writing any files or clearing any conflict artifacts.

### Non-Functional Requirements (Normative)

- NFR-IDM-001: The resolve script MUST be idempotent — re-running on an already-resolved working tree MUST produce no file changes and MUST exit 0.
- NFR-SCH-001: `upgrade_triage.json` MUST carry `schema_version: 1` as a top-level field and MUST validate against `scripts/lib/blueprint/schemas/upgrade_triage.schema.json`.
- NFR-SEC-001: `upgrade_triage.json` MUST NOT write file contents (`source_content`, `target_content`, `baseline_content`) — diff summaries only — to avoid inadvertently embedding secrets present in upgraded files.
- NFR-REL-001: If `upgrade_triage.json` is absent or fails schema validation when `make blueprint-upgrade-consumer-resolve` is invoked, the script MUST exit non-zero with a human-readable diagnostic message and MUST NOT produce a Python traceback as the primary output.
- NFR-OBS-001: The resolve script MUST print one summary line per applied action to stdout in the format `upgrade-resolve: <action> <path>` so output is grep-parseable by agents.
- NFR-A11Y-001: N/A — CLI tool with no browser-rendered UI surface.
- NFR-OPS-001: N/A — blueprint tooling script; no production service runbook required.

## Normative Option Decision
- Option A (conservative catch-all): `blueprint-managed` ownership (catch-all, the class assigned to files not explicitly in any blueprint ownership category) maps to `recommended_action = "human_required"`. Safe even before Issue #270 (explicit consumer test ownership markers) ships; no risk of auto-overwriting consumer-modified files.
- Option B (source-exists inference): If `UpgradeEntry.source_exists = True` and ownership is `blueprint-managed`, infer `take_source`. Reduces `human_required` rows but can auto-overwrite consumer modifications to files not yet in a named blueprint category.
- Selected option: OPTION_A
- Rationale: without Issue #270's explicit consumer ownership markers, the boundary between blueprint-managed and consumer-modified files in the catch-all class is not deterministic. Conservative classification preserves consumer changes at the cost of more residual rows; this is the correct trade-off for a first release. Option B can be adopted once #270 ships explicit consumer markers.

## Contract Changes (Normative)
- Config/Env contract: new `INTERACTIVE` env var and `--accept-source`, `--accept-target`, `--dry-run` flags for `upgrade_consumer_resolve.py`; `BLUEPRINT_UPGRADE_RESOLVE_SOURCE` not added (target is always the current working tree).
- API contract: none (no HTTP routes).
- OpenAPI / Pact contract path: none
- Event contract: none.
- Make/CLI contract: new make target `blueprint-upgrade-consumer-resolve` in `blueprint.generated.mk`; new artifact paths `artifacts/blueprint/upgrade_triage.json` and `artifacts/blueprint/upgrade_resolve.json`; new schema `scripts/lib/blueprint/schemas/upgrade_triage.schema.json`.
- Docs contract: `blueprint-consumer-upgrade/SKILL.md` Stage 2 step table updated to reference the resolve target; pipeline overview in `upgrade_consumer_pipeline.sh` usage block updated.

## Blueprint Upstream Defect Escalation (Normative)
- Upstream issue URL: none
- Temporary workaround path: none
- Replacement trigger: none
- Workaround review date: none

## Normative Acceptance Criteria

- AC-001: After a Stage 2 engine run producing ≥1 conflict, `artifacts/blueprint/upgrade_triage.json` MUST exist and pass `jsonschema` validation against `upgrade_triage.schema.json`.
- AC-002: Every triage entry with `ownership_class = "blueprint-managed-root"` MUST carry `recommended_action = "take_source"`.
- AC-003: Every triage entry with `ownership_class = "blueprint-managed"` (catch-all) MUST carry `recommended_action = "human_required"`.
- AC-004: `blueprint/contract.yaml` MUST NOT appear in `upgrade_triage.json` regardless of its conflict status.
- AC-005: `upgrade_triage.json` entries MUST NOT contain `source_content`, `target_content`, or `baseline_content` keys.
- AC-006: After `make blueprint-upgrade-consumer-resolve`, all `take_source` entries MUST have their working-tree file replaced with source content and their `.conflict.json` cleared.
- AC-007: After `make blueprint-upgrade-consumer-resolve`, `human_required` entries MUST remain untouched in `artifacts/blueprint/conflicts/`.
- AC-008: `artifacts/blueprint/upgrade_resolve.json` MUST exist after resolve and MUST list each applied action with `path`, `action_taken`, and `result`.
- AC-009: The residual table MUST list `human_required` rows sorted by ownership class then path; when row count exceeds 20, a footer MUST indicate the total count and the full path to `upgrade_triage.json`.
- AC-010: `make blueprint-upgrade-consumer-resolve INTERACTIVE=true` MUST prompt for each `human_required` row before writing; batch flags MUST skip prompts.

## Informative Notes (Non-Normative)
- Context: issue evidence from real consumer upgrade (dhe-marketplace v1.7.0 → v1.10.0, PR #62) — 88 conflicts, 85 blueprint-managed-root (take_source), 3 blueprint-managed catch-all (human_required), 1 contract.yaml (excluded). The 25-minute resolution was fully ad-hoc; this work item makes the common case zero-effort.
- Tradeoffs: Option A's conservative catch-all produces more `human_required` rows than Option B until Issue #270 ships. For the real upgrade evidence (3 catch-all rows), this is acceptable. The 25-minute reduction is still achieved on the 85-row majority.
- Clarifications: `source_diff_summary` and `target_diff_from_baseline` in the triage JSON are computed using `difflib` on content available in the per-file `.conflict.json` (read at triage emission time). The triage stores the human-readable summary string (e.g. "+3 -1 lines"), not the full diff, to keep the manifest compact.

## Explicit Exclusions
- Issue #270 (explicit consumer test ownership markers): deferred. The `human_required` catch-all covers this correctly until #270 ships.
- Issue #267 (`blueprint-upgrade-consumer-finalize` target): separate work item; not in scope.
- Issue #269 (auto-clone upgrade source URL): separate work item; not in scope.
- Interactive TUI (ncurses/lazygit-style): rejected; heavy dependency, not portable.
- HTML conflict report: rejected; browser context switch adds friction for the typically-small residual table.
