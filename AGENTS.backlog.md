# Blueprint Backlog

## Scope Registry

Controlled vocabulary for `on-scope:` backlog trigger tags.
When assigning a tag, pick the closest existing entry.
To introduce a new tag, append a row here in the same commit that uses it.

| Tag | Covers |
|---|---|
| `auth` | Authentication, authorization, identity, ESO, Keycloak |
| `infra` | Terraform, Helm, ArgoCD, cluster provisioning |
| `observability` | Logs, metrics, traces, alerting, dashboards |
| `api` | HTTP routes, filters, payloads, API contracts |
| `apps` | App delivery, build, publish, catalog, GitOps workloads |
| `docs` | Documentation, runbooks, blueprint docs sync |
| `quality` | Test automation, CI gates, quality hooks, SDD gates |
| `blueprint` | Blueprint upgrade, contract, template sync, init flow |
| `gitops` | GitOps manifests, ArgoCD sync, kustomization wiring |
| `skills` | Agent skill runbooks, SDD lifecycle tooling |
| `a11y` | Accessibility conformance, WCAG gates, ACR scaffold, axe tooling |

---

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
- [x] P1 (Agent inner-loop quality ergonomics): PR #232 — keep-going aggregation mode (`--keep-going` / `QUALITY_HOOKS_KEEP_GOING=true`), path-gating of infra checks, phase-gating of `quality-spec-pr-ready`, dedup of pre-commit-redundant checks, Step 5 skill per-slice gate clarification, and agent-agnostic env propagation. `make quality-hooks-fast` on docs/spec-only commits drops from ~107 s to under 15 s. **Done**: `specs/2026-04-28-quality-hooks-keep-going-mode/`
- [x] P1 (Runtime auth correctness): Issue #234 — `parse_literal_pairs()` splits `RUNTIME_CREDENTIALS_SOURCE_SECRET_LITERALS` on commas, silently truncating values containing commas (data URIs, base64 payloads); ESO source secret never created, all ExternalSecrets `NotReady`. Fix: newline-only `while IFS= read -r pair` loop; comma-separated input rejected with `log_warn`. Breaking change (Option B). **Done**: `specs/2026-04-28-issue-234-literal-pairs-newline-format/`, PR #235.
- [x] P1 (Make target ergonomics): Issue #241 (bug) — GNU Make override warnings when consumer re-defines blueprint-generated targets; expose `?=` override-point variables (`SPEC_SCAFFOLD_DEFAULT_TRACK`, `BLUEPRINT_UPLIFT_STATUS_SCRIPT`) in `blueprint.generated.mk` so consumers customise target behaviour without full target re-definition. **Done**: `specs/2026-04-30-issue-241-make-override-warnings/`, PR #242.
- [ ] (parked) proposal(issue-241-make-override-warnings): extend `?=` override-point pattern to other blueprint-managed targets
      trigger: on-scope: blueprint
      rationale: no consumer request for specific targets; same pattern directly applicable; surfaces when blueprint template/upgrade scope is next touched
- [x] P1 (Accessibility compliance): Issues #238 + #239 + #240 — **Done**: `specs/2026-04-30-issue-238-239-240-a11y-compliance/`, PR #243.
- [ ] proposal(issue-238-239-240-a11y-compliance): create consumer_fitness_status.sh for consumer-side fitness checks — https://github.com/sbonoc/stackit-platform-blueprint/issues/244
- [ ] proposal(issue-238-239-240-a11y-compliance): add layer: field to spec.md template for conditional a11y sections — https://github.com/sbonoc/stackit-platform-blueprint/issues/245
- [ ] (parked) proposal(issue-238-239-240-a11y-compliance): wire quality-a11y-acr-check into quality-ci-blueprint
      trigger: on-scope: quality
      rationale: revisit when CI blueprint gains a stable ACR or a skip mechanism; false-positive risk currently blocks this
- [ ] (parked) proposal(issue-238-239-240-a11y-compliance): automated W3C JSON fetch in sync_acr_criteria.py
      trigger: on-scope: a11y
      rationale: adds network dependency at CI time; surface when any a11y-scope work item is next in flight
- [x] P2 (Quality gate extensions): Issues #236 + #237 — **Done** — `specs/2026-04-30-issue-236-237-quality-gate-extensions/`, PR #246. (1) #236: `pnpm-lockfile-sync` pre-push hook in `.pre-commit-config.yaml` bootstrap template; (2) #237: `quality-consumer-pre-push` + `quality-consumer-ci` no-op stubs in `blueprint.generated.mk`, wired into pre-push hook and `quality-ci-blueprint`; `AGENTS.md.tmpl` tier documentation; 7 new contract assertions; 136 total passing.
- [ ] (parked) proposal(quality-hooks-keep-going-mode): parallel execution of independent quality-hooks checks
      trigger: on-scope: quality
      rationale: real optimization but non-trivial (log ordering, signal propagation, interleaved output); see ADR-20260428 Alternative D and ADR-20260430 Alternative D; surfaces when quality infrastructure is next touched
- [ ] (parked) proposal(quality-hooks-keep-going-mode): structured JSON summary output for machine consumers of the keep-going summary block
      trigger: on-scope: quality
      rationale: no current consumer; plain-text v1 contract is sufficient; design when a concrete integration need arises

- [ ] P2 (Ownership checker robustness): support normalized equivalence for semantically-identical prune-glob expressions in ownership-matrix documentation checks.
- [x] P2 (Capability enhancements): Issue #56 — expand app dependency pin auditing. **Done**: `specs/2026-04-23-issue-56-app-version-contract-checks/`
- [x] P2 (Capability enhancements): Issue #131 — add blueprint uplift convergence status command. **Done**: `specs/2026-04-22-issue-131-blueprint-uplift-status/`

### Consumer upgrade flow improvements

The items below form a layered programme: #166 and #169 ship first (#160 already done); #162 and #163 run inside the CI job introduced by #169; #164 and #165 improve the reporting layer once the correctness foundation is solid; #167 and #168 deliver the best long-term consumer experience on top of a proven baseline.

#### Phase 1 — Foundation and quick wins (parallel)

- [x] P1 (Consumer upgrade flow): Issue #160 — `consumer_seeded_paths` not honoured in `ensure_infra_template_file`/`ensure_infra_rendered_file`; placeholder manifests recreated on every bootstrap run. **Done**: `specs/2026-04-23-issue-160-bootstrap-consumer-seeded-paths-guard/`
- [x] P1 (Consumer upgrade flow): Issue #166 — `run_cmd_capture` merges stderr into stdout, corrupting parsed command output; any caller that parses the result receives injected warning lines, silently returning wrong values in environment-dependent ways. Fixed by removing `2>&1` from `run_cmd_capture` so it captures stdout only. **Done**: `specs/2026-04-23-issue-166-run-cmd-capture-stderr-isolation/`
- [x] P1 (Consumer upgrade flow): Issue #169 — add end-to-end consumer upgrade validation job in blueprint CI before tag publication; provisions a reference consumer at the previous stable tag, runs the full upgrade flow to the candidate tag, and runs post-upgrade smoke gates in a clean environment. Foundation that makes all Phase 2 correctness gates (#162, #163) automated regression tests on every release. **Done**: `specs/2026-04-23-issue-169-upgrade-ci-e2e-validation/`

#### Phase 2 — Correctness gates (implement inside the Phase 1 CI job)

- [x] P1 (Consumer upgrade flow): Issue #162 — add post-merge behavioral validation gate for merge-required plan entries; run `bash -n` on all modified shell scripts and resolve function call sites to verify no definition was silently dropped by a 3-way merge. **Done**: `specs/2026-04-23-issue-162-post-merge-behavioral-validation/`
- [x] P1 (Consumer upgrade flow): Issue #163 — run the post-upgrade smoke gate in a temporary clean worktree (fresh-environment simulation) so CI-only failures are surfaced during the local upgrade run, before the PR is opened. **Done**: `specs/2026-04-23-issue-163-fresh-env-smoke-gate/`

#### Phase 2 — Bug-fix layer (correctness regressions in the gates above)

Four independent tracks; all P1, can be started in parallel.

- [x] P1 (Consumer upgrade flow): Issue #182 — `upgrade_fresh_env_gate`: clean worktree missing gitignored upgrade artifacts; postcheck always fails. **Done**: `specs/2026-04-24-issue-182-fresh-env-gate-gitignored-artifacts/`
- [x] P1 (Consumer upgrade flow): Issue #189 — upgrade planner and postcheck do not enforce `source_artifact_prune_globs_on_init`; consumer repos can re-acquire blueprint-internal files (e.g. ADRs, specs) during upgrade with no warning. Reported from a real consumer upgrade incident (sbonoc/dhe-marketplace#40 — 25 ADRs re-introduced). Requires: planner emits `prune-glob-excluded`/`prune-glob-violation` entries; validate scans for violations; postcheck blocks on non-empty `prune_glob_violations`. **Done**: `specs/2026-04-24-issue-189-prune-glob-enforcement/` (PR #190 + PR #194 pipeline-wiring fix).
- [x] P1 (Consumer upgrade flow): Issues #180 + #181 — `upgrade_shell_behavioral_check`: false positives on case-label `|` alternation and array literal bare-words (#180, P1) and `_EXCLUDED_TOKENS` incomplete — blueprint runtime functions and common OS tools flagged as unresolved (#181, P2); bundle into one work item as they affect the same component. Gate is unreliable until both are resolved. **Done**: `specs/2026-04-24-issue-179-180-181-185-186-187-upgrade-correctness/`
- [x] P1 (Consumer upgrade flow): Issue #179 — `upgrade_reconcile_report`: `conflicts_unresolved` bucket incorrectly includes files that have already been resolved; consumers receive a wrong conflict count and may act on stale data. **Done**: `specs/2026-04-24-issue-179-180-181-185-186-187-upgrade-correctness/`
- [x] P1 (Consumer upgrade flow): Issue #185 — upgrade planner silently skips new blueprint files not enumerated in `required_files` or `blueprint_managed_roots`; uncovered files produce no warning and the validate gate does not enforce coverage. **Done**: `specs/2026-04-24-issue-179-180-181-185-186-187-upgrade-correctness/`
- [x] P1 (Consumer upgrade flow): Issue #186 — `upgrade_fresh_env_gate`: gate passes on exit code only; file-state divergence check between clean worktree and working tree is not implemented, so the gate can report PASS while producing different output files. **Done**: `specs/2026-04-24-issue-179-180-181-185-186-187-upgrade-correctness/`
- [x] P2 (Consumer upgrade flow): Issue #187 — `render_ci_workflow`: generated `ci.yml` omits `permissions:` block; GITHUB_TOKEN inherits implicit write access on orgs with non-restrictive defaults. **Done**: `specs/2026-04-24-issue-179-180-181-185-186-187-upgrade-correctness/`

#### Phase 3 — Reporting and guidance improvements

- [x] P2 (Consumer upgrade flow): Issue #164 — in the upgrade preflight report, list all version pin changes in `versions.sh` between the two tags and map each changed pin to the template files it affects; provide an explicit action item to sync them after `infra-bootstrap` rather than leaving the consumer to discover template drift reactively via `infra-validate`. **Done**: `specs/2026-04-26-issue-164-upgrade-version-pin-report/`, PR #195.
- [ ] proposal(issue-164): automated template sync (`BLUEPRINT_UPGRADE_SYNC_TEMPLATES=true`) after version pin changes — https://github.com/sbonoc/stackit-platform-blueprint/issues/196
- [ ] (parked) proposal(issue-164): value-based template scanning — detect hardcoded version strings in templates, not just variable name references
      trigger: on-scope: blueprint
      rationale: variable-name grep covers the common case; value scanning is a deeper semantic problem (false positives, multi-format strings) — surfaces naturally when template scanning scope is next touched
- [x] P2 (Consumer upgrade flow): Issue #165 — enrich merge-required plan entries with semantic annotations describing what changed in each file and what the consumer should verify after applying the merge. **Done**: `specs/2026-04-23-issue-165-semantic-annotations/`
- [ ] P2 (Consumer upgrade flow): Issue #183 — `upgrade_consumer_postcheck`: detect when the reconcile report on disk was generated against a different source/target tag pair than the current run and auto-rebuild it rather than silently operating on stale data. *(parked: deterministic pipeline always regenerates the reconcile report in the same run; standalone postcheck usage is the remaining risk surface — trigger: triage: next-session)*
- [ ] P2 (Consumer upgrade flow): Issue #184 — `upgrade_shell_behavioral_check`: make the symbol exclusion set extensible via consumer configuration (e.g. `BEHAVIORAL_CHECK_EXCLUDED_TOKENS` in `versions.sh` or a dedicated config file) so consumers can suppress project-specific false positives without patching blueprint code. Follow-on to #181.

#### Phase 4 — Major UX improvements (build on the stable correctness foundation)

- [x] P2 (Consumer upgrade flow): scripted upgrade pipeline — replace `blueprint-consumer-upgrade` runbook with a deterministic 10-stage pipeline (`make blueprint-upgrade-consumer`); resolves F-001–F-010 from the v1.0.0→v1.6.0 upgrade. **In progress**: `specs/2026-04-25-scripted-upgrade-pipeline/`, PR #193.
- [ ] P2 (Consumer upgrade flow): Issue #167 — add `BLUEPRINT_UPGRADE_DRY_RUN=true` flag that simulates all file mutations (copy, 3-way merge, skip, consumer-owned) and outputs a unified diff of the full change set without touching the working tree; reports the same warnings, conflicts, and behavioral failures the real apply would surface so consumers can review the exact change before committing to apply.
- [ ] P2 (Consumer upgrade flow): Issue #168 — add incremental tag-to-tag upgrade mode (`BLUEPRINT_UPGRADE_INCREMENTAL=true`) that applies changes one release at a time, surfacing a per-release changelog and cherry-pick plan at each step with resume support on conflict; batch mode remains the default.

#### v1.7.0 upgrade findings (pipeline correctness gaps)

- [x] P1 (Consumer upgrade flow): Issues #198 + #199 + #205 — four latent pipeline gaps uncovered during v1.7.0 adoption: (1) `blueprint-template-smoke` absent from `VALIDATION_TARGETS`; (2) `infra-argocd-topology-validate` absent from `VALIDATION_TARGETS`; (3) `apps/catalog*` paths not in `ownership_path_classes`, causing false-positive "uncovered file" warnings; (4) `resolve_contract_upgrade.py` uses bare `yaml.dump()`, producing indentless sequences and wrapped scalars that break `parse_yaml_subset`. **Done**: `specs/2026-04-26-issue-198-199-upgrade-coverage-gaps/`, PR #202.
- [x] P2 (Consumer upgrade flow): Issues #203 + #204 — **Done**: `specs/2026-04-27-issue-203-204-upgrade-apply-correctness/`, PR #212. (1) #203: generalise prune guard beyond `base/apps/` via `_is_kustomization_referenced` — checks consumer kustomization.yaml refs before any delete; supersedes the earlier app-descriptor prune-safety motivation noted below. (2) #204: post-merge Terraform block deduplication via `_tf_deduplicate_blocks` — auto-deduplicates byte-identical blocks, emits conflict artifact for non-identical ones.
- [x] P2 (Consumer upgrade flow): consumer app descriptor (`apps/descriptor.yaml`, `consumer_seeded`) — **Done**: `specs/2026-04-27-consumer-app-descriptor/`, PR #213. Declares app/component topology, owner team, service ports, health checks, and explicit manifest refs in a schema-validated, upgrade-safe file seeded by `blueprint-init-repo` and owned by the consumer thereafter. Blueprint validates descriptor refs against `infra/gitops/platform/base/apps/kustomization.yaml`, renders `apps/catalog/manifest.yaml` only as a deprecated compatibility artifact for two blueprint minor releases, and emits `artifacts/blueprint/app_descriptor.suggested.yaml` for existing consumers without silently writing it during upgrade apply. Upgrade prune classifies descriptor-listed paths as `consumer-app-descriptor` ahead of the deprecated `_is_consumer_owned_workload()` bridge guard and the kustomization-ref fallback; both deprecated guards remain for two blueprint minor releases (decommission triggers tracked below as `after: consumer-app-descriptor-adoption`).
- [ ] (parked) decommission: remove deprecated generated `apps/catalog/manifest.yaml` compatibility artifact after the consumer app descriptor migration window.
      trigger: after: consumer-app-descriptor-adoption
      rationale: `apps/descriptor.yaml` becomes the canonical app metadata source; keeping generated catalog output forever would create duplicate contract surfaces.
- [ ] (parked) decommission: remove deprecated `_is_consumer_owned_workload()` bridge guard after descriptor adoption becomes mandatory or two blueprint minor releases have passed, whichever is later.
      trigger: after: consumer-app-descriptor-adoption
      rationale: descriptor ownership and kustomization-ref fallback supersede the path-prefix bridge; tracking prevents the bridge from becoming permanent hidden behavior.

#### v1.7.0 upgrade findings (consumer domain boundary violations)

Reported by consumer sbonoc/dhe-marketplace from their v1.7.0 upgrade experience. All three share a root cause: blueprint code hardcodes consumer workload names that belong to the consumer's product domain.

- [x] P1 (Consumer upgrade experience): Issue #208 (bug) — `bootstrap.sh` and `template_smoke_assertions.py` hardcode blueprint seed workload names; consumer topology renames cause `generated-consumer-smoke` CI failures with no local signal. **Done**: `specs/2026-04-26-issue-208-dynamic-workload-derivation/`, PR #209.
- [x] P1 (Consumer upgrade experience): Issue #207 (bug) — upgrade prune deletes consumer workload manifests in `base/apps/` when `BLUEPRINT_UPGRADE_ALLOW_DELETE=true`; `kustomize build` breaks silently post-upgrade. **Done**: `specs/2026-04-26-issue-207-apps-prune-exclusion/`, PR #210.
- [x] P2 (Consumer upgrade experience): Issue #206 (enhancement) — `app_runtime_gitops_contract` hardcodes workload manifest names in `required_files` and `required_paths_when_enabled`; consumer must re-patch the contract after every upgrade. **Done**: `specs/2026-04-26-issue-206-contract-consumer-owned-workloads/`, PR #211.
- [ ] (parked) proposal(issue-206): source-only seed change advisory in upgrade plan — when a file reclassified to `source_only` (e.g. the four seed workload manifests from #206) has changed content between the previous and current blueprint tag, the upgrade planner MUST emit an advisory plan entry that (a) identifies the file, (b) shows a unified diff of what blueprint changed, and (c) instructs the consumer/agent to review and decide whether to apply the delta manually. Without this, the plan silently shows `source-only / skip` with no signal that blueprint improved the seed content (e.g. added health probes, security contexts, resource limits) — the consumer has no way to notice and no guidance on what to do. This is the necessary long-term companion to Option A from ADR-2026-04-26-issue-206; Option A is the correct minimal fix but becomes unsafe over time without this advisory layer. Conceptually analogous to issue #165 (semantic annotations for merge-required entries) applied to source-only files. Prerequisite: #206 implementation shipped.
      trigger: on-scope: blueprint
      rationale: surfaces naturally when blueprint maintainers next improve seed workload content (health probes, security contexts, resource limits) or when a consumer reports silently missing a seed update after upgrade

#### v1.8.0 upgrade findings (dhe-marketplace v1.7.0 → v1.8.0)

Reported by consumer sbonoc/dhe-marketplace from their v1.7.0→v1.8.0 upgrade experience. All three are genuine v1.8.0 defects fixed in v1.8.1. Consumer workarounds in place until 2026-07-27.

- [x] P1 (Consumer upgrade experience): Issues #214 + #215 (bug) — **Done**: `specs/2026-04-27-issue-214-215-source-only-glob-and-validate/`, PR #226. Group A: `audit_source_tree_coverage` now counts prune-glob matched files as covered via `fnmatch`; `_validate_absent_files` uses `is_file()` instead of `exists()` and supports glob/directory-prefix entries.
- [ ] proposal(issue-214-215): add validator warning for `**` in source_only glob entries (fnmatch limitation) — https://github.com/sbonoc/stackit-platform-blueprint/issues/229
- [x] P1 (Consumer upgrade experience): Issue #216 (bug) — **Done**: `specs/2026-04-27-issue-216-upgrade-source-only-filter/`, PR #227. Group B: Stage 3 `_filter_source_only` Phase 1+2 restored — drops source entries whose paths exist on disk in consumer; carries forward consumer-added entries.
- [x] P1 (Consumer upgrade experience): Issue #217 (bug) — **Done**: `specs/2026-04-27-issue-217-template-descriptor-kustomization-sync/`, PR #228. Group C: `template_smoke_assertions.py` cross-checks descriptor manifest filenames against kustomization resources; drift caught at template-edit time with named AssertionError.
- [ ] (parked) proposal(issue-217): extract `_assert_descriptor_kustomization_agreement` as shared module helper for future smoke scenario reuse
      trigger: on-scope: blueprint
      rationale: no additional callers exist today; surfaces when the next blueprint smoke scenario is developed

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

## Platform Module Candidates
- [ ] Issue #171 — managed-cache module: STACKIT Managed Redis as a first-class optional module (Helm/ArgoCD-managed); provider-backed via official STACKIT Terraform resources.
- [ ] Issue #172 — platform-email module: Helm/ArgoCD-managed Postal for transactional email as an optional module alongside existing platform modules.

## Provider-Backed STACKIT Expansion Candidates
- [ ] Evaluate and add a provider-backed Redis module built on official STACKIT Terraform resources. *(tracked as Issue #171 — see Platform Module Candidates above)*
- [ ] Evaluate and add provider-backed relational/NoSQL data-service modules for the currently available STACKIT Terraform resources (`mariadb`, `mongodbflex`, `sqlserverflex`).
- [ ] Evaluate and add a provider-backed Logs/LogMe module or baseline observability extension using official STACKIT Terraform resources.
- [ ] Evaluate and add a provider-backed File Storage module using STACKIT SFS Terraform resources.
- [ ] Evaluate whether STACKIT Application Load Balancer, CDN, and Public IP resources should become first-class edge modules alongside or instead of the current Gateway API baseline.
- [ ] Evaluate whether STACKIT network and security primitives (`network`, `network_area`, `routing_table`, `security_group`) should become first-class foundation capabilities in this blueprint.
- [ ] Evaluate whether STACKIT identity/project primitives (`service_account`, role assignments, Resource Manager folders/projects) should become blueprint-managed bootstrap/foundation capabilities.
- [ ] Evaluate whether STACKIT compute-oriented primitives (`server`, `volume`, `edgecloud`, `modelserving`) belong in blueprint scope for future workload patterns.
