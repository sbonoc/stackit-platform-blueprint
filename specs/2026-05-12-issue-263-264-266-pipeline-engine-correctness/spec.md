# Specification

## Spec Readiness Gate (Blocking)
<!-- SPEC_PRODUCT_READY=true: intake gate — Product sign-off only; unlocks agent ADR drafting.
     SPEC_READY=true: implementation gate — all sign-offs required; unlocks coding. -->
- SPEC_READY: false
- SPEC_PRODUCT_READY: false
- Open questions count: 0
- Unresolved alternatives count: 0
- Unresolved TODO markers count: 0
- Pending assumptions count: 0
- Open clarification markers count: 0
- Product sign-off: pending
- Architecture sign-off: pending
- Security sign-off: pending
- Operations sign-off: pending
- ADR path: docs/blueprint/architecture/decisions/ADR-issue-263-264-266-pipeline-engine-correctness.md
- ADR status: proposed

## Applicable Guardrail Controls (Normative)
- Applicable control IDs: SDD-C-002, SDD-C-003, SDD-C-004, SDD-C-005, SDD-C-006, SDD-C-007, SDD-C-008, SDD-C-009, SDD-C-010, SDD-C-011, SDD-C-012, SDD-C-016, SDD-C-017, SDD-C-019, SDD-C-020, SDD-C-021, SDD-C-024
- Control exception rationale:
  - SDD-C-001: no missing inputs; all requirements are fully derivable from issue evidence.
  - SDD-C-013: blueprint-internal tooling; no STACKIT managed service decision required.
  - SDD-C-014: no infra/runtime scope; exception: pure Python + Bash scripts change.
  - SDD-C-015: no app delivery impact; app onboarding contract unchanged.
  - SDD-C-018: this IS the upstream fix; no consumer-side workaround escalation required.
  - SDD-C-022: no HTTP route handlers or API endpoints touched.
  - SDD-C-023: no filter or payload-transform logic.

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
- Business outcome: the 10-stage scripted upgrade pipeline reaches and executes Stages 3–10 when Stage 2 produces conflicts; consumers no longer accumulate multi-release diff debt from wrong baselines; `make blueprint-upgrade-consumer` applies by default.
- Success metric: a real or simulated multi-version upgrade (v1.0.0 → v1.8.3 → v1.10.0) produces ≤10 conflicts on the second hop (currently 88); pipeline completes through Stage 10 when Stage 2 has conflicts; first pipeline invocation without BLUEPRINT_UPGRADE_APPLY=true mutates files.

## Normative Requirements

### Functional Requirements (Normative)
- FR-001 The upgrade engine (`upgrade_consumer.py`) MUST resolve the 3-way merge baseline ref from `spec.repository.template_bootstrap.last_applied_version` when that field is present and non-empty in the consumer's `blueprint/contract.yaml`; it MUST fall back to `template_version` only when `last_applied_version` is absent or empty. The same preference MUST be applied in `upgrade_version_pin_diff.py`.
- FR-002 The postcheck script (`upgrade_consumer_postcheck.py`) MUST write `last_applied_version` to `blueprint/contract.yaml` after a successful postcheck (status == "success"), setting the field to the `upgrade_ref` value recorded in `artifacts/blueprint/upgrade_apply.json`; it MUST NOT write the field when postcheck status is anything other than "success".
- FR-003 The upgrade pipeline (`upgrade_consumer_pipeline.sh`) MUST proceed to Stage 3 when Stage 2 exits and `artifacts/blueprint/upgrade_apply.json` contains `status == "conflicts"`; it MUST abort and set `pipeline_exit` when Stage 2 exits non-zero AND the artifact status is not "conflicts". The engine (`upgrade_consumer.py`) MUST exit 0 when apply completes with conflicts and MUST set `apply_payload["status"] = "conflicts"` in the artifact; it MUST exit non-zero only for true engine errors (contract load failure, clone failure, write errors, merge markers).
- FR-004 The upgrade pipeline (`upgrade_consumer_pipeline.sh`) MUST default `BLUEPRINT_UPGRADE_APPLY` to `true` via `set_default_env`; it MUST propagate the resolved value explicitly to the Stage 2 make invocation; it MUST emit a `[PIPELINE]` banner warning before Stage 2 when `BLUEPRINT_UPGRADE_APPLY=false` is explicitly set. The standalone `upgrade_consumer.sh` script MUST retain its existing default of `false` for backward compatibility with direct callers.

### Non-Functional Requirements (Normative)
- NFR-SEC-001 The `last_applied_version` field MUST contain only the semver upgrade ref string (e.g. `1.10.0` or `v1.10.0`); no credential, secret, or path information MUST be written to the field or any new log line.
- NFR-OBS-001 The pipeline Stage 2 completion log line MUST include `status=<value>` derived from `upgrade_apply.json` so operators can distinguish "conflicts" from "success" in log tailing. The engine MUST emit `blueprint_upgrade_apply_status_total status=conflicts` metric when apply exits with conflicts.
- NFR-REL-001 The `last_applied_version` bump MUST be performed atomically by the postcheck script only after a fully-successful postcheck; an incomplete or half-applied upgrade MUST NOT advance the baseline. Existing consumers whose `blueprint/contract.yaml` lacks the `last_applied_version` field MUST continue to resolve the baseline from `template_version` until their next successful postcheck writes the field.
- NFR-OPS-001 The pipeline script usage block MUST document that `BLUEPRINT_UPGRADE_APPLY` defaults to `true` in pipeline context. The `.agents/skills/blueprint-consumer-upgrade/SKILL.md` runbook MUST be updated to reflect that `make blueprint-upgrade-consumer` applies by default and that plan-only requires `BLUEPRINT_UPGRADE_APPLY=false`.
- NFR-A11Y-001 N/A — no UI or user-facing web surface is introduced or modified.

## Normative Option Decision
- Option A: Engine exits 0 when apply completes with conflicts; sets `status = "conflicts"` in artifact; pipeline reads artifact status to discriminate conflicts from errors. (Selected)
- Option B: Engine retains exit 1 for conflicts; pipeline reads artifact status first and ignores make exit code when artifact status is "conflicts".
- Selected option: OPTION_A
- Rationale: Option A produces correct Unix exit-code semantics — the engine completed its task successfully (write files + record conflicts); non-zero exit is reserved for failure. Option B still requires reading the artifact and would need the "conflicts" status value regardless, making the distinction purely cosmetic with more complex pipeline logic. Both options were proposed in issue #264; Option A is the recommended pick.

## Contract Changes (Normative)
- Config/Env contract: `BLUEPRINT_UPGRADE_APPLY` default changes from `false` to `true` in pipeline context (`upgrade_consumer_pipeline.sh`) only; standalone `upgrade_consumer.sh` retains `false`.
- API contract: none
- OpenAPI / Pact contract path: none
- Event contract: none
- Make/CLI contract: `make blueprint-upgrade-consumer` now applies by default (breaking change for callers who relied on plan-only default; banner and docs mitigate); `blueprint/contract.yaml` gains optional field `last_applied_version` under `template_bootstrap`; `artifacts/blueprint/upgrade_apply.json` schema gains `"conflicts"` as a valid `status` enum value.
- Docs contract: `.agents/skills/blueprint-consumer-upgrade/SKILL.md` updated to reflect apply-by-default behaviour.

## Blueprint Upstream Defect Escalation (Normative)
- Upstream issue URL: none — this work item IS the blueprint fix for issues #263, #264, #266.
- Temporary workaround path: none
- Replacement trigger: none
- Workaround review date: none

## Normative Acceptance Criteria
- AC-001 MUST: calling `_resolve_baseline_ref` with a source repo and a contract where `last_applied_version = "1.8.3"` MUST return the resolved ref for `v1.8.3` or `1.8.3` (whichever exists as a git tag), ignoring `template_version`.
- AC-002 MUST: calling `_resolve_baseline_ref` with a contract where `last_applied_version` is absent or empty MUST fall back to resolving `template_version` (migration compatibility for existing consumers).
- AC-003 MUST: after a successful postcheck invocation against an apply artifact containing `upgrade_ref = "v1.10.0"`, `blueprint/contract.yaml` MUST contain `last_applied_version: 1.10.0` (or `v1.10.0` per tag form) under `template_bootstrap`.
- AC-004 MUST: when Stage 2 exits and `upgrade_apply.json` has `status == "conflicts"`, the pipeline MUST log "Stage 2: complete" and proceed to Stage 3 without setting `pipeline_exit`.
- AC-005 MUST: when Stage 2 exits non-zero and `upgrade_apply.json` has `status != "conflicts"` (or artifact is absent), the pipeline MUST call `log_fatal` and abort (pipeline_exit set).
- AC-006 MUST: running `make blueprint-upgrade-consumer` with no `BLUEPRINT_UPGRADE_APPLY` environment variable set MUST result in `blueprint_upgrade_apply_enabled value=true` in the output log (apply mode active by default).
- AC-007 MUST: when `BLUEPRINT_UPGRADE_APPLY=false` is explicitly set in the environment before invoking the pipeline, the pipeline MUST emit a `[PIPELINE]` banner before Stage 2 informing the operator that the run will plan-only without mutations.

## Informative Notes (Non-Normative)
- Context: all three bugs were confirmed in a real consumer upgrade (sbonoc/dhe-marketplace, v1.7.0 → v1.10.0, PR #62) producing 88 conflicts from wrong baseline and causing the pipeline to abort at Stage 2 every time conflicts were present. The agent then had to manually invoke Stages 3, 5, 6, 8, 9. BLUEPRINT_UPGRADE_APPLY=false caused an additional ~5 minute waste.
- Tradeoffs: Option A (engine exits 0 for conflicts) is a minor change to engine semantics that affects existing callers who check `make blueprint-upgrade-consumer-apply` exit code directly. The `upgrade_apply.json` artifact was already the canonical result carrier; relying on it rather than the exit code is more robust across GNU make version differences.
- Clarifications: `last_applied_version` is written verbatim from `upgrade_ref` in the apply artifact (typically `v1.10.0`). The reader MUST try both `v{version}` and `{version}` as tag candidates (existing `_resolve_baseline_ref` logic already does this).

## Explicit Exclusions
- Conflict auto-resolution triage manifest (Issues #265 + #271): deferred to its own work item.
- `upgrade_consumer_pipeline.sh` `blueprint-upgrade-consumer-finalize` target (Issue #267): deferred.
- Source auto-clone from URL (Issue #269): deferred.
- Test ownership contract (Issue #270): deferred.
- Issue #183 (stale reconcile report detection): surfaced as backlog proposal; not incorporated into this work item scope.
