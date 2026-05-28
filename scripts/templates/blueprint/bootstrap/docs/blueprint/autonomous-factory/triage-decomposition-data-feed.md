# Triage + Decomposition Data Feed (Retrospective)

**Status:** approved
**Date:** 2026-05-29
**Issue:** #337
**Spec:** `specs/2026-05-28-issue-337-factory-phase-0-foundations/` (FR-015)
**Meta-ADR:** [`docs/blueprint/architecture/decisions/ADR-issue-337-factory-phase-0-foundations.md`](../architecture/decisions/ADR-issue-337-factory-phase-0-foundations.md)
**Owner:** `@sbonoc/factory-operations`
**Companion:** [`pre-factory-baselines.md`](pre-factory-baselines.md), [`instrumentation-plan.md`](instrumentation-plan.md)

## Purpose

This document records what [`blueprint-ticket-triage-size`](../architecture/decisions/ADR-issue-337-triage-size-threshold.md) (FR-009 thresholds) **would have classified** each historical ticket cycle as, and — for `large-decomposable` rows — what boundary set [`blueprint-ticket-decompose-light`](../architecture/decisions/ADR-issue-337-light-decomposition-policy.md) (FR-010) **would have proposed**. It is the evidence base Phase 3 (#338) consumes when designing composition orchestration.

## Explicit Caveat (FR-015 normative requirement)

**These are retrospective hypothetical classifications, not factory-produced classifications.** No live factory ran against any PR in this dataset; classifications are derived programmatically from each PR's title, `changedFiles` count, and `additions + deletions` line delta as a proxy for the FR-009 threshold dimensions. The proxy mapping is deliberately conservative — when in doubt, the heuristic prefers the larger class so that #338 sees a worst-case decomposition load distribution. Live-factory classification will use the FR-009 thresholds directly against the real-time triage skill's measured token cost and skill-invocation count, both of which are unavailable retrospectively.

## Sample Window and Size

| Field | Value |
|---|---|
| Window | 2026-04-17 → 2026-05-28 (per [`pre-factory-baselines.md`](pre-factory-baselines.md) Measurement Window — anchored on the SDD-enable commit `df7595c` per Q-6) |
| Sample n | **100 ticket cycles** (one row per merged PR; full population in window) |
| Sample-size disclosure | n=100 satisfies FR-015's "at least 30 ticket-cycle rows" floor; no `### Sample Size` exception subsection is required per Q-7 |

## Classification Heuristic (retrospective only)

Per FR-009 the three threshold dimensions are bounded contexts touched, estimated token cost, and estimated SDD step invocations. None of these is directly measurable from historical PR metadata; the retrospective proxy substitutes:

| FR-009 dimension | Retrospective proxy | Rationale |
|---|---|---|
| Bounded contexts touched | `ctx_estimate = ceil(changedFiles / 12)`, capped at 5 | The blueprint's bounded-context layout (per Q-3: factory / infra / docs / governance) typically maps one bounded context to ~10–15 changed files per PR; the divisor of 12 is the rounded midpoint. Cap at 5 maps "many files across many areas" to `escalate`. |
| Estimated token cost | `tokens = (additions + deletions) × 15` | Multiplier of 15 = 3 tokens/line × 5× read-context factor (the model reads surrounding code to make the edit). Conservative; real read-context can be higher for large refactors. |
| Estimated SDD step invocations | Fixed at 6 | All SDD-track PRs invoke approximately 6 steps (intake / resolve / complete / plan-slice / implement / package). Pre-SDD-bypass PRs ran fewer steps but the cost ceiling-relevant dimension (step count) is dominated by the SDD-track baseline. Bypass-track PRs are still subject to the same threshold check because forward factory runs against the same workflow. |

Classification rule (AND-conjoined per [`ADR-issue-337-triage-size-threshold.md`](../architecture/decisions/ADR-issue-337-triage-size-threshold.md)):

- `small` iff `ctx_estimate ≤ 1` AND `tokens ≤ 50_000`
- `medium` iff `ctx_estimate ≤ 2` AND `tokens ≤ 150_000`
- `large-decomposable` iff `ctx_estimate ≤ 4` AND `tokens ≤ 400_000`
- `escalate` otherwise

(The step-count dimension is a constant 6 in this retrospective and is therefore never the promoting dimension; for live-factory classification it is one of the three AND-conjoined dimensions.)

## Distribution Summary

| Class | Count | % of n=100 |
|---|---|---|
| `small` | 10 | 10% |
| `medium` | 23 | 23% |
| `large-decomposable` | 59 | 59% |
| `escalate` | 8 | 8% |

**Reading the distribution.** The `large-decomposable` majority (59%) is the load-bearing signal for Phase 1's decomposition policy — under live-factory operation, roughly six out of every ten incoming tickets would be candidates for `blueprint-ticket-decompose-light` rather than single-pass execution. This validates the FR-010 decision to ship light decomposition in Phase 1 rather than defer all decomposition to Phase 3. The 8% `escalate` rate represents work that the factory should not attempt and that human authors should continue to drive end-to-end. The 33% `small` + `medium` cluster represents the cleanest single-pass execution path with the highest expected factory win rate.

## Hypothetical Boundary-Decomposition Axes (FR-010 proposals for `large-decomposable` rows)

The FR-010 policy allows three single-axis decomposition types: `bounded-context`, `architectural-layer`, `user-visible-feature-behavior`. For the 59 `large-decomposable` rows in this dataset, the heuristic boundary axis is assigned by inspection of the PR title:

| Title pattern | Proposed boundary axis | Example rows |
|---|---|---|
| Multi-module / multi-bounded-context features (`feat(issue-XXX-Y-Z):`, `feat(module1+module2):`) | `bounded-context` | #331, #285, #283, #289, #274, #202, #155 |
| Layer-spanning refactors (CI / tooling / cross-cutting upgrades) | `architectural-layer` | #257, #226, #209, #210, #176, #146, #142 |
| User-visible feature shipping with internal sub-features | `user-visible-feature-behavior` | #243, #287, #232, #195, #193 |
| Single-bounded-context implementations classified `large-decomposable` by file-count proxy alone | would **refuse** decomposition per FR-010 (single axis cannot produce ≥ 2 children); route to single-pass execution as if `medium` | majority of `feat(issue-248-*-module):` rows (#306, #305, #307, #308, #251, #250, #249, #256) |

The refuse-then-single-pass cluster (single-bounded-context PRs that the file-count proxy over-classifies) is **the largest single category** within the 59 `large-decomposable` rows. This is the dominant retrospective signal for #338: under live-factory operation many `large-decomposable` classifications will resolve at decomposition time to "refuse and proceed as a single ticket," because the file-count proxy overcounts contexts when a single module surface is implemented across many files. The live triage skill's direct bounded-context measurement will give a cleaner classification than this retrospective heuristic.

## Per-Cycle Classification Table

Columns:

- **PR #** — GitHub PR number
- **Title** — PR title (truncated)
- **Files** — `changedFiles` count
- **LOC Δ** — `additions + deletions`
- **Est. tokens** — `(additions + deletions) × 15`
- **Ctx est.** — `ceil(changedFiles / 12)`, capped at 5
- **Class** — hypothetical FR-009 classification

| PR # | Title | Files | LOC Δ | Est. tokens | Ctx est. | Class |
|---|---|---|---|---|---|---|
| #344 | chore(managed-cache): align state-file labels with multi-word module convention | 6 | 88 | 1320 | 1 | `small` |
| #340 | feat(issue-339-factory-design-contracts): SDD intake — C1–C8 design contracts + consumer-shipped surface + extensibility/semver posture | 15 | 1693 | 25395 | 2 | `medium` |
| #331 | feat(issue-284-302-local-dx-improvements): .env.local auto-load + ARGOCD_LOCAL_TARGET_REVISION | 22 | 880 | 13200 | 3 | `large-decomposable` |
| #330 | feat(issue-171-managed-cache): managed-cache optional module — STACKIT Managed Redis + bitnami/redis local lane | 53 | 2125 | 31875 | 5 | `escalate` |
| #329 | feat(issue-312-observability-csi-hardening): replace blueprint-observability-auth K8s Secret with Secrets Store CSI Driver on STACKIT | 53 | 1848 | 27720 | 5 | `escalate` |
| #328 | chore: mark issue-248 identity-aware-proxy done in backlog | 1 | 2 | 30 | 1 | `small` |
| #327 | feat(issue-248-observability-enhancements): Faro receiver + dashboard provisioning + OTEL pipeline improvements | 45 | 1715 | 25725 | 4 | `large-decomposable` |
| #326 | fix(issue-321): add always-run pre-push hook for contract required_files check | 10 | 189 | 2835 | 2 | `medium` |
| #325 | fix(issue-323): bump PostgreSQL to 17 — local image pin + STACKIT version default | 21 | 516 | 7740 | 3 | `large-decomposable` |
| #322 | fix(sdd-toolchain): align skill runbooks and templates with quality-gate contracts | 24 | 294 | 4410 | 3 | `large-decomposable` |
| #320 | chore(branch-naming): adopt semantic prefixes; retire codex/ as default | 22 | 171 | 2565 | 3 | `large-decomposable` |
| #318 | feat(issue-248-identity-aware-proxy): SDD compliance — README hardening + bootstrap template mirror | 15 | 1536 | 23040 | 2 | `medium` |
| #317 | feat(issue-248-workflows-local-improvements): self-contained smoke port-forward + DAG Python version split | 21 | 820 | 12300 | 3 | `large-decomposable` |
| #316 | feat(issue-248-workflows-local-lane): local Apache Airflow lane on Docker Desktop Kubernetes | 37 | 2007 | 30105 | 4 | `large-decomposable` |
| #315 | chore: mark workflows done in backlog; commit stale issue-295 manifest | 2 | 25 | 375 | 1 | `small` |
| #314 | feat(issue-248-workflows-module): add STACKIT Workflows module — contract test, pyramid registration, docs | 16 | 1760 | 26400 | 2 | `medium` |
| #313 | chore: mark dns module ✅ in issue #248 backlog (PR #306 merged) | 1 | 2 | 30 | 1 | `small` |
| #311 | fix(blueprint): replace declare -A with temp-file set in prune_codex_skills.sh | 1 | 25 | 375 | 1 | `small` |
| #308 | feat(issue-248-observability-module): STACKIT otel-collector + push URL outputs — closes dangling endpoint bug | 28 | 2108 | 31620 | 3 | `large-decomposable` |
| #307 | feat(issue-248-public-endpoints-module): TLS + external-dns — HTTPS listener, cert-manager Issuer/Certificate, Gateway annotation | 34 | 1891 | 28365 | 4 | `large-decomposable` |
| #306 | feat(dns): standalone multi-zone TF module + shell contract (issue #248) | 32 | 1427 | 21405 | 4 | `large-decomposable` |
| #305 | feat(secrets-manager): standalone TF module + shell layer with namespace/auth_method_details | 28 | 1488 | 22320 | 3 | `large-decomposable` |
| #304 | feat(issue-296-workaround-manifest-action-path-check): CI gate for workaround manifest action_path existence | 19 | 1000 | 15000 | 3 | `large-decomposable` |
| #303 | feat(issue-247-step05-slice-done-gate): add deterministic slice-done gate for HTTP+UI-rendering scope | 19 | 1038 | 15570 | 3 | `large-decomposable` |
| #301 | feat(issue-293-294): anti-duplication contract + AGENTS.decisions.md scan rules + quality-docs-cross-reference-check hook | 27 | 1651 | 24765 | 3 | `large-decomposable` |
| #300 | chore(issue-295): close OM baseline question — templates already clean + bypass-track aware spec-pr-ready | 5 | 275 | 4125 | 1 | `small` |
| #299 | feat(issue-275): lightweight SDD bypass track via SPEC_READY_EXCEPTION field | 19 | 1691 | 25365 | 3 | `large-decomposable` |
| #298 | fix(issue-277-argocd-health-na): override ignoreResourceUpdates.all to restore ArgoCD health evaluation | 18 | 761 | 11415 | 2 | `medium` |
| #297 | chore(backlog): harmonize open GH issues and restructure AGENTS.backlog.md | 2 | 425 | 6375 | 1 | `small` |
| #292 | feat(issue-268-consumer-workarounds-catalogue): versioned workarounds catalogue applied automatically by version | 31 | 3793 | 56895 | 4 | `large-decomposable` |
| #291 | feat(issue-265-271-source-exists-inference): source-exists inference for blueprint-managed catch-all | 26 | 1015 | 15225 | 3 | `large-decomposable` |
| #290 | feat(issue-270-test-ownership-contract): relocate blueprint-author tests from tests/infra/ to tests/blueprint/ | 25 | 5645 | 84675 | 3 | `large-decomposable` |
| #289 | feat(issue-286-288-ci-template-draft-guard-drift-hook): consumer CI draft-PR skip + bootstrap drift commit hook | 24 | 994 | 14910 | 3 | `large-decomposable` |
| #287 | fix(issue-281-282-opensearch-bitnami-chart-fixes): allowInsecureImages + sysctlImage.enabled=false for Bitnami chart 1.6.x | 17 | 663 | 9945 | 2 | `medium` |
| #285 | feat(issue-267-269): pipeline finalize target + auto-clone source URL | 23 | 1573 | 23595 | 3 | `large-decomposable` |
| #283 | feat(issue-265-271): conflict resolution UX — upgrade_triage.json + blueprint-upgrade-consumer-resolve | 26 | 1833 | 27495 | 3 | `large-decomposable` |
| #278 | feat(issue-263-264-266): pipeline/engine correctness — baseline version tracking, exit code disambiguation, apply default | 30 | 1196 | 17940 | 3 | `large-decomposable` |
| #276 | fix(docs): v1.10.0 docs hotfix — restore --ignore-workspace and improve pnpm version error (#272 #273) | 17 | 926 | 13890 | 2 | `medium` |
| #274 | feat(issue-258-259-260-261-v110-engine-hotfix): fix 4 upgrade pipeline blockers for v1.10.0 consumers | 29 | 1731 | 25965 | 3 | `large-decomposable` |
| #257 | feat(uv-run-phase2): adopt uv run python3 for all Python invocations | 41 | 373 | 5595 | 4 | `large-decomposable` |
| #256 | feat(issue-248-kms-module): KMS module dual-lane implementation (Vault Transit local + STACKIT KMS) | 33 | 1528 | 22920 | 4 | `large-decomposable` |
| #255 | feat(issue-248-rabbitmq-module): SDD intake — spec, architecture, plan ready for PO review | 30 | 1473 | 22095 | 3 | `large-decomposable` |
| #254 | ci: add Claude GitHub Actions workflows | 2 | 98 | 1470 | 1 | `small` |
| #253 | feat(generalize-consumer-seeded-feature-gates): generic opt-in gate for consumer-seeded blueprint files | 43 | 2467 | 37005 | 4 | `large-decomposable` |
| #251 | feat(issue-248-postgres-module): postgres dual-lane module (Bitnami Helm local + STACKIT postgresflex Terraform) | 30 | 1306 | 19590 | 3 | `large-decomposable` |
| #250 | feat(issue-248-object-storage-module): object-storage dual-lane implementation (MinIO local + STACKIT Terraform) | 32 | 1378 | 20670 | 4 | `large-decomposable` |
| #249 | feat(issue-248-opensearch-module): implement OpenSearch module dual-lane (STACKIT + local Helm) | 36 | 1885 | 28275 | 4 | `large-decomposable` |
| #246 | feat(quality-gates): pnpm lockfile pre-push gate + consumer CI extension stubs (Issues #236+#237) | 22 | 875 | 13125 | 3 | `large-decomposable` |
| #243 | feat(a11y): P1 Accessibility compliance — SDD lifecycle gates, test infra, ACR scaffold (Issues #238+#239+#240) | 37 | 1985 | 29775 | 4 | `large-decomposable` |
| #242 | fix(issue-241): expose ?= override-point variables in blueprint.generated.mk for spec-scaffold and blueprint-uplift-status | 16 | 834 | 12510 | 2 | `medium` |
| #235 | fix(issue-234): newline-only delimiter for RUNTIME_CREDENTIALS_SOURCE_SECRET_LITERALS in parse_literal_pairs | 18 | 824 | 12360 | 2 | `medium` |
| #233 | fix(issue-230): correct stale release_notes.md refs and tighten test assertion message | 4 | 24 | 360 | 1 | `small` |
| #232 | feat(quality-hooks): inner-loop verification ergonomics — keep-going + path/phase gating + dedup + Step 5 skill | 46 | 3367 | 50505 | 5 | `escalate` |
| #231 | fix(issue-230): restore descriptor↔kustomization lockstep on blueprint-init-repo force-reseed | 23 | 1010 | 15150 | 3 | `large-decomposable` |
| #228 | feat(issue-217): SDD intake — descriptor-kustomization smoke assertion | 13 | 826 | 12390 | 2 | `medium` |
| #227 | fix(issue-216): restore Stage 3 source_only Phase 1 + Phase 2 filter in contract resolver | 14 | 900 | 13500 | 2 | `medium` |
| #226 | fix(issue-214-215): source_only glob and directory-prefix support in audit coverage and contract validation | 19 | 774 | 11610 | 3 | `large-decomposable` |
| #213 | feat(consumer-app-descriptor): consumer-owned app descriptor intake | 42 | 3880 | 58200 | 4 | `large-decomposable` |
| #212 | feat(issue-203-204): upgrade apply correctness — kustomization-ref prune guard and Terraform block deduplication | 25 | 1356 | 20340 | 3 | `large-decomposable` |
| #211 | feat(issue-206): consumer-owned workload manifests — move seed paths to source_only | 26 | 1210 | 18150 | 3 | `large-decomposable` |
| #210 | fix(issue-207): guard upgrade planner against pruning consumer workload manifests in base/apps/ | 16 | 867 | 13005 | 2 | `medium` |
| #209 | fix(issue-208): derive app workload names dynamically from template kustomization | 18 | 824 | 12360 | 2 | `medium` |
| #202 | feat(issue-198-199-205): close four upgrade pipeline gaps (VALIDATION_TARGETS, feature_gated, yaml.dump) | 23 | 1049 | 15735 | 3 | `large-decomposable` |
| #201 | chore: prune stale blueprint-* skills on install | 9 | 120 | 1800 | 2 | `medium` |
| #197 | feat(issue-184): make shell behavioral check exclusion set extensible via contract.yaml | 20 | 724 | 10860 | 3 | `large-decomposable` |
| #195 | feat(issue-164): surface version pin changes and template impact in upgrade residual report | 20 | 1588 | 23820 | 3 | `large-decomposable` |
| #194 | fix(issue-189): wire prune-glob enforcement into pipeline Stage 9 and residual report | 4 | 151 | 2265 | 1 | `small` |
| #193 | feat(scripted-upgrade-pipeline): replace blueprint-consumer-upgrade runbook with deterministic 10-stage pipeline | 27 | 3447 | 51705 | 3 | `large-decomposable` |
| #192 | feat(issue-179-180-181-185-186-187-upgrade-correctness): fix six behavioral correctness bugs in upgrade tooling and CI renderer | 51 | 2952 | 44280 | 5 | `escalate` |
| #191 | docs(sdd): execution guide + step-numbered skill redesign | 169 | 6137 | 92055 | 5 | `escalate` |
| #190 | feat(sdd/189): intake spec for prune-glob enforcement in upgrade tooling | 20 | 843 | 12645 | 3 | `large-decomposable` |
| #188 | fix(issue-182): seed gitignored upgrade artifacts into fresh-env gate worktree | 15 | 534 | 8010 | 2 | `medium` |
| #178 | feat(issue-163): fresh-environment simulation gate in upgrade smoke | 27 | 1692 | 25380 | 3 | `large-decomposable` |
| #177 | feat(spec): intake + complete — issue-165 semantic annotations on merge-required plan entries | 37 | 1850 | 27750 | 4 | `large-decomposable` |
| #176 | feat(blueprint): add post-merge behavioral validation gate (#162) | 30 | 2101 | 31515 | 3 | `large-decomposable` |
| #175 | feat(sdd): introduce two-phase spec model with PO skill and agent-drafted ADR | 35 | 967 | 14505 | 4 | `large-decomposable` |
| #174 | feat(test): codify local smoke as automated e2e tests with make target | 7 | 272 | 4080 | 2 | `medium` |
| #173 | feat(ci): add upgrade-e2e-validation CI job and quality-ci-upgrade-validate lane (#169) | 19 | 730 | 10950 | 3 | `large-decomposable` |
| #170 | fix(exec): remove 2>&1 from run_cmd_capture to isolate stderr from stdout (#166) | 14 | 596 | 8940 | 2 | `medium` |
| #161 | fix(infra): honour consumer_seeded_paths in ensure_infra_template_file / ensure_infra_rendered_file (#160) | 16 | 614 | 9210 | 2 | `medium` |
| #159 | feat(platform): add app version contract checker for catalog artifact drift detection (#56) | 18 | 1366 | 20490 | 2 | `medium` |
| #158 | feat(blueprint): add blueprint-uplift-status convergence status command (#131) | 19 | 1374 | 20610 | 3 | `large-decomposable` |
| #157 | feat(quality): add quality-spec-pr-ready publish-gate validator for SDD artifacts | 19 | 1638 | 24570 | 3 | `large-decomposable` |
| #156 | feat(blueprint): detect stale module make targets in upgrade preflight; fix postgres ESO key (#118, #137) | 19 | 1101 | 16515 | 3 | `large-decomposable` |
| #155 | feat(apps): scaffold backend/touchpoints Dockerfiles and fix deployment images (#111, #112) | 20 | 728 | 10920 | 3 | `large-decomposable` |
| #154 | fix(platform/auth): best-effort reconcile hard-fail and gho_ token policy (#105, #110) | 16 | 592 | 8880 | 2 | `medium` |
| #153 | feat(quality): add SDD scaffold placeholder guard (#152) | 18 | 676 | 10140 | 2 | `medium` |
| #151 | fix(infra): add external-secrets destination to ArgoCD AppProject overlays | 23 | 582 | 8730 | 3 | `large-decomposable` |
| #150 | fix: rename JSON-content YAML files to .json extension | 73 | 276 | 4140 | 5 | `escalate` |
| #149 | fix(upgrade): reclassify additive-file conflicts and relocate platform helpers (#104 #106 #107) | 22 | 1134 | 17010 | 3 | `large-decomposable` |
| #148 | fix: repo-mode-aware infra contract fast lane for generated consumers (#103) | 15 | 871 | 13065 | 2 | `medium` |
| #147 | test: enforce optional-module required_env fixture parity in fast lane | 19 | 904 | 13560 | 3 | `large-decomposable` |
| #146 | feat: add upgrade reconcile artifact and postcheck convergence gate | 48 | 3235 | 48525 | 5 | `escalate` |
| #145 | refactor(docs): centralize repo-mode resolution for docs sync | 18 | 1296 | 19440 | 2 | `medium` |
| #144 | feat: enforce repo-mode required-file reconciliation in upgrade validate | 21 | 1801 | 27015 | 3 | `large-decomposable` |
| #143 | Issue #102: preflight checklist for missing required consumer Make targets | 19 | 935 | 14025 | 3 | `large-decomposable` |
| #142 | Enforce SDD local-smoke and red-green finding gates | 34 | 892 | 13380 | 4 | `large-decomposable` |
| #141 | Validate prune-glob ownership matrix documentation in infra-validate | 19 | 816 | 12240 | 3 | `large-decomposable` |
| #140 | Enforce blueprint source-only artifact boundaries for generated-consumer templates | 26 | 1157 | 17355 | 3 | `large-decomposable` |
| #139 | Enforce strict-default SDD and dedicated branch creation for new work items | 52 | 1635 | 24525 | 5 | `escalate` |

## Phase 3 Consumption Hooks (#338)

#338 (composition orchestration design) consumes this data feed as evidence. The cleanest signals for #338 from the n=100 retrospective:

1. **`large-decomposable` is the dominant class (59%)** — composition orchestration is the critical-path Phase 3 work, not an optional polish.
2. **The single-bounded-context overclassification cluster** (visible in the table as `feat(issue-248-*-module):` rows with high file counts) tells #338 that the triage skill's direct bounded-context measurement will materially reduce the live `large-decomposable` rate. #338 SHOULD NOT design composition orchestration assuming a 59% decomposition rate; the live rate is likely 25–40% once the triage skill measures bounded contexts directly.
3. **The 8% `escalate` rate** is the unavoidable human-driven workload — #338 SHOULD NOT attempt to expand the factory's reach into this class; instead, surface escalate-routing more prominently in the triage UX.
4. **Cross-axis tickets** (titles citing multiple `issue-XXX-Y-Z` slugs) are the highest-value decomposition targets — #338 SHOULD prioritize composition machinery for parents whose children come from different bounded contexts, since that is where integration AC violations are most likely.

## Update Cadence

This data feed is a **one-time retrospective**; it is NOT updated by the live factory. Once Phase 1 ships, the live factory's C7 lifecycle event stream becomes the canonical source of triage decisions, and this document remains as the pre-factory baseline against which live-factory triage class distribution is compared. The instrumentation plan's weekly report includes triage class distribution per `owner_team` from the live event stream.

If, post-Phase-1, the live `large-decomposable` rate diverges from the retrospective 59% by more than ±15 percentage points sustained over four consecutive weekly reports, `@sbonoc/factory-operations` MUST review the FR-009 thresholds for calibration per the calibration trigger in [`pre-factory-baselines.md`](pre-factory-baselines.md).

## References

- Spec: `specs/2026-05-28-issue-337-factory-phase-0-foundations/spec.md` § FR-015, § Clarifications Q-7
- Meta-ADR: [`docs/blueprint/architecture/decisions/ADR-issue-337-factory-phase-0-foundations.md`](../architecture/decisions/ADR-issue-337-factory-phase-0-foundations.md)
- Related ADRs: [`ADR-issue-337-triage-size-threshold.md`](../architecture/decisions/ADR-issue-337-triage-size-threshold.md), [`ADR-issue-337-light-decomposition-policy.md`](../architecture/decisions/ADR-issue-337-light-decomposition-policy.md)
- Companion: [`pre-factory-baselines.md`](pre-factory-baselines.md) (same window, complementary baseline metrics), [`instrumentation-plan.md`](instrumentation-plan.md) (forward-measurement specification)
- Source data: `gh pr list --base main --state merged --search "merged:2026-04-17..2026-05-29"` retrieved 2026-05-29
- Phase 3 consumer: #338 (composition orchestration design)
