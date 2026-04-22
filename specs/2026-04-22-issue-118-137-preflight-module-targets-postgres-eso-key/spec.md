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
- ADR path: docs/blueprint/architecture/decisions/ADR-20260422-issue-118-137-preflight-module-targets-postgres-eso-key.md
- ADR status: approved

## Applicable Guardrail Controls (Normative)
- Applicable control IDs: SDD-C-001, SDD-C-002, SDD-C-003, SDD-C-004, SDD-C-005, SDD-C-006, SDD-C-007, SDD-C-008, SDD-C-009, SDD-C-010, SDD-C-011, SDD-C-012, SDD-C-013, SDD-C-014, SDD-C-015, SDD-C-016, SDD-C-017, SDD-C-018, SDD-C-019, SDD-C-020, SDD-C-021
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
- Business outcome: Eliminate two silent contract drift hazards — stale make target references after module disable (#118) and wrong ESO key name in postgres module contract (#137) — so consumers and the tooling agree on actual behaviour at all times.
- Success metric: `make quality-sdd-check` passes; upgrade preflight warns on stale `infra-<module>-*` references; `module.contract.yaml` output key matches the ESO-produced secret key `POSTGRES_DB_NAME`.

## Normative Requirements

### Functional Requirements (Normative)
- FR-001 MUST correct `blueprint/modules/postgres/module.contract.yaml` `spec.outputs.produced` to list `POSTGRES_DB_NAME` instead of `POSTGRES_DB`, matching the key emitted by the postgres ExternalSecret and consumed by `scripts/lib/infra/postgres.sh`.
- FR-002 MUST add detection in `scripts/lib/blueprint/upgrade_consumer.py` that identifies consumer-owned files referencing `infra-<module>-*` make targets that are absent from `make/blueprint.generated.mk` because the module is disabled; the detection MUST surface each stale reference as a `RequiredManualAction` in the upgrade plan output.
- FR-003 MUST keep the stale-reference detection scoped to the consumer platform make surfaces and CI workflow files already covered by `BLUEPRINT_MAKE_TARGET_REFERENCE_PATHS` and `_collect_platform_make_paths`; it MUST NOT scan arbitrary files.
- FR-004 MUST gate stale-reference detection on the consumer repo being in generated-consumer mode (i.e. `contract.repository.repo_mode == consumer_init.mode_to`); in template-source mode all module targets are potentially valid.

### Non-Functional Requirements (Normative)
- NFR-SEC-001 MUST NOT introduce shell injection or path traversal; file reads remain in-process Python using `pathlib`.
- NFR-OBS-001 MUST surface each detected stale reference with the file path and target name in the `RequiredManualAction.reason` so the operator knows exactly what to clean up.
- NFR-REL-001 Detection failures (e.g. unreadable file) MUST NOT abort the upgrade plan; issues MUST be collected and surfaced, not raised as exceptions during plan generation.
- NFR-OPS-001 The postgres key fix MUST require no operator action beyond `make blueprint-upgrade-consumer` in downstream consumers; the output key rename in module contract docs is a metadata correction only.

## Normative Option Decision
- Option A: Correct `module.contract.yaml` in-place (one-line change, `POSTGRES_DB` → `POSTGRES_DB_NAME`) and add a new helper `_collect_stale_module_target_actions` in `upgrade_consumer.py` called from the existing plan assembly block.
- Option B: Generate the module outputs list from the ESO contract YAML at runtime so key names are always derived from a single source of truth.
- Selected option: OPTION_A
- Rationale: Option B would require significant new plumbing across the contract loading pipeline and introduce coupling between the ESO manifest and the module contract loader. The mismatch is a one-line typo; a direct correction with a regression test is the lowest-risk fix. For #118 a focused helper that mirrors the existing `_collect_missing_platform_make_target_actions` pattern integrates cleanly without architectural change.

## Contract Changes (Normative)
- Config/Env contract: `POSTGRES_DB_NAME` is the correct output key; no consumer-facing env change (it was already used correctly everywhere except the module contract doc).
- API contract: none
- Event contract: none
- Make/CLI contract: `make blueprint-upgrade-consumer` preflight output gains new `RequiredManualAction` entries for stale module target references.
- Docs contract: `blueprint/modules/postgres/module.contract.yaml` `outputs.produced` corrected.

## Blueprint Upstream Defect Escalation (Normative)
- Upstream issue URL: none
- Temporary workaround path: `should_skip_eso_contract_check()` in `reconcile_eso_runtime_secrets.sh` skips postgres ESO contract check in local-lite profile; this workaround is unrelated to the key name fix and remains in place for local-lite postgres runtime.
- Replacement trigger: none
- Workaround review date: none

## Normative Acceptance Criteria

### Issue #137 — Postgres ESO key mismatch
- AC-001 MUST: `blueprint/modules/postgres/module.contract.yaml` `spec.outputs.produced` contains `POSTGRES_DB_NAME` and does NOT contain `POSTGRES_DB` as a standalone entry.
- AC-002 MUST: A contract test asserts that the postgres module contract output key `POSTGRES_DB_NAME` matches the `secretKey` used in `infra/gitops/platform/base/security/runtime-external-secrets-core.yaml` for the `postgres-runtime-credentials` ExternalSecret data entry.

### Issue #118 — Stale module make target references
- AC-003 MUST: When a generated-consumer repo references `infra-<module>-*` targets in CI or make files but those targets are absent from `make/blueprint.generated.mk` (module disabled), `upgrade_consumer.py` plan output includes a `RequiredManualAction` for each stale reference.
- AC-004 MUST: In template-source mode (or when all referenced module targets are present in the generated makefile) no spurious stale-reference `RequiredManualAction` entries are emitted.
- AC-005 MUST: A unit test in `tests/blueprint/test_upgrade_consumer.py` validates AC-003 and AC-004 using the existing fixture-repo pattern.

## Informative Notes (Non-Normative)
- Context: `module.contract.yaml` `outputs.produced` is a documentation/governance field consumed by `contract_schema.py` for schema validation and summary generation. The ESO ExternalSecret at `infra/gitops/platform/base/security/runtime-external-secrets-core.yaml:166` uses `secretKey: POSTGRES_DB_NAME`; `scripts/lib/infra/postgres.sh` reads `POSTGRES_DB_NAME`. The mismatch is purely in the module contract metadata.
- Context: For #118, `render_makefile.sh:makefile_module_phony_suffix` gates each module's `.PHONY` entries and target blocks on `is_module_enabled`. When a module is disabled, its `infra-<module>-*` targets disappear from `make/blueprint.generated.mk`. A consumer that previously had the module enabled can retain CI steps or makefile recipes that invoke these targets, causing silent CI failures after the module is disabled.
- Tradeoffs: Scanning only the files already covered by `BLUEPRINT_MAKE_TARGET_REFERENCE_PATHS` and `_collect_platform_make_paths` keeps the detection surface bounded and avoids false positives from unrelated files that legitimately reference make targets as strings.
- Clarifications: The `should_skip_eso_contract_check()` workaround in `reconcile_eso_runtime_secrets.sh` is orthogonal to this fix and is not removed here.

## Explicit Exclusions
- Removing or modifying the `should_skip_eso_contract_check()` local-lite workaround is out of scope.
- Adding runtime enforcement of the module contract output key list (e.g. failing ESO reconcile when keys diverge) is out of scope; this spec covers metadata correction and preflight detection only.
- Scanning files beyond the existing make surface and CI reference paths for stale module target references is out of scope.
