# Specification

## Spec Readiness Gate (Blocking)
<!-- SPEC_PRODUCT_READY=true: intake gate — Product sign-off only; unlocks agent ADR drafting.
     SPEC_READY=true: implementation gate — all sign-offs required; unlocks coding. -->
- SPEC_READY: false
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
- ADR path: docs/blueprint/architecture/decisions/ADR-20260426-upgrade-version-pin-report.md
- ADR status: proposed

## Applicable Guardrail Controls (Normative)
- Applicable control IDs: SDD-C-001, SDD-C-002, SDD-C-003, SDD-C-004, SDD-C-005, SDD-C-006, SDD-C-007, SDD-C-008, SDD-C-009, SDD-C-010, SDD-C-011, SDD-C-012, SDD-C-013, SDD-C-014, SDD-C-015, SDD-C-016, SDD-C-018
- Control exception rationale: SDD-C-017 excluded — no HTTP route, query/filter, or new API endpoint changes. SDD-C-019 excluded — no managed-service runtime decisions in scope. SDD-C-020 excluded — this is blueprint-internal tooling with no consumer workaround lifecycle. SDD-C-021 excluded — no new API or event contracts introduced.

## Implementation Stack Profile (Normative)
- Backend stack profile: python_scripting_plus_bash (Python stdlib + subprocess; no web framework)
- Frontend stack profile: none
- Test automation profile: pytest (existing `tests/blueprint/` suite; new unit fixtures for pin diff logic)
- Agent execution model: specialized-subagents-isolated-worktrees
- Managed service preference: explicit-consumer-exception
- Managed service exception rationale: no managed service provisioned or consumed; this work item adds a Python script, modifies shell orchestration and a Python report generator only
- Runtime profile: local-first-docker-desktop-kubernetes
- Local Kubernetes context policy: docker-desktop-preferred
- Local provisioning stack: crossplane-plus-helm
- Runtime identity baseline: eso-plus-argocd-plus-keycloak
- Local-first exception rationale: no Kubernetes, Crossplane, or runtime identity components exercised; local-first profile declared for compliance only

## Objective
- Business outcome: When a consumer runs `make blueprint-upgrade-consumer`, the residual report surfaces every version pin change in `scripts/lib/infra/versions.sh` between the baseline and target blueprint tags — including which consumer-owned bootstrap templates reference each changed pin — so the operator knows exactly what manual template sync is required after `make infra-bootstrap` before discovering drift reactively via `make infra-validate`.
- Success metric: Given a real tag pair where at least one pin in `versions.sh` changed, `artifacts/blueprint/upgrade-residual.md` MUST include a "Version Pin Changes" section listing each changed pin, its old and new value, and all template files under `scripts/templates/infra/bootstrap/` that reference the pin variable name, with a prescribed action item. When no pins changed, the section MUST state this explicitly.

## Normative Requirements

### Functional Requirements (Normative)

- FR-001 The version pin diff script MUST read `scripts/lib/infra/versions.sh` from both the baseline blueprint ref and the target blueprint ref using local git operations against the already-cloned blueprint source repository; no external HTTP calls are permitted.
- FR-002 The version pin diff script MUST parse all `VARIABLE="value"` and `VARIABLE=value` assignments from both `versions.sh` files and classify each variable as: unchanged, changed (old_value → new_value), new (present only in target), or removed (present only in baseline).
- FR-003 For each changed or new pin variable, the script MUST scan `scripts/templates/infra/bootstrap/` in the consumer working tree and record all file paths that contain a reference to the variable name.
- FR-004 The script MUST emit `artifacts/blueprint/version_pin_diff.json` containing: `baseline_ref`, `target_ref`, `changed_pins` list, `new_pins` list, `removed_pins` list, and `unchanged_count` integer. Each pin entry MUST include `variable`, `old_value` (null for new pins), `new_value` (null for removed pins), and `template_references` list.
- FR-005 The script MUST NOT propagate a non-zero exit code when git operations or template scanning encounter an error; it MUST log the error, emit a partial JSON artifact with a top-level `error` string field, and exit zero so the pipeline continues.
- FR-006 The upgrade pipeline MUST invoke `upgrade_version_pin_diff.py` after Stage 1 (pre-flight) passes and before Stage 2 (apply) begins; the pipeline MUST continue regardless of the script's exit code.
- FR-007 The residual report script MUST include a "Version Pin Changes" section that reads `artifacts/blueprint/version_pin_diff.json` and formats all changed, new, and removed pins with their `template_references` and a prescribed action.
- FR-008 When `version_pin_diff.json` reports zero entries across all categories, the residual report MUST state: "No version pin changes detected between `<baseline_ref>` and `<target_ref>`."
- FR-009 Each changed pin entry in the residual report MUST include the prescribed action: "After running `make infra-bootstrap`, verify and sync affected templates under `scripts/templates/infra/bootstrap/`, then re-run `make infra-validate`."
- FR-010 The upgrade consumer skill runbook (`.agents/skills/blueprint-consumer-upgrade/SKILL.md`) MUST be updated to document the version pin diff residual report section and instruct operators to review it before running `make infra-bootstrap`.

### Non-Functional Requirements (Normative)

- NFR-PERF-001 `upgrade_version_pin_diff.py` MUST complete within 10 seconds for any consumer repository; all operations MUST be local git commands against the already-cloned source repository; no network calls are permitted.
- NFR-SEC-001 The script MUST NOT write any secrets or credentials to `version_pin_diff.json` or any log output; `versions.sh` contains only tool and chart version strings, not secrets — no filtering is required.
- NFR-OBS-001 The script MUST log each stage of its execution to stdout using the existing pipeline logging conventions (`log_info`/`log_warning` from the upgrade pipeline library); all errors MUST be written to stderr.
- NFR-REL-001 The pipeline MUST remain fully functional when `upgrade_version_pin_diff.py` fails or produces an incomplete artifact; when `version_pin_diff.json` is absent or malformed, the residual report MUST note: "Version pin diff unavailable: `<reason>`. Manual fallback: `git diff <baseline_ref> <target_ref> -- scripts/lib/infra/versions.sh`."
- NFR-OPS-001 An operator MUST be able to invoke `upgrade_version_pin_diff.py` standalone — `python3 scripts/lib/blueprint/upgrade_version_pin_diff.py --repo-root . --source-path <cloned-source-path> --baseline-ref <ref> --target-ref <ref>` — and receive the JSON artifact without running the full pipeline.

## Normative Option Decision
- Option A: Run version pin diff between Stage 1 and Stage 2 (before any file mutations), emit JSON artifact consumed by Stage 10 residual report.
- Option B: Compute pin diff inline inside `upgrade_residual_report.py` at Stage 10 (post-mutation, simpler integration, no new pipeline stage).
- Selected option: OPTION_A
- Rationale: Proactive warning before mutations gives the operator full context upfront and keeps the residual report's role as a consumer of pre-computed artifacts consistent with how `contract_resolve_decisions.json` and `validate.json` are sourced. OPTION_B couples analysis logic into the report generator and prevents the diff from being referenced by future pipeline stages.

## Contract Changes (Normative)
- Config/Env contract: no new environment variables; the script consumes `BLUEPRINT_UPGRADE_REF` and `BLUEPRINT_UPGRADE_SOURCE` already declared by the pipeline
- API contract: none
- OpenAPI / Pact contract path: none
- Event contract: none
- Make/CLI contract: no new make targets; `upgrade_version_pin_diff.py` is invoked directly from `upgrade_consumer_pipeline.sh`
- Docs contract: `.agents/skills/blueprint-consumer-upgrade/SKILL.md` updated to document the new residual report section

## Blueprint Upstream Defect Escalation (Normative)
- Upstream issue URL: none
- Temporary workaround path: none
- Replacement trigger: none
- Workaround review date: none

## Normative Acceptance Criteria
- AC-001 Given a tag pair where `TERRAFORM_VERSION` changes from `1.12.0` to `1.13.3` and one template file under `scripts/templates/infra/bootstrap/` contains the string `TERRAFORM_VERSION`, the residual report MUST include a "Version Pin Changes" section listing `TERRAFORM_VERSION: 1.12.0 → 1.13.3`, that template file path, and the prescribed sync action.
- AC-002 Given a tag pair where no variables in `versions.sh` change, the residual report MUST state "No version pin changes detected between `<baseline_ref>` and `<target_ref>`."
- AC-003 Given a new pin variable present only in the target `versions.sh` (no old value), it MUST appear in a "New Pins" subsection with its new value and any template references.
- AC-004 Given a pin variable present in baseline `versions.sh` but absent from target `versions.sh`, it MUST appear in a "Removed Pins" subsection with its old value.
- AC-005 Given a git error when reading `versions.sh` from the baseline ref, the pipeline MUST continue and the residual report MUST include "Version pin diff unavailable: `<error message>`. Manual fallback: `git diff <baseline_ref> <target_ref> -- scripts/lib/infra/versions.sh`."
- AC-006 The unit tests for `upgrade_version_pin_diff.py` MUST assert that parsing two fixture `versions.sh` strings with a known set of changed, new, and removed variables produces the correct `changed_pins`, `new_pins`, `removed_pins`, and `unchanged_count` in `version_pin_diff.json`, with correct `old_value`, `new_value`, and `template_references` per entry.

## Informative Notes (Non-Normative)
- Context: The scripted upgrade pipeline (PR #193) resolved F-001–F-010 from the v1.0.0→v1.6.0 upgrade. A persistent gap is that consumers learn about version pin drift only after running `make infra-bootstrap` and `make infra-validate` — too late to act proactively. Issue #164 filed by the same upgrade incident that motivated Issue #189.
- Tradeoffs: Grepping for variable names (e.g., `TERRAFORM_VERSION`) in template files catches explicit references but will miss cases where the template uses the pin's value directly (e.g., hardcoded `1.12.0`). Value-based matching is deferred — the variable-name grep covers the common case where templates source `versions.sh` and use the variable name.
- Clarifications: The automated template-sync option (`BLUEPRINT_UPGRADE_SYNC_TEMPLATES=true`) proposed in the issue is explicitly deferred — this work item covers detection and reporting only.

## Explicit Exclusions
- Automated template sync (`BLUEPRINT_UPGRADE_SYNC_TEMPLATES=true`) — deferred; reporting scope only in this work item.
- Semantic analysis of which rendered overlay values are affected by each pin change — deferred; file-name grep is sufficient for the target operator workflow.
- Version pin comparison for sources other than `scripts/lib/infra/versions.sh` (e.g., pinned GitHub Actions versions, Dockerfile base image tags) — out of scope for this work item.
