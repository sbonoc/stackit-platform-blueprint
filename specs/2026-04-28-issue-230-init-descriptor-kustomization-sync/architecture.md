# Architecture

## Context
- Work item: issue #230 — `v1.8.1` incomplete fix for `#217`: descriptor↔kustomization cross-check tightened the validator but the underlying init-seeding mismatch was not fixed; smoke is broken for every consumer upgrading from v1.8.0.
- Owner: Platform / Blueprint maintainer
- Date: 2026-04-28

## Stack and Execution Model
- Backend stack profile: explicit-consumer-exception (blueprint Python tooling — `scripts/lib/blueprint/init_repo*.py`, `scripts/bin/blueprint/template_smoke.sh`)
- Frontend stack profile: not-applicable-stackit-runtime
- Test automation profile: explicit-consumer-exception (`pytest` against blueprint tooling fixtures + bash smoke under `make blueprint-template-smoke` and `make quality-ci-generated-consumer-smoke`)
- Agent execution model: specialized-subagents-isolated-worktrees

## Problem Statement
- What needs to change and why: The `blueprint-init-repo` flow force-reseeds `apps/descriptor.yaml` from `scripts/templates/consumer/init/apps/descriptor.yaml.tmpl` (which references `backend-api`/`touchpoints-web` manifests). The downstream `make infra-bootstrap` step seeds `infra/gitops/platform/base/apps/kustomization.yaml` via `ensure_file_from_template`, which has create-if-missing semantics — so a consumer's existing kustomization (listing their actual apps, e.g. `marketplace-*`/`backoffice-*`) is preserved. The new descriptor↔kustomization cross-check added in PR #228 then correctly detects the drift and `infra-validate` fails. The fix MUST keep the two files in lockstep across a force-init, OR remove the pairing invariant by emitting an empty descriptor template.
- Scope boundaries: blueprint init flow (`scripts/lib/blueprint/init_repo*.py`, `scripts/templates/consumer/init/apps/descriptor.yaml.tmpl`); blueprint contract (`blueprint/contract.yaml` `consumer_seeded` list); template smoke fixtures (`scripts/bin/blueprint/template_smoke.sh`, `tests/blueprint/fixtures/upgrade_matrix/`); CI lane `quality-ci-generated-consumer-smoke`.
- Out of scope: the validator (`scripts/lib/blueprint/app_descriptor.py:verify_kustomization_membership`) and the cross-check assertion (`scripts/lib/blueprint/template_smoke_assertions.py:_assert_descriptor_kustomization_agreement`) — both are correct and MUST stay; this work item supplies the missing seed-pair management upstream of them.

## Bounded Contexts and Responsibilities
- Context A — `blueprint-init-repo` (consumer-owned seed force-reseed): owns the post-init state of consumer-owned files. Today it force-reseeds `apps/descriptor.yaml` but NOT `infra/gitops/platform/base/apps/kustomization.yaml`. The fix MUST close this gap (Option A) or remove the dependency (Option B).
- Context B — `infra-bootstrap` (create-if-missing infra seed): owns the post-bootstrap state of infra files and intentionally preserves consumer state. The fix MUST NOT couple bootstrap behaviour to init flags (this is why Option C is rejected as primary).
- Context C — `validate_app_descriptor` (membership cross-check): owns the runtime invariant that descriptor manifest filenames ⊆ kustomization resources. Behaviour is correct; this work item makes upstream seed pairing satisfy this invariant by construction.
- Context D — template smoke (`scripts/bin/blueprint/template_smoke.sh` + `template_smoke_assertions.py`): owns the upstream-side detection of seed drift. Today it asserts the source-blueprint templates agree, but does NOT exercise the v1.8.0-state-shaped consumer-fixture scenario. FR-003 extends smoke to cover that.

## High-Level Component Design
- Domain layer: not applicable (blueprint tooling, no business domain).
- Application layer: `scripts/lib/blueprint/init_repo.py:main()` (entry point), `scripts/lib/blueprint/init_repo_contract.py:seed_consumer_owned_files()` (Option A: extend to include the kustomization path; Option B: descriptor template change only).
- Infrastructure adapters: `scripts/lib/blueprint/cli_support.py:render_template`/`apply_file_update` (existing seed application primitives) — re-used as-is by Option A; no change for Option B.
- Presentation/API/workflow boundaries: `scripts/bin/blueprint/init_repo.sh` (CLI shim), `make/blueprint.generated.mk:blueprint-init-repo` (make wrapper), `scripts/bin/blueprint/template_smoke.sh` (smoke driver) — none change for Option A or B beyond an updated smoke fixture.

## Integration and Dependency Edges
- Upstream dependencies: `blueprint/contract.yaml` `consumer_seeded` list (Option A adds the kustomization path; Option B unchanged); `scripts/templates/consumer/init/apps/descriptor.yaml.tmpl` (Option B replaces with `apps: []`); `scripts/templates/infra/bootstrap/infra/gitops/platform/base/apps/kustomization.yaml` (Option A: paired with descriptor.yaml.tmpl; Option B: untouched but no longer constrained by descriptor).
- Downstream dependencies: `validate_app_descriptor` → `verify_kustomization_membership` (`scripts/lib/blueprint/app_descriptor.py`) — both options leave it untouched; Option B causes it to short-circuit (no components); Option A causes it to pass with matching filename sets. `template_smoke_assertions.py:_assert_descriptor_kustomization_agreement` — both options leave it satisfied.
- Data/API/event contracts touched: only `blueprint/contract.yaml` (Option A) — `consumer_seeded` list grows by one path. No runtime API/event contracts touched.

## Non-Functional Architecture Notes
- Security: no new file-write paths outside the existing init-managed/consumer-seeded contract surface. Option A explicitly extends the declared scope (NFR-SEC-001) so contract validation continues to detect drift. Option B reduces write scope.
- Observability: `log_info` lines for every newly-seeded file (NFR-OBS-001). Existing `apply_file_update`/`ChangeSummary` mechanism already provides this for descriptor and would automatically cover the kustomization path under Option A.
- Reliability and rollback: idempotent re-runs (NFR-REL-001). Rollback is a single-commit revert of the contract + init code change; the validator and smoke assertion stay intact, so a revert reverts the failure to its pre-fix state (postcheck fails) — matching the issue's pre-fix baseline. Consumers can revert by pinning to the previous blueprint tag.
- Monitoring/alerting: existing CI lanes (`quality-ci-generated-consumer-smoke`, `make blueprint-template-smoke`) MUST exit 0 — these are the canonical operator-facing signals for this contract surface.

## Risks and Tradeoffs
- Risk 1 — Option A couples descriptor and kustomization templates into a paired-reseed group; future template edits MUST keep them filename-consistent. Mitigation: PR #228's `template_smoke_assertions.py` cross-check already enforces this for the source repo, and FR-003's extended smoke fixture extends enforcement to the consumer-state path.
- Risk 2 — Option B changes the fresh-init starting state. Mitigation: not adopted as primary recommendation; if selected, requires paired updates to onboarding docs (`docs/platform/consumer/app_onboarding.md`) and to source-mode smoke expectations (the source blueprint repo currently keeps a populated `apps/descriptor.yaml` for self-test demo).
- Tradeoff 1 — Demo-baseline preservation (Option A) vs. invariant elimination (Option B). Option A keeps the runnable-demo property at the cost of maintaining a paired-reseed contract; Option B inverts the tradeoff. Recommendation: Option A for v1.8.x patch; Option B as a separate proposal for v1.9 alongside an onboarding-doc rewrite.
