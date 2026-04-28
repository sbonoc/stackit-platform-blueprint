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
- ADR path: docs/blueprint/architecture/decisions/ADR-2026-04-28-issue-230-init-descriptor-kustomization-sync.md
- ADR status: approved

## Applicable Guardrail Controls (Normative)
- Applicable control IDs: SDD-C-002, SDD-C-003, SDD-C-004, SDD-C-005, SDD-C-006, SDD-C-008, SDD-C-009, SDD-C-010, SDD-C-011, SDD-C-012, SDD-C-016, SDD-C-017, SDD-C-019, SDD-C-020, SDD-C-021, SDD-C-023, SDD-C-024
- Control exception rationale: none

## Implementation Stack Profile (Normative)
- Backend stack profile: explicit-consumer-exception
- Frontend stack profile: not-applicable-stackit-runtime
- Test automation profile: explicit-consumer-exception
- Agent execution model: specialized-subagents-isolated-worktrees
- Managed service preference: explicit-consumer-exception
- Managed service exception rationale: blueprint source tooling only — no managed service involved
- Runtime profile: local-first-docker-desktop-kubernetes
- Local Kubernetes context policy: docker-desktop-preferred
- Local provisioning stack: crossplane-plus-helm
- Runtime identity baseline: custom-approved-exception
- Local-first exception rationale: blueprint tooling change — no runtime deployment

## Objective
- Business outcome: blueprint v1.8.2 (or v1.8.1 follow-up patch) restores `make blueprint-template-smoke` and the consumer postcheck/fresh-env-gate for every consumer upgrading from v1.8.0 by ensuring `apps/descriptor.yaml` and `infra/gitops/platform/base/apps/kustomization.yaml` remain in lockstep across the `blueprint-init-repo` → `infra-bootstrap` → `infra-validate` sequence.
- Success metric: in any generated-consumer repo at v1.8.0 with arbitrary consumer apps in `infra/gitops/platform/base/apps/kustomization.yaml`, running `BLUEPRINT_UPGRADE_REF=<this-version> make blueprint-upgrade-consumer && make blueprint-upgrade-consumer-postcheck` exits 0 with no `[infra-validate]` `manifest filename not listed` errors; `make quality-ci-generated-consumer-smoke` and `make blueprint-template-smoke` exit 0 in CI.

## Normative Requirements

### Functional Requirements (Normative)
- FR-001 The `blueprint-init-repo` flow MUST guarantee that, after a force-init reseed, the on-disk `apps/descriptor.yaml` and `infra/gitops/platform/base/apps/kustomization.yaml` reference EXACTLY the same set of manifest filenames such that `validate_app_descriptor` → `verify_kustomization_membership` returns no errors.
- FR-002 The `blueprint-init-repo` flow MUST NOT leave the consumer in a state where one half of the descriptor↔kustomization pair is force-reseeded from a blueprint template while the other half is preserved from prior consumer state, unless the post-reseed pair is provably membership-consistent (descriptor manifest filenames ⊆ kustomization resources).
- FR-003 The `blueprint-template-smoke` flow MUST exercise the v1.8.0 → current upgrade scenario against a generated consumer repo whose `infra/gitops/platform/base/apps/kustomization.yaml` lists app manifests that DIFFER from the blueprint init descriptor template, and MUST exit 0 (i.e. the chosen FR-001/FR-002 fix MUST be exercised by smoke, not only by source-mode self-test).
- FR-004 The CI lane `quality-ci-generated-consumer-smoke` MUST exit 0 against the canonical generated-consumer fixture after this work item ships, restoring the `blueprint-upgrade-consumer-postcheck` and `blueprint-upgrade-fresh-env-gate` lanes for consumers.

### Non-Functional Requirements (Normative)
- NFR-SEC-001 The fix MUST NOT introduce any new file write outside the existing init-managed and consumer-seeded path sets declared in `blueprint/contract.yaml`. Any newly-overwritten path MUST be added to the appropriate contract list (`consumer_seeded` or `init_managed`) in the same change so contract validation (`infra-validate`) detects future scope drift.
- NFR-OBS-001 The init flow MUST emit a structured log line (via `log_info`) for every file the fix newly seeds or reseeds, identifying the relative path and the seed source (template path), so operators can trace post-init state from console output.
- NFR-REL-001 The fix MUST be idempotent: running `BLUEPRINT_INIT_FORCE=true make blueprint-init-repo` twice in succession MUST converge to the same on-disk state and MUST NOT cause `infra-validate` to fail on the second run.
- NFR-OPS-001 The fix MUST require no consumer-side action beyond running the standard upgrade sequence (`make blueprint-upgrade-consumer && make blueprint-upgrade-consumer-postcheck`); no new env var, no new make target, no manual file edit MUST be required to recover.

## Normative Option Decision
- Option A: **Init force-resets the kustomization in lockstep with the descriptor.** Extend `seed_consumer_owned_files` (or add a sibling pass invoked from `init_repo.py`) so that whenever `apps/descriptor.yaml` is force-reseeded, `infra/gitops/platform/base/apps/kustomization.yaml` is also reseeded from `scripts/templates/infra/bootstrap/infra/gitops/platform/base/apps/kustomization.yaml`. Requires adding the kustomization path to `consumer_seeded` (or a new `init_force_paired` list) in `blueprint/contract.yaml`. Most direct fix; preserves the demo-app baseline for fresh inits.
- Option B: **Empty descriptor template (`apps: []`).** Change `scripts/templates/consumer/init/apps/descriptor.yaml.tmpl` so the init force-seed produces a descriptor with no components. `validate_app_descriptor` short-circuits to a no-op when there are no components, so the cross-check passes regardless of the consumer's existing kustomization. Consumers add their own apps post-init, matching the long-term ownership model where `apps/descriptor.yaml` is consumer-owned. Most defensive; eliminates the "two seeded templates must stay in lockstep" invariant entirely, but loses the demo-app baseline that source-mode smoke and fresh-init demos currently rely on.
- Option C: **`infra-bootstrap` reseeds kustomization on init force.** Extend `make infra-bootstrap` (or a sibling target invoked by init) to overwrite `kustomization.yaml` from the bootstrap template when `BLUEPRINT_INIT_FORCE=true` is set. Couples bootstrap behaviour to init flags; `infra-bootstrap` no longer has create-if-missing semantics for that one path. Less clean than A; rejected as primary recommendation.
- Selected option: OPTION_A
- Rationale: Q-1 resolved on PR #231 — reviewer (sbonoc, OWNER) selected Option A in PR comment 2026-04-28T01:21:28Z. Option A restores postcheck/fresh-env-gate quickly, keeps the "fresh init produces a runnable demo" property that source-mode smoke already depends on, and contains the change to the init contract surface where the pairing is conceptually owned. Option B remains a candidate for a separate v1.9 work item paired with onboarding-doc and source-mode-smoke updates; Option C is rejected because it would couple `infra-bootstrap` create-if-missing semantics to init flags.

## Contract Changes (Normative)
- Config/Env contract: `blueprint/contract.yaml` `consumer_seeded` list (or a new `init_force_paired` list — implementation-time decision) MUST include `infra/gitops/platform/base/apps/kustomization.yaml` so the init force-reseed scope is contract-declared and drift-checked.
- API contract: none
- OpenAPI / Pact contract path: none
- Event contract: none
- Make/CLI contract: no new make targets; `make blueprint-init-repo` (with `BLUEPRINT_INIT_FORCE=true`) gains a paired-reseed responsibility for `infra/gitops/platform/base/apps/kustomization.yaml` alongside `apps/descriptor.yaml`.
- Docs contract: `docs/blueprint/architecture/decisions/ADR-2026-04-28-issue-230-init-descriptor-kustomization-sync.md` (proposed → approved on Architecture sign-off); `docs/blueprint/upgrade/release_notes.md` v1.8.2 (or v1.8.1 follow-up) entry that explicitly documents the expanded force-init blast radius (one additional consumer-owned file).

## Blueprint Upstream Defect Escalation (Normative)
- Upstream issue URL: https://github.com/sbonoc/stackit-platform-blueprint/issues/230
- Temporary workaround path: no consumer-side fix is possible; consumers MUST acknowledge in their upgrade PR description that `generated-consumer-smoke` will fail until this ships, or temporarily mark the smoke job `continue-on-error: true` in their CI workflow.
- Replacement trigger: blueprint v1.8.2 (or v1.8.1 follow-up) released and consumed by `dhe-marketplace`; consumer drops the workaround note and re-enables the smoke job in CI.
- Workaround review date: 2026-07-28

## Normative Acceptance Criteria
- AC-001 MUST: in a synthetic consumer fixture whose pre-upgrade `infra/gitops/platform/base/apps/kustomization.yaml` lists `marketplace-*`/`backoffice-*` manifests (i.e. NOT the blueprint demo apps), running the full upgrade sequence (`make blueprint-upgrade-consumer && make blueprint-upgrade-consumer-postcheck`) MUST exit 0; `infra-validate` MUST NOT emit `manifest filename not listed in infra/gitops/platform/base/apps/kustomization.yaml` errors for any descriptor app.
- AC-002 MUST: a unit test MUST assert FR-001 directly — given a force-init applied to a consumer-state fixture (descriptor template + pre-existing non-matching kustomization), the post-init descriptor and kustomization MUST satisfy `validate_app_descriptor` with zero errors.
- AC-003 MUST: `make quality-ci-generated-consumer-smoke` and `make blueprint-template-smoke` MUST exit 0 in CI on the branch produced by this work item; the smoke fixture MUST cover the v1.8.0-state-shaped consumer kustomization scenario (FR-003).
- AC-004 MUST: a contract-level unit test MUST assert that, for the selected option, the on-disk init scope listed in `blueprint/contract.yaml` includes every path the init force-reseed actually writes (Option A: descriptor + kustomization both declared) — preventing future contract drift.

## Informative Notes (Non-Normative)
- Context: PR #228 (issue #217) tightened the cross-check validator without fixing the underlying init-seeding mismatch. The validator now correctly detects the drift, but every consumer upgrading from v1.8.0 hits the failure because their existing kustomization (with consumer apps like `marketplace-*`/`backoffice-*`) does not list the demo-app manifest filenames the init template force-reseeds into the descriptor. The smoke test in `scripts/bin/blueprint/template_smoke.sh` reproduces this exact sequence: `blueprint-init-repo` (overwrites descriptor) → `infra-bootstrap` (preserves kustomization via `ensure_file_from_template`'s create-if-missing semantics) → `infra-validate` (fails with 4 membership errors). PR #228's #217 spec FR-002 declared the source templates MUST agree, but the spec only enforced that invariant in the source repo — not after a consumer-side init force-reseed.
- Tradeoffs: Option A (selected) preserves the demo-app baseline that fresh-init tutorials and source-mode smoke depend on, at the cost of coupling two consumer-seeded files into a paired-reseed group. The PR #228 `template_smoke_assertions.py` cross-check already enforces filename-consistency at the source-template layer; AC-004 extends this to the contract layer to prevent future scope drift. Option B (empty descriptor) and Option C (bootstrap conditional on init flag) are documented for posterity in § Normative Option Decision but were not selected.
- Clarifications: none

## Explicit Exclusions
- Modifying `validate_app_descriptor` or `verify_kustomization_membership` — the validator behaviour is correct; the bug is upstream of validation in the seed pairing.
- Removing or weakening the `template_smoke_assertions.py` cross-check added by PR #228 — the assertion correctly catches the drift; the fix MUST satisfy the assertion, not bypass it.
- Changing the blueprint contract for `init_managed` paths (this work item does not touch identity files).
- Reverting PR #228 — the cross-check validator and smoke assertion are the right mechanisms; only the init/template seed pairing needs to change.
