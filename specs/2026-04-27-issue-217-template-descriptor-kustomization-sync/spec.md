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
- ADR path: docs/blueprint/architecture/decisions/ADR-2026-04-27-issue-217-template-descriptor-kustomization-sync.md
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
- Business outcome: v1.8.1 patch resolves the blueprint-template-smoke failure that blocks blueprint-upgrade-consumer-validate for all consumers on v1.8.0; dhe-marketplace can drop their upgrade workaround in a single v1.8.1 upgrade cycle.
- Success metric: make blueprint-template-smoke exits 0 for all template scenarios; any future descriptor-kustomization filename drift is caught at template-edit time by the new smoke assertion rather than at consumer-upgrade time via infra-validate.

## Normative Requirements

### Functional Requirements (Normative)
- FR-001 MUST add a cross-check assertion in `scripts/lib/blueprint/template_smoke_assertions.py:main()` that reads the seeded `apps/descriptor.yaml` and `infra/gitops/platform/base/apps/kustomization.yaml` from the generated temp repo and verifies that every manifest filename referenced by descriptor components appears in the kustomization resources section. The assertion MUST execute when `APP_RUNTIME_GITOPS_ENABLED=true` and MUST be placed after the existing kustomization resource non-empty check so that it re-uses the already-parsed kustomization resource list. A failing assertion MUST raise AssertionError with a message that names the missing filename, the descriptor path, and the kustomization path.
- FR-002 MUST guarantee that `scripts/templates/infra/bootstrap/infra/gitops/platform/base/apps/kustomization.yaml` lists EXACTLY the set of manifest filenames derivable from components declared in `scripts/templates/consumer/init/apps/descriptor.yaml.tmpl`. The cross-check assertion introduced by FR-001 MUST serve as the automated enforcement mechanism for this invariant.

### Non-Functional Requirements (Normative)
- NFR-SEC-001 MUST NOT introduce any new file I/O path outside the `repo_root` argument passed to the assertion entry point. All reads MUST remain within the generated temp repo directory.
- NFR-OBS-001 MUST emit one distinct AssertionError message per missing filename, identifying the descriptor path, the kustomization path, and the exact missing filename, so operators can diagnose drift without inspecting the generated files manually.
- NFR-REL-001 MUST cause `template_smoke_assertions.py` to return non-zero (via AssertionError) whenever any descriptor manifest filename is absent from the kustomization resources set, so that `make blueprint-template-smoke` correctly fails on drift and blocks blueprint-upgrade-consumer-validate.
- NFR-OPS-001 MUST require no operator action beyond upgrading to v1.8.1; the fix MUST be fully contained in blueprint tooling with no configuration changes needed in consumer repos.

## Normative Option Decision
- Option A: Extend `template_smoke_assertions.py:main()` inline — add the descriptor-kustomization cross-check after the existing `app_manifest_names` extraction, re-using the already-loaded kustomization resource list and parsing `apps/descriptor.yaml` with `yaml.safe_load`.
- Option B: Extract a standalone validator into `app_descriptor.py` or a new module and call it from `template_smoke_assertions.py`.
- Selected option: OPTION_A
- Rationale: The assertion is smoke-specific — it compares two seeded files in the generated temp repo. Keeping it inline in `template_smoke_assertions.py` avoids leaking a generated-repo-scope helper into `app_descriptor.py`, which operates on the consumer's live repo. Option B adds a new public API surface that has no caller outside the smoke context.

## Contract Changes (Normative)
- Config/Env contract: none
- API contract: none
- OpenAPI / Pact contract path: none
- Event contract: none
- Make/CLI contract: `make blueprint-template-smoke` now fails on descriptor-kustomization filename drift (the underlying membership check already existed in `infra-validate`; this adds an explicit Python assertion in the post-smoke verification step so the failure is reported with a human-readable message before the operator inspects infra-validate logs)
- Docs contract: none

## Blueprint Upstream Defect Escalation (Normative)
- Upstream issue URL: https://github.com/sbonoc/stackit-platform-blueprint/issues/217
- Temporary workaround path: no consumer-side workaround is possible; the failure is acknowledged in the upgrade PR description and the workaround review date tracks the v1.8.1 upgrade window
- Replacement trigger: blueprint v1.8.1 release consumed by dhe-marketplace; consumer drops the workaround note from their upgrade PR description
- Workaround review date: 2026-07-27

## Normative Acceptance Criteria
- AC-001 MUST: `make blueprint-template-smoke APP_RUNTIME_GITOPS_ENABLED=true` against a generated repo where `apps/descriptor.yaml` references a filename absent from `infra/gitops/platform/base/apps/kustomization.yaml` MUST exit non-zero and emit an AssertionError message that names the missing filename and both file paths.
- AC-002 MUST: `make blueprint-template-smoke APP_RUNTIME_GITOPS_ENABLED=true` against the current consistent templates — where descriptor and kustomization both reference the same 4 manifest filenames — MUST exit 0 with no descriptor-kustomization assertion errors.
- AC-003 MUST: `scripts/templates/consumer/init/apps/descriptor.yaml.tmpl` and `scripts/templates/infra/bootstrap/infra/gitops/platform/base/apps/kustomization.yaml` MUST reference the same set of manifest filenames; this invariant MUST be verified by a unit test that reads both template files and compares their filename sets.

## Informative Notes (Non-Normative)
- Context: The descriptor template was introduced in slice 1 of the consumer-app-descriptor PR with 4 manifest references. The kustomization membership check was added in the same PR via validate_app_descriptor in app_runtime_gitops.py. The failure surfaced when blueprint-template-smoke ran infra-validate against the generated temp repo. The current main branch already has consistent content in both templates (all 4 filenames present in both). What was missing is an explicit assertion in the Python smoke verification step so that future template edits that introduce drift are caught early.
- Tradeoffs: Inline assertion (Option A) is tightly scoped to the smoke context and avoids adding a new public helper. A standalone helper (Option B) would be more reusable but creates coupling between app_descriptor.py and the smoke scenario.
- Clarifications: none

## Explicit Exclusions
- Modifying `validate_contract.py` or `app_descriptor.py` — the kustomization membership check already exists in infra-validate; this spec only adds a second, earlier-stage catch in template_smoke_assertions.py.
- Adding new make targets, environment variables, or config changes.
- Changing the descriptor or kustomization template content beyond what is already consistent on main.
