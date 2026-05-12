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
- ADR path: docs/blueprint/architecture/decisions/ADR-issue-258-259-260-261-v110-engine-hotfix.md
- ADR status: approved

## Applicable Guardrail Controls (Normative)
- Applicable control IDs: SDD-C-001, SDD-C-002, SDD-C-003, SDD-C-004, SDD-C-005, SDD-C-006, SDD-C-008, SDD-C-009, SDD-C-010, SDD-C-011, SDD-C-012, SDD-C-016, SDD-C-017, SDD-C-019, SDD-C-020, SDD-C-021, SDD-C-024
- Control exception rationale:
  - SDD-C-007: Blueprint tooling layer (standalone Python scripts and YAML contract); no DDD/Clean Architecture layer separation applies.
  - SDD-C-013: No STACKIT managed services in scope.
  - SDD-C-014: CLI tooling scripts — no k8s runtime, Crossplane, ESO, ArgoCD, or Keycloak involvement.
  - SDD-C-015: No app delivery workflow or Make-target contract affected.
  - SDD-C-018: N/A — this work item IS the upstream blueprint fix; no consumer-side workaround tracking is needed here.
  - SDD-C-022: No HTTP routes, filters, or API endpoints touched.
  - SDD-C-023: No filter or payload-transform logic introduced.

## Implementation Stack Profile (Normative)
- Backend stack profile: python (pure Python 3 scripts and YAML; blueprint tooling only — no FastAPI or Pydantic runtime)
- Frontend stack profile: none
- Test automation profile: pytest (unit and regression tests only)
- Agent execution model: specialized-subagents-isolated-worktrees
- Managed service preference: explicit-consumer-exception
- Managed service exception rationale: blueprint tooling scripts and YAML contract only; no STACKIT managed services in scope
- Runtime profile: local-first-docker-desktop-kubernetes
- Local Kubernetes context policy: not-applicable-stackit-runtime
- Local provisioning stack: crossplane-plus-helm
- Runtime identity baseline: custom-approved-exception
- Local-first exception rationale: blueprint CLI scripts execute without k8s runtime; Crossplane/ESO/ArgoCD/Keycloak not involved in this tooling fix

## Objective
- Business outcome: Every consumer upgrading to v1.10.0 MUST be able to complete `make blueprint-upgrade-consumer` end-to-end without being blocked by false-positive contract coverage errors (#258), false-positive behavioral check failures (#259), spurious postcheck validation failures for generated-consumer repos (#260), or false-positive fresh-env-gate divergences caused by absolute paths in artifacts (#261). Closes issues #258, #259, #260, #261.
- Success metric: A generated-consumer repo upgrading from any prior version to v1.10.0 MUST pass all four pipeline gates — apply (Stage 2), validate (#260 fix), postcheck (#259 fix), and fresh-env-gate (#261 fix) — without any consumer-side workarounds.

## Normative Requirements

### Functional Requirements (Normative)
- FR-001 `blueprint/contract.yaml` MUST classify `pyproject.toml` and `uv.lock` under `init_managed`, and MUST classify `infra/local/helm/opensearch/values.yaml` and `infra/local/helm/kms/values.yaml` under `conditional_scaffold`, so that `audit_source_tree_coverage` reports `uncovered_source_files_count=0` for the v1.10.0 source tree.
- FR-002 `scripts/lib/blueprint/upgrade_consumer_validate.py` MUST filter `blueprint-template-smoke` from `VALIDATION_TARGETS` when `contract.repository.repo_mode` equals the generated-consumer mode value (`generated-consumer`), mirroring the skip logic already applied by the `quality-hooks-strict` runner.
- FR-003 `scripts/lib/blueprint/upgrade_fresh_env_gate.py` MUST add `upgrade_validate.json` and `required_files_status.json` to `_VOLATILE_ARTIFACT_NAMES` so that checksum divergences caused by absolute repository paths embedded in those artifact files are excluded from the fresh-env gate comparison.
- FR-004 `scripts/lib/blueprint/upgrade_shell_behavioral_check.py` MUST resolve function definitions from the full transitive source chain of each blueprint-managed script under analysis — not capped at depth 1 — with cycle detection to prevent infinite recursion, and MUST NOT flag bare shell command tokens (tokens that are not prefixed by `function` or followed by `()` in any reachable source file, e.g. `uv`, `validate`) as unresolved symbols, so that `make blueprint-upgrade-consumer-postcheck` reports zero false-positive failures for v1.10.0 blueprint-managed scripts.

### Non-Functional Requirements (Normative)
- NFR-SEC-001 N/A — these are internal blueprint tooling fixes with no authentication, authorization, or secret handling in scope; no security properties change.
- NFR-OBS-001 All four fixes MUST preserve the existing JSON artifact schemas (field names, types, and nesting structure) of `upgrade_validate.json`, `required_files_status.json`, `fresh_env_gate.json`, and behavioral check output; no breaking schema changes are permitted.
- NFR-REL-001 Each fix MUST be independently backward-compatible: consumers with a working upgrade flow against any prior blueprint version MUST NOT be broken by any of the four changes.
- NFR-OPS-001 All regression tests added by this work item MUST be runnable via `uv run python3 -m pytest` without requiring a live k8s cluster or external network access.

## Normative Option Decision
- Option A (transitive resolver + bare-command suppression for FR-004): replace the depth-1 source collection in `upgrade_shell_behavioral_check.py` with a fully transitive BFS traversal (with a visited-paths cycle guard); additionally identify and suppress bare shell command tokens that do not appear as function definitions in any reachable source file.
- Option B (contract default exclusion list for FR-004): ship a default `extra_excluded_tokens` list in the source `blueprint/contract.yaml` under `spec.upgrade.behavioral_check` covering all 29 known false-positive symbols; no resolver code change required.
- Selected option: OPTION_A
- Rationale: Option A fixes the root cause structurally. The depth-1 cap is a simplification that breaks for any script whose dependencies span more than one hop, and will silently recur for any future blueprint function added transitively. Option B is a data patch that requires manual maintenance of the exclusion list every time a new transitive symbol appears, creating ongoing drift risk. Option A also handles bare command tokens (`uv`, `validate`) categorically rather than enumerating each command by name, which Option B cannot do without encoding all OS commands. Cycle detection is mandatory and ensures correctness in pathological source graphs.

## Contract Changes (Normative)
- Config/Env contract: none
- API contract: none
- OpenAPI / Pact contract path: none
- Event contract: none
- Make/CLI contract: no new Make targets; behavior of `blueprint-upgrade-consumer`, `blueprint-upgrade-consumer-validate`, `blueprint-upgrade-consumer-postcheck`, and `blueprint-upgrade-fresh-env-gate` improves (false-positive errors removed for v1.10.0 consumers)
- Docs contract: none

## Blueprint Upstream Defect Escalation (Normative)
- Upstream issue URL: https://github.com/sbonoc/stackit-platform-blueprint/issues/258, https://github.com/sbonoc/stackit-platform-blueprint/issues/259, https://github.com/sbonoc/stackit-platform-blueprint/issues/260, https://github.com/sbonoc/stackit-platform-blueprint/issues/261
- Temporary workaround path: consumer `blueprint/contract.yaml` — add 4 file entries to consumer contract (#258); add 29 tokens to `spec.upgrade.behavioral_check.extra_excluded_tokens` (#259); patch `_VOLATILE_ARTIFACT_NAMES` locally (#261); patch `scripts/lib/blueprint/upgrade_consumer_validate.py` locally (#260)
- Replacement trigger: this PR merged to main and released; consumers MUST remove workarounds after adopting the patched blueprint version
- Workaround review date: 2026-08-12

## Normative Acceptance Criteria
- AC-001 Given a clean v1.10.0 blueprint source tree, `audit_source_tree_coverage` MUST report `uncovered_source_files_count=0` with no `BLOCKED` status, and the upgrade plan stage MUST produce a valid plan without aborting.
- AC-002 Given a generated-consumer repo upgrading against v1.10.0, `make blueprint-upgrade-consumer-validate` MUST NOT list `blueprint-template-smoke` as a failed target and MUST NOT propagate a validate-status-failure to `make blueprint-upgrade-consumer-postcheck` due to this target.
- AC-003 Given a generated-consumer repo where the working tree and a clean fresh-env worktree produce equivalent pipeline behavior but differ only in absolute paths embedded in `upgrade_validate.json` and `required_files_status.json`, `make blueprint-upgrade-fresh-env-gate` MUST report status `pass`.
- AC-004 Given a generated-consumer repo upgrading against v1.10.0, `make blueprint-upgrade-consumer-postcheck` MUST report `behavioral_check_failures_total=0` for all blueprint-managed scripts whose only unresolved tokens are functions defined in transitive sources or bare shell command tokens.

## Informative Notes (Non-Normative)
- Context: All four defects were discovered during the dhe-marketplace consumer upgrade from v1.7.0 to v1.10.0 (PR sbonoc/dhe-marketplace#62). Each was independently filed as a separate upstream issue and has a known consumer-side workaround currently in place. This work item fixes all four at the blueprint source so the next release removes the need for consumer workarounds.
- Tradeoffs: FR-004 (Option A) adds transitive source resolution complexity and requires a visited-set cycle guard. The performance cost for a one-time postcheck operation on a repository of this scale is negligible. The depth-1 resolver is preserved as a lower-level building block; the BFS layer composes on top of it.
- Clarifications: The `conditional_scaffold` classification for the two helm values files mirrors the existing pattern for postgres, rabbitmq, and object-storage module values files already declared in `blueprint/contract.yaml`. The `init_managed` classification for `pyproject.toml` and `uv.lock` reflects that these files are managed at blueprint init time and owned by the blueprint, not seeded to consumers.

## Explicit Exclusions
- Consumer workaround removal is out of scope — consumers must remove their own workarounds after adopting the fixed blueprint version; this work item does not touch any consumer repository.
- Path normalization inside `upgrade_validate.json` and `required_files_status.json` artifact writers is out of scope — the volatile-set approach for #261 is the minimal correct fix.
- Extending behavioral check depth beyond full transitive resolution (e.g. adding semantic analysis of variables or eval expressions) is out of scope.
- Changes to the pipeline shell wrapper scripts (`upgrade_consumer_pipeline.sh`, `upgrade_consumer.sh`) are out of scope for this hotfix.
