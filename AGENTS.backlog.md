# Blueprint Backlog

## Current Priorities
- [ ] P0 (SDD UX): Issue #138 — add local smoke and positive-path filter/transform guardrails to SDD `plan.md`/`tasks.md` templates and governance docs.
- [ ] P0 (Upgrade preflight ergonomics): Issue #102 — detect missing consumer-owned required Make targets in preflight with explicit remediation guidance.
- [ ] P0 (Upgrade validation determinism): Issue #129 — add repo-mode-aware required-file reconciliation checks and deterministic remediation hints.
- [ ] P1 (Upgrade convergence safety): Issue #128 — add ownership-aware reconcile report artifact and `blueprint-upgrade-consumer-postcheck` gate.
- [ ] P1 (Fixture-contract hardening): Issue #130 — enforce optional-module `required_env` fixture parity in fast infra contract checks.
- [ ] P1 (Generated-consumer upgrade regressions): Issues #103, #104, #106, #107 — fix repo-mode test selection, additive-file conflict classification, and missing helper distribution.
- [ ] P1 (Runtime operability correctness): Issues #105, #108, #109, #110, #111, #112, #118, #137 — resolve runtime identity, Argo health/project policy, image-lane, and target migration friction.
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
