# Blueprint Backlog

## Current Priorities
- [x] P0 (SDD UX): Issue #138 — local smoke + positive-path filter/transform guardrails are now enforced in SDD templates/governance, including red->green translation for reproducible pre-PR findings.
- [x] P0 (Upgrade preflight ergonomics): Issue #102 — detect missing consumer-owned required Make targets in preflight with explicit remediation guidance.
- [x] P0 (Upgrade validation determinism): Issue #129 — add repo-mode-aware required-file reconciliation checks and deterministic remediation hints.
- [x] P0 (Docs ownership boundary for generated consumers): implemented repo-mode-aware docs sync/check behavior so generated-consumer repos keep one-way `docs/platform/**` ownership, template-source retains strict sync, and generated-consumer upgrade/bootstrap now cleans template-orphan platform docs outside contract-declared `required_seed_files`.
- [x] P1 (Upgrade convergence safety): Issue #128 — implemented ownership-aware reconcile report artifact and `blueprint-upgrade-consumer-postcheck` gate, including preflight merge-risk bucketing, postcheck convergence enforcement, and source-ref wrapper compatibility for legacy engines.
- [x] P1 (Fixture-contract hardening): Issue #130 — enforce optional-module `required_env` fixture parity in fast infra contract checks (canonical fixture resolver wiring + fast-lane parity tests).
- [x] P1 (Generated-consumer upgrade regressions): Issue #103 — `infra-contract-test-fast` is now repo-mode aware (generated-consumer skips template-source-only tests; template-source remains fail-fast for missing selected tests).
- [x] P1 (Generated-consumer upgrade regressions): Issues #104, #106, #107 — fix additive-file conflict classification and missing helper distribution. **Done**: `specs/2026-04-22-issue-104-106-107-upgrade-additive-file-helper-gaps/`
- [x] P1 (ArgoCD AppProject namespace policy gap): Issues #108, #109 — `external-secrets` destination added to all overlay AppProject files; guard test added in `infra-contract-test-fast`; Issue #109 cause #2 (ESO NotReady for unneeded optional modules) deferred to #137. **Done**: `specs/2026-04-22-issue-108-109-argocd-appproject-namespace-policy/`
- [x] P1 (SDD quality gate gap): Issue #152 — `check_sdd_assets.py` does not detect unfilled scaffold placeholders in `architecture.md` or `context_pack.md`; both can ship as pure scaffold output and pass `make quality-hardening-review`. **Done**: `specs/2026-04-22-issue-152-sdd-placeholder-guard/`
- [x] P1 (Runtime operability correctness) — Work item A: Issues #105 + #110 — fix best-effort provision hard-fail in reconcile_eso_runtime_secrets.sh and clarify gho_ token policy in reconcile_argocd_repo_credentials.sh (both in scripts/bin/platform/auth/). **Done**: `specs/2026-04-22-issue-105-110-runtime-auth-best-effort-fix/`
- [x] P1 (Runtime operability correctness) — Work item B: Issues #111 + #112 — scaffold canonical backend/touchpoints Dockerfiles so image lanes work out of the box, and replace placeholder workloads (http.server/nginx) with real app runtime in generated consumers. **Done**: `specs/2026-04-22-issue-111-112-app-dockerfile-and-runtime/`
- [x] P1 (Runtime operability correctness) — Work item C: Issues #118 + #137 — add upgrade preflight detection for removed infra-<module>-* make targets (#118) and fix postgres ESO seed key mismatch causing continuous UpdateFailed events (#137, P2 in GH). **Done**: `specs/2026-04-22-issue-118-137-preflight-module-targets-postgres-eso-key/`
- [x] P1 (SDD publish-gate gap): add a `quality-spec-pr-ready` make target (new script `scripts/bin/quality/check_spec_pr_ready.py`) to detect unfilled scaffold placeholders and incomplete publish artifacts in `plan.md`, `tasks.md`, `hardening_review.md`, and `pr_context.md` before a PR is opened. **Done**: `specs/2026-04-22-quality-spec-pr-ready-publish-gate/`

- [ ] P2 (Ownership checker robustness): support normalized equivalence for semantically-identical prune-glob expressions in ownership-matrix documentation checks.
- [ ] P2 (Capability enhancements): Issues #56, #131 — expand app dependency pin auditing and add blueprint uplift convergence status command.
- [ ] Add an automated bundled-skill contract verifier to enforce parity across `.agents/skills/**`, consumer-template fallbacks, install make targets, and docs references.
- [ ] Add a contract-level traceability verifier that checks every declared requirement ID in `spec.md` maps to implementation paths and at least one automated test assertion.
- [ ] Add a declarative module action manifest (`apply/plan/smoke/destroy`) to replace duplicated wrapper branching and keep runtime/CI execution paths deterministic.
- [ ] Extract artifact/schema validation orchestration into a shared Python package entrypoint consumed by blueprint wrappers (single validation surface for state/schema contracts).
- [ ] Add a repository-wide script trace identifier contract propagated across wrapper calls and metrics to improve CI/runtime diagnosability for multi-script failures.
- [ ] Auto-generate docs snippets for canonical blueprint lifecycle + audit targets from source metadata to reduce docs drift and manual synchronization load.
- [ ] Split CI into path-aware lane selection for contract/docs-only vs infra/runtime-heavy changes while preserving full strict gates on merge/main updates.
- [ ] Backport the new runtime-credentials ESO source-to-target contract (including mandatory Keycloak/IAP runtime targets) and drift-safe platform extension surface to existing generated-consumer repositories.
- [ ] Add a DNS contract mode where generated-consumer repos can provide pre-created Keycloak/IAP DNS entries instead of blueprint-managed STACKIT DNS record reconciliation.
- [ ] Add a CI-grade execute-mode full e2e lane (ephemeral cluster + `test-e2e-all-local-execute`) so merge gating covers real apply paths, not only dry-run orchestration.
- [ ] Tune and baseline `E2E_*_BUDGET_SECONDS` from collected CI metrics (p95 per lane) and fail budgets only once the baseline is stable.
- [ ] Split the mirrored Python version pin so STACKIT Workflows can keep its runtime-limited baseline while the rest of the blueprint tracks latest stable upstream Python.
- [ ] Continue migrating `workflows` to provider-backed STACKIT execution when official resources become available.
- [ ] Add optional Neo4j Keycloak realm/client reconciliation (gated by `KEYCLOAK_OPTIONAL_MODULE_RECONCILIATION_ENABLED`) as a follow-up to current Workflows/Langfuse reconciliation.
- [ ] Extend the consumer seed resync workflow with optional merge-assist coverage for selected init-managed identity files without weakening customization boundaries.
- [ ] Add pluggable async message-contract provider support beyond Pact while preserving the canonical producer/consumer lane contract and upgrade safety guarantees.

## Provider-Backed STACKIT Expansion Candidates
- [ ] Evaluate and add a provider-backed Redis module built on official STACKIT Terraform resources.
- [ ] Evaluate and add provider-backed relational/NoSQL data-service modules for the currently available STACKIT Terraform resources (`mariadb`, `mongodbflex`, `sqlserverflex`).
- [ ] Evaluate and add a provider-backed Logs/LogMe module or baseline observability extension using official STACKIT Terraform resources.
- [ ] Evaluate and add a provider-backed File Storage module using STACKIT SFS Terraform resources.
- [ ] Evaluate whether STACKIT Application Load Balancer, CDN, and Public IP resources should become first-class edge modules alongside or instead of the current Gateway API baseline.
- [ ] Evaluate whether STACKIT network and security primitives (`network`, `network_area`, `routing_table`, `security_group`) should become first-class foundation capabilities in this blueprint.
- [ ] Evaluate whether STACKIT identity/project primitives (`service_account`, role assignments, Resource Manager folders/projects) should become blueprint-managed bootstrap/foundation capabilities.
- [ ] Evaluate whether STACKIT compute-oriented primitives (`server`, `volume`, `edgecloud`, `modelserving`) belong in blueprint scope for future workload patterns.
