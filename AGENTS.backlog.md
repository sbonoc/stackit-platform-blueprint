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
- [x] P2 (Capability enhancements): Issue #56 — expand app dependency pin auditing. **Done**: `specs/2026-04-23-issue-56-app-version-contract-checks/`
- [x] P2 (Capability enhancements): Issue #131 — add blueprint uplift convergence status command. **Done**: `specs/2026-04-22-issue-131-blueprint-uplift-status/`

### Consumer upgrade flow improvements

The items below form a layered programme: #166 and #169 ship first (#160 already done); #162 and #163 run inside the CI job introduced by #169; #164 and #165 improve the reporting layer once the correctness foundation is solid; #167 and #168 deliver the best long-term consumer experience on top of a proven baseline.

#### Phase 1 — Foundation and quick wins (parallel)

- [x] P1 (Consumer upgrade flow): Issue #160 — `consumer_seeded_paths` not honoured in `ensure_infra_template_file`/`ensure_infra_rendered_file`; placeholder manifests recreated on every bootstrap run. **Done**: `specs/2026-04-23-issue-160-bootstrap-consumer-seeded-paths-guard/`
- [x] P1 (Consumer upgrade flow): Issue #166 — `run_cmd_capture` merges stderr into stdout, corrupting parsed command output; any caller that parses the result receives injected warning lines, silently returning wrong values in environment-dependent ways. Fixed by removing `2>&1` from `run_cmd_capture` so it captures stdout only. **Done**: `specs/2026-04-23-issue-166-run-cmd-capture-stderr-isolation/`
- [ ] P1 (Consumer upgrade flow): Issue #169 — add end-to-end consumer upgrade validation job in blueprint CI before tag publication; provisions a reference consumer at the previous stable tag, runs the full upgrade flow to the candidate tag, and runs post-upgrade smoke gates in a clean environment. Foundation that makes all Phase 2 correctness gates (#162, #163) automated regression tests on every release.

#### Phase 2 — Correctness gates (implement inside the Phase 1 CI job)

- [ ] P1 (Consumer upgrade flow): Issue #162 — add post-merge behavioral validation gate for merge-required plan entries; run `bash -n` on all modified shell scripts and resolve function call sites to verify no definition was silently dropped by a 3-way merge. Catches the most dangerous upgrade failure class: a green merge that produces `command not found` at runtime.
- [ ] P1 (Consumer upgrade flow): Issue #163 — run the post-upgrade smoke gate in a temporary clean worktree (fresh-environment simulation) so CI-only failures — files absent on a fresh checkout but present in the developer's working tree — are surfaced during the local upgrade run, before the PR is opened.

#### Phase 3 — Reporting and guidance improvements

- [ ] P2 (Consumer upgrade flow): Issue #164 — in the upgrade preflight report, list all version pin changes in `versions.sh` between the two tags and map each changed pin to the template files it affects; provide an explicit action item to sync them after `infra-bootstrap` rather than leaving the consumer to discover template drift reactively via `infra-validate`.
- [ ] P2 (Consumer upgrade flow): Issue #165 — enrich merge-required plan entries with semantic annotations describing what changed in each file and what the consumer should verify after applying the merge (e.g. "new function `foo` added — verify definition is present in merged result"); annotations appear in both the plan output and the post-apply report.

#### Phase 4 — Major UX improvements (build on the stable correctness foundation)

- [ ] P2 (Consumer upgrade flow): Issue #167 — add `BLUEPRINT_UPGRADE_DRY_RUN=true` flag that simulates all file mutations (copy, 3-way merge, skip, consumer-owned) and outputs a unified diff of the full change set without touching the working tree; reports the same warnings, conflicts, and behavioral failures the real apply would surface so consumers can review the exact change before committing to apply.
- [ ] P2 (Consumer upgrade flow): Issue #168 — add incremental tag-to-tag upgrade mode (`BLUEPRINT_UPGRADE_INCREMENTAL=true`) that applies changes one release at a time, surfacing a per-release changelog and cherry-pick plan at each step with resume support on conflict; batch mode remains the default.

---

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
