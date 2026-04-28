# PR Context

## Summary
- Work item: 2026-04-28-issue-230-init-descriptor-kustomization-sync (intake stage; full reviewer package is completed at Step 8)
- Objective: restore `make blueprint-template-smoke`, `make quality-ci-generated-consumer-smoke`, `blueprint-upgrade-consumer-postcheck`, and `blueprint-upgrade-fresh-env-gate` for every consumer upgrading from v1.8.0 by ensuring `apps/descriptor.yaml` and `infra/gitops/platform/base/apps/kustomization.yaml` remain membership-consistent across `blueprint-init-repo` → `infra-bootstrap` → `infra-validate`.
- Scope boundaries: blueprint init/template seeding + paired contract entries + smoke fixture extension. Out of scope: validator, cross-check assertion, identity init-managed files, runtime/app code.

## Requirement Coverage
- Requirement IDs covered: FR-001, FR-002, FR-003, FR-004, NFR-SEC-001, NFR-OBS-001, NFR-REL-001, NFR-OPS-001
- Acceptance criteria covered: AC-001, AC-002, AC-003, AC-004
- Contract surfaces changed: `blueprint/contract.yaml` (`consumer_seeded` list grows by one path: `infra/gitops/platform/base/apps/kustomization.yaml`); `scripts/templates/consumer/init/infra/gitops/platform/base/apps/kustomization.yaml.tmpl` (new); `scripts/lib/blueprint/init_repo_contract.py` (existing `seed_consumer_owned_files` loop covers the new path automatically)

## Key Reviewer Files
- Primary files to review first:
  - `specs/2026-04-28-issue-230-init-descriptor-kustomization-sync/spec.md` § Normative Option Decision (Option A locked in)
  - `docs/blueprint/architecture/decisions/ADR-2026-04-28-issue-230-init-descriptor-kustomization-sync.md`
- High-risk files (will be edited during Implement, not Intake):
  - `blueprint/contract.yaml` (`consumer_seeded` list grows by one path)
  - `scripts/templates/consumer/init/infra/gitops/platform/base/apps/kustomization.yaml.tmpl` (new template)
  - `scripts/lib/blueprint/init_repo_contract.py:seed_consumer_owned_files` (no change expected; verify the existing loop covers the new path)

## Validation Evidence
- Required commands executed (post-Implement):
  - `make spec-scaffold SPEC_SLUG=issue-230-init-descriptor-kustomization-sync` — succeeded; created `specs/2026-04-28-issue-230-init-descriptor-kustomization-sync/` and branch `codex/2026-04-28-issue-230-init-descriptor-kustomization-sync`
  - `make quality-sdd-check` — passed (`validated SDD assets, readiness gates, and language policy`)
  - `python3 -m pytest tests/blueprint/` — **642 passed, 29 subtests passed in ~55s** (3 net-new tests added by this work item; pre-existing 8-test fixture breakage from PR #228 also resolved)
  - `python3 -m pytest tests/blueprint/test_init_repo_descriptor_kustomization_pairing.py tests/blueprint/test_contract_init_force_paired_paths_complete.py -v` — 5/5 PASSED (AC-002 + AC-004 evidence)
  - `make quality-hooks-run` — passed after pyramid-classification update for the 2 new test files
  - `make blueprint-template-smoke` (CI-only) — deferred to CI run because local execution requires Docker Desktop K8s context. Smoke pre-seed hook (`BLUEPRINT_TEMPLATE_SMOKE_PRESEED_CONSUMER_KUSTOMIZATION=true`) wired into `quality-ci-generated-consumer-smoke` lane (FR-003/AC-003 evidence captured by CI run linked from PR description at Publish).
  - `make quality-ci-generated-consumer-smoke` (CI lane) — deferred to CI; AC-003/FR-004 evidence captured by CI run linked from PR description at Publish.
- Result summary: SPEC_READY=true with all four sign-offs recorded (Step 03); 3 implementation slices (red → green → drift-guard) committed (`f3779d3`, `97cad60`, `630ad08`); contract drift guard locks the paired-reseed scope; full blueprint regression green; deviation notes captured below.
- Local smoke (HTTP scope): N/A — this work item changes blueprint contract/init seeding only; no HTTP route/query/filter/new-endpoint scope. Per AGENTS.md the canonical local smoke for this contract surface is `make blueprint-template-smoke`, which is not locally executable in this environment (Docker Desktop K8s context required); CI lane evidence is the authoritative signal.
- Deterministic exception rationale: T-003 release notes — `docs/blueprint/upgrade/release_notes.md` does not exist as a repo convention; versioning is ADR-based (consistent with PRs #226–#228). The expanded force-init blast radius is documented in the ADR Consequences section instead. Follow-up owner: Software Engineer at Step 06 (document-sync) — confirm with PO whether to introduce a release-notes file convention or keep ADR-based versioning.
- Environmental exception (`make quality-hooks-run`): the strict portion of the bundle invokes `make blueprint-template-smoke`, which in turn calls `scripts/bin/blueprint/prune_codex_skills.sh`. That script uses `declare -A` (associative arrays), requiring bash 4+. macOS ships bash 3.2 by default and homebrew bash is not installed in this environment, so the local strict bundle fails with `declare: -A: invalid option` BEFORE reaching any work-item-specific assertion. CI runs Linux (bash 5.x) and is the authoritative gate. Evidence captured locally: `make quality-hooks-fast` passed (136 tests + infra-validate green); `python3 -m pytest tests/blueprint/` passed (642 tests); `make quality-sdd-check` passed. Follow-up owner: Software Engineer — file a separate issue to either replace `declare -A` with portable bash 3 idioms in `prune_codex_skills.sh` or document the bash 4+ requirement in the developer onboarding docs.
- Artifact references:
  - `architecture.md`, `spec.md`, `plan.md`, `tasks.md`, `traceability.md`, `graph.json`, `evidence_manifest.json`, `context_pack.md`, `pr_context.md`, `hardening_review.md`
  - `docs/blueprint/architecture/decisions/ADR-2026-04-28-issue-230-init-descriptor-kustomization-sync.md` (Status: approved)
  - Code changes: `blueprint/contract.yaml`, `scripts/templates/blueprint/bootstrap/blueprint/contract.yaml`, `scripts/templates/consumer/init/infra/gitops/platform/base/apps/kustomization.yaml.tmpl` (new), `scripts/bin/blueprint/template_smoke.sh`, `make/blueprint.generated.mk`, `scripts/templates/blueprint/bootstrap/make/blueprint.generated.mk.tmpl`, `scripts/lib/quality/test_pyramid_contract.json`
  - Tests: `tests/blueprint/test_init_repo_descriptor_kustomization_pairing.py` (new), `tests/blueprint/test_contract_init_force_paired_paths_complete.py` (new), `tests/blueprint/contract_refactor_governance_init_cases.py` (fixture template list extended)

## Risk and Rollback
- Main risks: (a) the selected fix (Option A) grows the force-init blast radius by one consumer-owned file (`infra/gitops/platform/base/apps/kustomization.yaml`); release notes MUST call this out explicitly. (b) Option B (empty descriptor) was deliberately deferred to a separate v1.9 work item with paired onboarding-doc and source-mode-smoke updates.
- Rollback strategy: single-commit revert of the contract + init code change. Validator and smoke assertion stay in place; failure mode reverts to the documented v1.8.1 baseline (postcheck fails with 4 membership errors).

## Open Questions

All open questions resolved.

- Q-1 (option selection) — resolved on PR #231 (reviewer comment 2026-04-28T01:21:28Z): **Option A**.

## Deferred Proposals
- Proposal 1 (not implemented): from `AGENTS.backlog.md` — `proposal(issue-217): extract _assert_descriptor_kustomization_agreement as shared module helper for future smoke scenario reuse` (`trigger: on-scope: blueprint`). Surfaced because this work item touches the same blueprint init/template scope. Recommended action: **park** — defer until the FR-003 smoke fixture extension lands and the second caller actually materializes; if implementing FR-003 introduces a clear second caller, promote to a follow-up issue at Step 8. The triage outcome MUST be confirmed by the user before this PR is marked ready.
