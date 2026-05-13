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
- ADR path: docs/blueprint/architecture/decisions/ADR-issue-267-269-pipeline-finalize-auto-clone.md
- ADR status: approved

## Applicable Guardrail Controls (Normative)
- Applicable control IDs: SDD-C-002, SDD-C-003, SDD-C-004, SDD-C-005, SDD-C-006, SDD-C-007, SDD-C-008, SDD-C-009, SDD-C-010, SDD-C-011, SDD-C-012, SDD-C-016, SDD-C-017, SDD-C-019, SDD-C-020, SDD-C-021, SDD-C-024
- Control exception rationale:
  - SDD-C-001: no missing inputs; all requirements are fully derivable from issue evidence and real consumer upgrade failures.
  - SDD-C-013: blueprint-internal tooling; no STACKIT managed service decision required.
  - SDD-C-014: no infra/runtime scope; pure Bash scripts change with no Docker Desktop, Crossplane, ESO, ArgoCD, or Keycloak involvement.
  - SDD-C-015: no app delivery impact; app onboarding contract unchanged.
  - SDD-C-018: this IS the upstream fix; no consumer-side workaround escalation required.
  - SDD-C-022: no HTTP route handlers or API endpoints touched.
  - SDD-C-023: no filter or payload-transform logic.

## Implementation Stack Profile (Normative)
- Backend stack profile: blueprint-tooling-bash (Bash scripts only; existing make target orchestration; no new Python in core scope)
- Frontend stack profile: none
- Test automation profile: pytest (existing infra test pattern under tests/infra/)
- Agent execution model: single-agent
- Managed service preference: explicit-consumer-exception
- Managed service exception rationale: blueprint-internal tooling scripts only; no STACKIT managed services in scope
- Runtime profile: local-first-docker-desktop-kubernetes
- Local Kubernetes context policy: not-applicable-stackit-runtime
- Local provisioning stack: crossplane-plus-helm
- Runtime identity baseline: custom-approved-exception
- Local-first exception rationale: Bash scripts only; no runtime infrastructure involved

## Objective
- Business outcome: eliminate the trial-and-error post-apply convergence cycle that costs consumers 15+ minutes and 5 fix→re-run cycles per upgrade; any consumer can reach a green post-upgrade state with a single `make blueprint-upgrade-consumer-finalize` invocation.
- Success metric: a real or simulated upgrade that previously required 5 manual `quality-hooks-run` cycles reaches green state in 1 finalize invocation; pipeline Stage 1b and Stage 5 succeed when `BLUEPRINT_UPGRADE_SOURCE` is a URL (currently they warn or fatal).

## Normative Requirements

### Functional Requirements (Normative)

#### Issue #269 — Auto-clone source URL

- FR-001 The pipeline (`upgrade_consumer_pipeline.sh`) MUST normalize `BLUEPRINT_UPGRADE_SOURCE` to a local path before Stage 1b. If the resolved value of `upgrade_source` does not point to a local directory containing a `.git` subdirectory, the pipeline MUST clone the source with `git clone --depth 1 --branch "$upgrade_ref" "$upgrade_source"` into a temporary directory and use that local path for all subsequent pipeline stages.
- FR-002 The temporary clone directory MUST be registered with a Bash `trap 'rm -rf "$cloned_source_dir"' EXIT` immediately after creation so the directory is removed on all exit paths (success, failure, and interrupt).
- FR-003 Stage 2 engine (`upgrade_consumer.py`) MUST detect when `upgrade_source` is already a local directory at the correct ref and MUST skip its own internal clone in that case, using the pre-cloned path directly.
- FR-004 The local-path form of `BLUEPRINT_UPGRADE_SOURCE` MUST continue to work without triggering the auto-clone step.

#### Issue #267 — Finalize target

- FR-005 A `make blueprint-upgrade-consumer-finalize` target MUST exist and MUST invoke `scripts/bin/blueprint/upgrade_consumer_finalize.sh`.
- FR-006 `upgrade_consumer_finalize.sh` MUST run a sync pass in fixed canonical order. The sync pass MUST include at minimum: `make quality-docs-sync-all`, `make quality-sdd-sync-consumer-init-assets`, `make quality-sdd-sync-policy-snippets`. The sync pass MUST aggregate all failures and MUST NOT fail-fast; a single failing sync target MUST not prevent subsequent sync targets from executing.
- FR-007 `upgrade_consumer_finalize.sh` MUST run a verify pass in fixed canonical order after the sync pass. The verify pass MUST include in order: `make infra-validate`, `make quality-hooks-run`, `make blueprint-upgrade-consumer-validate`, `make blueprint-upgrade-consumer-postcheck`, `make blueprint-upgrade-fresh-env-gate`. The verify pass MUST fail fast on the first failing target and print a summary banner naming the failing target and its exit code.
- FR-008 The pipeline (`upgrade_consumer_pipeline.sh`) MUST invoke `make blueprint-upgrade-consumer-finalize` as its post-Stage-2 tail in place of the current Stages 8 and 9 implementations; Stages 3–7 remain as named pipeline steps preceding finalize. Stage 10 (residual report) continues to run via the EXIT trap.
- FR-009 The `.agents/skills/blueprint-consumer-upgrade/SKILL.md` runbook MUST be updated to document `make blueprint-upgrade-consumer-finalize` as the single canonical post-apply step, replacing the current per-target list in Stage 2b and the ad-hoc guidance.

### Non-Functional Requirements (Normative)

- NFR-IDM-001 `blueprint-upgrade-consumer-finalize` MUST be idempotent: a second invocation after a clean first pass MUST produce no file changes and MUST exit 0.
- NFR-OBS-001 `upgrade_consumer_finalize.sh` MUST emit a `[finalize] <step>: <status>` log line per step (using the repo's `log_info` / `log_error` bootstrap functions) so operators can diagnose which sync or verify step failed without reading the full output.
- NFR-REL-001 The auto-clone cleanup MUST use `trap 'rm -rf "$cloned_source_dir"' EXIT` so the tmp directory is removed on success, failure, and SIGINT; a partial clone MUST NOT be left on disk.
- NFR-SEC-001 Before running `git clone`, the pipeline MUST validate that `upgrade_source` starts with `https://`, `git@`, `ssh://`, or is a local path (starts with `/`, `./`, or `../`); any other form MUST cause the pipeline to abort with an actionable error message. This prevents shell-metacharacter injection in the `git clone` invocation.
- NFR-OPS-001 The pipeline usage block in `upgrade_consumer_pipeline.sh` MUST be updated to document the auto-clone behaviour (URL form triggers a `--depth 1` clone; local path is used as-is). The finalize script usage block MUST document the two-pass structure and the env vars required for coverage-fetch stages.
- NFR-A11Y-001 N/A — CLI tool with no browser-rendered UI surface.

## Normative Option Decision
- Option A: Finalize script wraps only the quality tail (Stage 8+9 equivalents — sync + verify), with Stages 3–7 remaining in the pipeline.
- Option B: Finalize script wraps all post-Stage-2 work (Stages 3–9 + postcheck + fresh-env-gate), making the pipeline a thin Stage-1/1b/2 + finalize wrapper.
- Selected option: OPTION_A
- Rationale: Stages 3–7 require `BLUEPRINT_UPGRADE_SOURCE` and `BLUEPRINT_UPGRADE_REF` env vars and perform content-fetching operations that are tightly coupled to the apply result. The finalize target is primarily the deterministic quality-convergence layer (sync + verify). Option B would make finalize a heavyweight orchestrator that is harder to invoke standalone meaningfully. Option A keeps finalize as the documented post-apply convergence command, matching the issue's suggested two-pass structure, and keeps Stages 3–7 as pipeline-internal steps. The postcheck and fresh-env-gate are added to the verify pass since they were previously missing from the pipeline's Stage 9.

## Contract Changes (Normative)
- Config/Env contract: `BLUEPRINT_UPGRADE_SOURCE` URL form now auto-clones; local path form unchanged. No new env vars required.
- API contract: none
- OpenAPI / Pact contract path: none
- Event contract: none
- Make/CLI contract: new target `blueprint-upgrade-consumer-finalize` added to `blueprint.generated.mk.tmpl` and regenerated; new script `scripts/bin/blueprint/upgrade_consumer_finalize.sh`.
- Docs contract: `.agents/skills/blueprint-consumer-upgrade/SKILL.md` updated; `upgrade_consumer_pipeline.sh` usage block updated.

## Blueprint Upstream Defect Escalation (Normative)
- Upstream issue URL: none
- Temporary workaround path: none
- Replacement trigger: none
- Workaround review date: none

## Normative Acceptance Criteria

- AC-001 `make blueprint-upgrade-consumer-finalize` exists, runs to completion, and exits 0 when all sync and verify steps pass.
- AC-002 Running `make blueprint-upgrade-consumer-finalize` a second time after a clean first pass produces no file changes and exits 0 (idempotent).
- AC-003 Sync pass runs all sync targets in fixed order; a failing sync target does not prevent subsequent sync targets from executing; failures are aggregated and reported after all sync steps complete.
- AC-004 Verify pass fails fast on the first failing target and emits a summary banner naming the failing target and its exit code.
- AC-005 The `blueprint-upgrade-consumer` pipeline invokes `make blueprint-upgrade-consumer-finalize` as its post-Stage-2 tail; behavioural equivalence with the current Stages 8+9 is preserved.
- AC-006 Test added: synthetic upgrade scenario reaches green state via a single `make blueprint-upgrade-consumer-finalize` invocation without manual intervention.
- AC-007 Skill runbook (`SKILL.md`) references `make blueprint-upgrade-consumer-finalize` as the single canonical post-apply step.
- AC-008 Pipeline auto-clones URL form of `BLUEPRINT_UPGRADE_SOURCE` to a tmp dir before Stage 1b and the tmp dir is removed on pipeline exit.
- AC-009 Stage 1b (version pin diff) and Stage 5 (coverage fetch) succeed when `BLUEPRINT_UPGRADE_SOURCE` is a URL (currently they warn or fatal, respectively).
- AC-010 Local-path form of `BLUEPRINT_UPGRADE_SOURCE` continues to work without triggering auto-clone.
- AC-011 Test added: pipeline integration test demonstrates that the URL-form source path causes Stage 1b and Stage 5 to succeed.

## Informative Notes (Non-Normative)
- Context: both issues were identified during a real consumer upgrade (sbonoc/dhe-marketplace, v1.7.0 → v1.10.0, PR #62). The auto-clone issue caused a fatal Stage 5 failure; the finalize gap caused 5 sequential `quality-hooks-run` cycles with 15+ minutes of trial-and-error.
- Tradeoffs: Option A (finalize = quality tail only) means a standalone `make blueprint-upgrade-consumer-finalize` after an interrupted pipeline run will succeed only after Stages 3–7 have already run; this is an acceptable limitation documented in the usage block.
- Clarifications: none required.

## Explicit Exclusions
- Moving Stages 3–7 into the finalize target (Option B) — explicitly excluded by the option decision above.
- Adding new sync targets beyond the three defined in FR-006 — surfaces when a new sync target is added to `quality-sdd-sync-all` and the finalize script is updated as part of that work.
- Incremental tag-to-tag upgrade mode (Issue #168) — separate work item.
- Dry-run mode for the pipeline (Issue #167) — separate work item.
