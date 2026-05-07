# Specification — Generalize Consumer-Seeded Feature Gates

## Spec Readiness Gate (Blocking)
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
- ADR path: docs/blueprint/architecture/decisions/ADR-2026-05-07-generalize-consumer-seeded-feature-gates.md
- ADR status: approved

## Applicable Guardrail Controls (Normative)
- Applicable control IDs: SDD-C-001, SDD-C-002, SDD-C-003, SDD-C-004, SDD-C-005, SDD-C-006, SDD-C-007, SDD-C-008, SDD-C-011, SDD-C-012, SDD-C-016, SDD-C-017, SDD-C-019, SDD-C-020, SDD-C-021
- Control exception rationale:
  - SDD-C-009 (security/authn/authz): not applicable — no runtime authn or secret handling; env vars gate init-time behavior only, not a security boundary
  - SDD-C-010 (observability): not applicable — no operated runtime paths; init script only
  - SDD-C-013 (managed-service-first): not applicable — no STACKIT runtime resources
  - SDD-C-014 (local-first baseline): not applicable — no local Kubernetes runtime involved
  - SDD-C-015 (app onboarding Make targets): not applicable — no app delivery scope affected
  - SDD-C-018 (blueprint-defect escalation): not applicable — this IS blueprint source work
  - SDD-C-022 (HTTP smoke gate): not applicable — no HTTP routes
  - SDD-C-023 (filter/transform coverage): not applicable — no filter or payload-transform logic
  - SDD-C-024 (reproducible-finding translation): not applicable — no pre-existing smoke failures

## Implementation Stack Profile (Normative)
- Backend stack profile: blueprint-maintainer-python
- Frontend stack profile: none
- Test automation profile: pytest
- Agent execution model: single-agent
- Managed service preference: explicit-consumer-exception
- Managed service exception rationale: blueprint-maintainer tooling work only; no STACKIT runtime resources involved
- Runtime profile: local-first-docker-desktop-kubernetes
- Local Kubernetes context policy: docker-desktop-preferred
- Local provisioning stack: crossplane-plus-helm
- Runtime identity baseline: eso-plus-argocd-plus-keycloak
- Local-first exception rationale: none — no local runtime scope; profile declared for contract compliance only

## Objective
- Business outcome: Consumers can opt in to the Claude AI GH Actions workflows at `make blueprint-init-repo` time via an env var flag; existing consumers that missed the init-time flag can adopt any feature gate later via a single targeted Make target without re-seeding the full consumer-owned set; future optional seeded files follow the same generic gate contract instead of requiring new bespoke resolvers.
- Success metric: `CLAUDE_AI_ENABLED=false make blueprint-init-repo` produces no Claude workflow files; `CLAUDE_AI_ENABLED=true make blueprint-init-repo` produces both; an existing consumer runs `make blueprint-seed-feature FEATURE=claude_ai_integration` and gets the files from the pinned blueprint ref without touching any other consumer-owned file; a second gate entry works without any Python code change.

## Normative Requirements

### Functional Requirements (Normative)

- REQ-001: `blueprint/contract.yaml` MUST declare a top-level `consumer_seeded_feature_gates` list. Each list entry MUST contain exactly: `id` (string, unique across all entries), `enable_flag` (string, references an existing entry in `spec.toggles`), `enabled_by_default` (boolean, MUST be `false`), `description` (non-empty string), and `consumer_seeded_paths_when_enabled` (non-empty list of strings, each path MUST also appear in `consumer_seeded_paths`).

- REQ-002: `scripts/lib/blueprint/init_repo_contract.py` MUST export a function `resolve_consumer_seeded_feature_gates(repo_root: Path) -> list[tuple[str, bool, list[str]]]` that reads the `consumer_seeded_feature_gates` list from the contract and returns one tuple per gate: `(id, enabled, paths)`. The `enabled` value MUST be resolved by reading the env var named by `enable_flag`; if the env var is absent, `enabled_by_default` MUST be used.

- REQ-003: `seed_consumer_owned_files` in `scripts/lib/blueprint/init_repo_contract.py` MUST call `resolve_consumer_seeded_feature_gates` after the normal `consumer_seeded_paths` seeding pass and MUST call `remove_path` for every path belonging to a disabled gate.

- REQ-004: The `claude_ai_integration` gate MUST be the first entry in `consumer_seeded_feature_gates` with `enable_flag: CLAUDE_AI_ENABLED`, `enabled_by_default: false`, and `consumer_seeded_paths_when_enabled` listing `.github/workflows/claude.yml` and `.github/workflows/claude-code-review.yml`.

- REQ-005: Both Claude workflow paths MUST appear in `consumer_seeded_paths` and in `required_files` within `blueprint/contract.yaml`.

- REQ-006: Template files `scripts/templates/consumer/init/.github/workflows/claude.yml.tmpl` and `scripts/templates/consumer/init/.github/workflows/claude-code-review.yml.tmpl` MUST exist and MUST contain the workflow content from the PR #252 branch (`add-claude-github-actions-1778138840576`) at the point this work item merges.

- REQ-007: `scripts/bin/blueprint/validate_contract.py` MUST include a `_validate_consumer_seeded_feature_gates` function that: (a) requires the `consumer_seeded_feature_gates` key to be present in the contract YAML, (b) requires each entry to have all mandatory fields with correct types, (c) requires `enabled_by_default` to be `false` for every entry, (d) requires `enable_flag` to reference an existing key in `spec.toggles`, (e) requires `consumer_seeded_paths_when_enabled` to be non-empty, and (f) requires every path in `consumer_seeded_paths_when_enabled` to also appear in `consumer_seeded_paths`.

- REQ-008: The `_validate_consumer_seeded_feature_gates` function MUST be called from the top-level `_validate_contract` orchestrator in `validate_contract.py`.

- REQ-009: A `blueprint-seed-feature` Make target MUST be available in consumer repos (propagated via the blueprint-managed Makefile layer). It MUST accept a mandatory `FEATURE=<gate-id>` parameter. When invoked, it MUST: (a) read `BLUEPRINT_UPGRADE_REF` from `blueprint/repo.init.env`, (b) fetch the blueprint source at that ref into a temporary directory using the same cloning mechanism as `make blueprint-upgrade-consumer`, (c) locate the gate entry matching `FEATURE` in the fetched blueprint source's `consumer_seeded_feature_gates` list, (d) render each path in `consumer_seeded_paths_when_enabled` from the fetched source's template files, and (e) write the rendered files to the consumer repo. The target MUST NOT touch any consumer-seeded path not listed in the matching gate's `consumer_seeded_paths_when_enabled`.

- REQ-010: `make blueprint-seed-feature` MUST exit non-zero with a clear diagnostic message when `FEATURE` is not provided or when the provided gate ID does not exist in the fetched blueprint source's `consumer_seeded_feature_gates` list.

- REQ-011: `make blueprint-seed-feature` MUST be idempotent: running it twice with the same `FEATURE` MUST produce the same file contents and MUST NOT error on the second run.

- REQ-012: A `scripts/bin/blueprint/feature_gate_status.py` script MUST exist and a `blueprint-feature-gate-status` Make target MUST be available in consumer repos. When invoked, the script MUST: (a) read the `consumer_seeded_feature_gates` list from the consumer's `blueprint/contract.yaml`, (b) for each gate determine adoption status — a gate is adopted if the `enable_flag` env var is truthy in `blueprint/repo.init.env` OR at least one path in `consumer_seeded_paths_when_enabled` physically exists in the consumer repo, (c) for unadopted gates, upsert a backlog entry in `AGENTS.backlog.md` with gate id, seed command, and description, (d) for adopted gates with an existing backlog entry, mark that entry `[x]`. The script MUST exit 0 always (informational tool, not a gate).

- REQ-013: Backlog entries written by `feature_gate_status.py` MUST use the format: `- [ ] (blueprint-feature) seed: <gate_id>` followed by indented `command:` and `description:` lines. The `command:` value MUST use the source URL from `BLUEPRINT_UPGRADE_SOURCE` env var or `blueprint/repo.init.env` if available, else the literal placeholder `<BLUEPRINT_UPGRADE_SOURCE>`. Entries MUST be idempotent — running the script twice MUST NOT produce duplicate entries.

- REQ-014: `upgrade_consumer_postcheck.sh` MUST call `feature_gate_status.py` after the `emit_postcheck_report_metrics` step and before the final exit. The call MUST be non-blocking (exit code NOT propagated to the postcheck result); the script is informational only.

- REQ-015: The `.agents/skills/blueprint-consumer-upgrade/SKILL.md` runbook MUST be updated to describe the `blueprint-feature-gate-status` target, explain the `AGENTS.backlog.md` backlog entry format, and instruct the agent to run `make blueprint-seed-feature FEATURE=<id>` for each unadopted feature gate entry it finds after an upgrade.

### Non-Functional Requirements (Normative)

- NFR-001: The `app_catalog_scaffold_contract` section and its validation logic MUST remain unchanged. The new mechanism MUST NOT alter any existing behavior of `resolve_app_catalog_scaffold_contract` or its callers.

- NFR-002: A consumer repo that was initialized before this change MUST NOT be affected by a blueprint upgrade that includes this change, because the Claude workflow paths are in `consumer_seeded` and the upgrade engine hard-skips them.

- NFR-003: Test line coverage for `resolve_consumer_seeded_feature_gates` and the gate-pruning branch in `seed_consumer_owned_files` MUST be 100%.

- NFR-004: The `make quality-hooks-run` and `make infra-validate` bundles MUST both pass after implementation.

- NFR-005: `make blueprint-seed-feature` MUST use the consumer's pinned `BLUEPRINT_UPGRADE_REF` exclusively. It MUST NOT accept a ref override parameter; the pinned ref is the only authorised source to prevent version skew between seeded files and the consumer's installed blueprint machinery.

## Contract Changes (Normative)
- Config/Env contract: new env var `CLAUDE_AI_ENABLED` (boolean, default false) read at `make blueprint-init-repo` time; no runtime env change
- API contract: none
- OpenAPI / Pact contract path: none
- Event contract: none
- Make/CLI contract: new `blueprint-seed-feature` Make target in consumer repos (propagated via blueprint-managed Makefile layer); mandatory parameter `FEATURE=<gate-id>`; existing `make blueprint-init-repo` behavior extended with gate-pruning step; new `blueprint-feature-gate-status` Make target (no parameters, informational, always exits 0)
- Docs contract: `blueprint/contract.yaml` schema extended; blueprint consumer docs MUST document the new flag in the init guide

## Blueprint Upstream Defect Escalation (Normative)
- Upstream issue URL: none
- Temporary workaround path: none
- Replacement trigger: none
- Workaround review date: none

## Normative Acceptance Criteria

- AC-001: Running `CLAUDE_AI_ENABLED=false make blueprint-init-repo` (or running without the env var) MUST NOT produce `.github/workflows/claude.yml` or `.github/workflows/claude-code-review.yml` in the consumer repo.

- AC-002: Running `CLAUDE_AI_ENABLED=true make blueprint-init-repo` MUST produce both `.github/workflows/claude.yml` and `.github/workflows/claude-code-review.yml` in the consumer repo, with content rendered from their respective `.tmpl` files.

- AC-003: When `make blueprint-upgrade-consumer` runs against any consumer repo, the upgrade engine MUST classify `.github/workflows/claude.yml` and `.github/workflows/claude-code-review.yml` as `consumer-seeded / skip` and MUST NOT create, modify, or delete those files during any upgrade pass, regardless of whether the files are physically present in the consumer repo.

- AC-004: `validate_contract.py` MUST reject a `blueprint/contract.yaml` where any `consumer_seeded_feature_gates` entry is missing a mandatory field, has `enabled_by_default: true`, references a non-existent toggle, or lists a path not in `consumer_seeded_paths`.

- AC-005: Adding a second gate entry to `consumer_seeded_feature_gates` in YAML with its template files and `consumer_seeded_paths` entries MUST work without any Python code change beyond the contract YAML and templates.

- AC-006: All pre-existing tests for `app_catalog_scaffold_contract` MUST continue to pass unchanged.

- AC-007: Running `make blueprint-seed-feature FEATURE=claude_ai_integration` in a consumer repo MUST write both `.github/workflows/claude.yml` and `.github/workflows/claude-code-review.yml` using templates from the blueprint source at the consumer's pinned `BLUEPRINT_UPGRADE_REF`, without modifying any other file in the consumer repo.

- AC-008: Running `make blueprint-seed-feature FEATURE=nonexistent` MUST exit non-zero and print a diagnostic identifying the unknown gate ID.

- AC-009: Running `make blueprint-seed-feature FEATURE=claude_ai_integration` twice in sequence MUST produce identical file contents on both runs and MUST exit zero on the second run.

- AC-010: Running `make blueprint-feature-gate-status` in a consumer repo with no adopted gates MUST produce an `AGENTS.backlog.md` entry for each unadopted gate with the correct format (gate id, command, description). The script MUST exit 0.

- AC-011: Running `make blueprint-feature-gate-status` twice in sequence MUST NOT produce duplicate backlog entries.

- AC-012: When a gate is adopted (enable_flag truthy in `blueprint/repo.init.env` or gate paths present), running `make blueprint-feature-gate-status` MUST mark that gate's backlog entry `[x]` if an open entry exists, and MUST NOT add a new open entry.

- AC-013: `make blueprint-upgrade-consumer-postcheck` MUST call the feature gate status check as a non-blocking informational step; postcheck result MUST NOT be affected by the gate status output.

## Informative Notes (Non-Normative)

- The seeding order is: (1) unconditionally seed all `consumer_seeded_paths` from templates, (2) resolve all `consumer_seeded_feature_gates`, (3) prune paths of disabled gates. This means the template files for gated paths MUST exist in `scripts/templates/consumer/init/`, even though the files are pruned immediately after when the gate is disabled.
- `enabled_by_default: false` is mandatory for all gates to ensure consumers explicitly opt in. A gate with `enabled_by_default: true` would change the current behavior of `make blueprint-init-repo` for all consumers without notice.
- The Claude workflow templates contain no consumer-specific tokens; the `{{...}}` substitution pass runs on them but produces no changes. They are kept as `.tmpl` files for consistency with the init engine's template-loading contract. A future gate entry that does require token substitution follows the same pattern without code change.

## Explicit Exclusions
- Migration of `app_catalog_scaffold_contract` into the new `consumer_seeded_feature_gates` list: excluded. app_catalog gates `feature_gated` paths (not `consumer_seeded`) and has domain-specific manifest-marker and test-lane validation with no generic counterpart.
- Upgrade-time delivery of gated consumer-seeded files to existing consumers: excluded. Consumer-seeded files are permanently upgrade-skipped by contract.
- Ref override on `blueprint-seed-feature`: excluded. The target MUST use the consumer's pinned `BLUEPRINT_UPGRADE_REF` only; consumers who want files from a newer blueprint version MUST run `make blueprint-upgrade-consumer` first.
- `make blueprint-seed-feature` support for seeding multiple gates in one invocation: excluded. Each call targets exactly one gate ID; consumers requiring multiple gates run the target once per gate.
- `blueprint-feature-gate-status` reading from the blueprint source repository: excluded. Gate metadata (id, description, command) is read from the consumer's local `blueprint/contract.yaml`, which is always present. The source URL placeholder is used when source is not available rather than failing.
