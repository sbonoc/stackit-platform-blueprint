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
- Required commands executed (intake stage):
  - `make spec-scaffold SPEC_SLUG=issue-230-init-descriptor-kustomization-sync` — succeeded; created `specs/2026-04-28-issue-230-init-descriptor-kustomization-sync/` and branch `codex/2026-04-28-issue-230-init-descriptor-kustomization-sync`
  - `make quality-sdd-check` — see Step 1 report appended to PR description
- Result summary: artifacts populated; one open question (Q-1) recorded; ADR drafted with `Status: proposed`.
- Artifact references:
  - `architecture.md`, `spec.md`, `plan.md`, `tasks.md`, `traceability.md`, `graph.json`, `evidence_manifest.json`, `context_pack.md`, `pr_context.md`, `hardening_review.md`
  - `docs/blueprint/architecture/decisions/ADR-2026-04-28-issue-230-init-descriptor-kustomization-sync.md`

## Risk and Rollback
- Main risks: (a) the selected fix (Option A) grows the force-init blast radius by one consumer-owned file (`infra/gitops/platform/base/apps/kustomization.yaml`); release notes MUST call this out explicitly. (b) Option B (empty descriptor) was deliberately deferred to a separate v1.9 work item with paired onboarding-doc and source-mode-smoke updates.
- Rollback strategy: single-commit revert of the contract + init code change. Validator and smoke assertion stay in place; failure mode reverts to the documented v1.8.1 baseline (postcheck fails with 4 membership errors).

## Open Questions

All open questions resolved.

- Q-1 (option selection) — resolved on PR #231 (reviewer comment 2026-04-28T01:21:28Z): **Option A**.

## Deferred Proposals
- Proposal 1 (not implemented): from `AGENTS.backlog.md` — `proposal(issue-217): extract _assert_descriptor_kustomization_agreement as shared module helper for future smoke scenario reuse` (`trigger: on-scope: blueprint`). Surfaced because this work item touches the same blueprint init/template scope. Recommended action: **park** — defer until the FR-003 smoke fixture extension lands and the second caller actually materializes; if implementing FR-003 introduces a clear second caller, promote to a follow-up issue at Step 8. The triage outcome MUST be confirmed by the user before this PR is marked ready.
