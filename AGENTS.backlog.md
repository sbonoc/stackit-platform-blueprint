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
| `c7-emission` | C7 lifecycle event emission surface: emitters, schema, JSONL sink, ingest, Grafana facets |
| `a11y` | Accessibility conformance, WCAG gates, ACR scaffold, axe tooling |
| `local-dx` | Local developer experience: `.env.local` auto-load, ArgoCD branch tracking, cluster context overrides |
| `factory` | Autonomous software factory: orchestrator, expert panel, cost telemetry, routing, C7 lifecycle |

---

## Active Work

### P1 — Next Up (priority order confirmed 2026-05-15)

- [x] P1 (Architecture gate): Issue #295 — CLOSED 2026-05-15. Audit confirmed blueprint templates contain no OpenMetadata content; `AGENTS.decisions.md` already records the architectural decision (OM is consumer/product-owned). No template changes required.
- [x] P1 (Bug — ArgoCD health): Issue #277 — CLOSED. `ignoreResourceUpdates.all` `/status` rule narrowed; health reporting restored. Merged PR #298.
- [x] P1 (SDD governance): Issue #275 — CLOSED. Lightweight bypass track shipped. Merged PR #299.
- [x] P1 (Quality tooling): Issues #293 + #294 — CLOSED. Three-layer AGENTS.md ↔ north_star.md anti-duplication contract shipped. Merged PR #301.
- [ ] (parked) proposal(issue-293-294-agents-north-star-cross-reference): Option B — body-heuristic duplication detection
      trigger: on-scope: quality
      rationale: OPTION_A (exact heading match) selected in spec as the starting point; Option B adds false-positive risk before consumer feedback on Option A is gathered.
- [ ] (parked) normative-keyword-allowlist-enforcement: `contract.yaml normative_language.allowed_keywords` declares MUST / MUST NOT / SHALL / EXACTLY ONE OF as the only permitted terms, but `check_sdd_assets.py` only rejects forbidden ambiguous terms — it does not validate that only the allowed keywords are used. A spec using WILL or REQUIRED passes today.
      trigger: on-scope: quality
      rationale: low-priority hardening; forbidden-terms check catches most violations; allowlist check risks false positives on legacy specs
- [ ] (parked) scaffold-token-gate: `check_spec_pr_ready.py` rejects empty `\d+. Slice N:` lines but does not reject unfilled `<describe ...>` scaffold tokens left in slices, risks, or deferred-proposals placeholders. A contributor can leave scaffold text untouched and pass the PR-ready gate.
      trigger: on-scope: quality
      rationale: Step01 Guardrail #1 ("stubs and placeholder text are not acceptable") provides the agent/human-facing control; adding `<describe` rejection requires check-script changes and test updates. Validate tradeoff after observing real-world scaffold misuse.
- [ ] (parked) app-onboarding-impact-gate: `_check_plan` in `check_spec_pr_ready.py` only rejects the literal `no-impact | impacted (select one)` text. It does not enforce that `no-impact` is changed to `impacted` when the work item adds or changes make targets. Templates now seed `no-impact` with a `Notes:` guidance line; a harder gate would heuristically inspect make targets touched.
      trigger: on-scope: quality
      rationale: heuristic detection of "app-delivery changes" is ambiguous; guidance text in the template Notes field provides a softer control. Validate tradeoff after observing real-world misuse.

- [x] (done) Issue #312 — Observability CSI hardening: replace `blueprint-observability-auth` K8s Secret with Secrets Store CSI Driver delivery from STACKIT Secrets Manager. Closed by PR #329. — https://github.com/sbonoc/stackit-platform-blueprint/issues/312

- [x] (done) P1 (Quality tooling): Issue #353 — V-gate E2E classification enforcement: `_check_vgate_classification` in `check_sdd_assets.py`; two new spec fields (`has-user-facing-flow`, `E2E gate classification`); step01 shift-left inference; AGENTS.md Playwright three-MUSTs rule. Closed by PR #357. — https://github.com/sbonoc/stackit-platform-blueprint/pull/357

- [ ] P1 (Factory — Epic #332 Child A): Issue #360 — **IN REVIEW** (PR #362 ready for review, 0 deferred proposals). Author 10 factory personas + 10 SDD/factory skill runbooks + retroactive `## Required Output Schema` backfill on 8 existing SDD skills + CLAUDE.md step08 slash-command row. Spec: `specs/2026-06-02-issue-360-factory-personas-skills/`. Branch: `feature/2026-06-02-issue-360-factory-personas-skills`. — https://github.com/sbonoc/stackit-platform-blueprint/pull/362

- [ ] **FUTURE (Factory — Epic #332, blocked_by: #361)** Issue #369 — **UX/UI expert persona** (9th panel slot). Add a `usability-pragmatist` expert to the factory panel that catches design-system token drift, interaction-pattern regressions, accessibility contract violations, and component-level UX anti-patterns. Pre-conditions: (1) #361 ships conditional dispatch so the expert fires only when `has-user-facing-flow: true` and the diff touches frontend paths — without this gate the expert produces empty verdicts at full token cost on every non-UI work item; (2) push-back triggers are distinct from `product-pragmatist` (which covers scope/value, not visual consistency). Do NOT pick up until condition (1) is met. — https://github.com/sbonoc/stackit-platform-blueprint/issues/369

### P2 — Consumer upgrade flow

- [ ] Issue #167 — dry-run mode (`BLUEPRINT_UPGRADE_DRY_RUN=true`): simulate all file mutations and output a unified diff without touching the working tree; same warnings and conflicts as a real apply.
- [ ] Issue #168 — incremental tag-to-tag upgrade mode (`BLUEPRINT_UPGRADE_INCREMENTAL=true`): apply one release at a time with per-release changelog and resume support on conflict; batch mode remains the default.
- [ ] Issue #183 — stale reconcile report: detect when the report on disk was generated against a different source/target tag pair and auto-rebuild it; standalone postcheck usage is the remaining risk surface.
- [ ] Issue #196 — automated template sync after version pin changes (`BLUEPRINT_UPGRADE_SYNC_TEMPLATES=true`).
- [ ] Issue #218 — move upstream example app names out of `consumer_settings.py` into explicit consumer configuration.
- [ ] Issue #222 — clean stale `artifacts/blueprint/conflicts/` entries after a successful Stage 2 apply.
- [ ] Issue #224 — reconcile bucket policy: do not mark consumer-owned files as blueprint-managed.
- [ ] Issue #225 — guided descriptor adoption target for consumers that pre-date `apps/descriptor.yaml` (new make target to be added).
- [ ] Issue #229 — add validator warning for `**` in `source_only` glob entries (fnmatch limitation).
- [ ] Issue #244 — `consumer_fitness_status.sh` for consumer-side fitness checks (a11y compliance follow-on).
- [ ] Issue #245 — add `layer:` field to `spec.md` template for conditional a11y sections.

### P2 — Blueprint tooling and SDD

- [x] Issue #247 — step-05-implement: add deterministic slice-done gate for HTTP+UI-rendering scope (Guardrails #13, #14, #15 + promoted smoke step + AGENTS.md canonical normative home FR-007–FR-010). Closed by PR #303.
- [x] Issues #284 + #302 — local DX improvements: `ARGOCD_LOCAL_TARGET_REVISION` env var for non-main branch ArgoCD tracking; `.env.local` auto-load in `bootstrap.sh`. Closed by PR #331.
- [ ] (parked) proposal(issue-284-302-local-dx-improvements): encrypt `.env.local` at rest (e.g., `age`/`sops`)
      trigger: on-scope: local-dx
      rationale: adds tooling dependency for a local convenience file; local developer responsibility; no active credential-at-rest risk given gitignore enforcement
- [ ] (parked) proposal(issue-284-302-local-dx-improvements): extend `ARGOCD_LOCAL_TARGET_REVISION` to patch multiple ArgoCD Applications
      trigger: on-scope: gitops
      rationale: only `platform-local-core` is relevant for this pattern; multi-app patching requires a list-based contract that is out of scope here
- [x] Issue #296 — workaround manifest `action_path` CI validation gate. Closed by PR #304.
- [ ] (no issue) Ownership checker robustness: support normalized equivalence for semantically-identical prune-glob expressions in ownership-matrix documentation checks.

### P2 — Platform modules

- [x] Issue #248 remaining modules — STACKIT-managed service candidates (kms ✅, secrets-manager ✅ PR #305, dns ✅ PR #306, public-endpoints ✅ PR #307, observability ✅ PR #308, workflows ✅ PR #314 + local lane ✅ PR #316, identity-aware-proxy ✅ PR #318). Gate on #295 removed — architecture decision recorded in `AGENTS.decisions.md`: OM is consumer/product-owned and not a blueprint module candidate. Issue #248 fully closed.
- [x] Issue #171 — managed-cache module: STACKIT Managed Redis as a first-class optional module (Helm/ArgoCD-managed, provider-backed via STACKIT Terraform). Closed by PR #330.
- [ ] Issue #172 — platform-email module: Helm/ArgoCD-managed Postal for transactional email as an optional module.

---

## Parked Proposals

Surface automatically when the named scope is next touched. Do not promote to active unless the trigger condition is met.

### on-scope: infra

- [ ] proposal(issue-248-dns-module): external-DNS module — K8s-native DNS record management via external-dns controller (analogous to ESO for secrets); surfaces when public-endpoints or ingress TLS work is next in scope.
      rationale: zone-only TF module is the correct separation; record lifecycle belongs in the cluster operator layer; no active consumer need for static record management via stackit_dns_record_set
- [ ] proposal(issue-248-public-endpoints-module): gateway-level HSTS via EnvoyPatchPolicy — inject `Strict-Transport-Security: max-age=31536000; includeSubDomains` on all HTTPS responses at the Envoy listener level using `EnvoyPatchPolicy`; surfaces when Envoy Gateway adds a stable gateway-policy API for response header injection or when EG xDS patch support is confirmed stable for the pinned version.
      rationale: `BackendTrafficPolicy.responseHeaderModifiers` does not exist in EG 1.x CRD; `ClientTrafficPolicy` only handles downstream connection settings; `EnvoyPatchPolicy` is alpha and requires fragile xDS path knowledge; HSTS documented as consumer HTTPRoute responsibility in the interim
- [ ] proposal(issue-248-public-endpoints-module): BackendTLSPolicy (Gateway→Pod encryption) — encrypt east-west traffic from Envoy proxy to backend pods using Envoy Gateway `BackendTLSPolicy`; surfaces when a consumer requires end-to-end TLS or zero-trust east-west encryption.
      rationale: requires per-service TLS provisioning by each consumer; not addressable at the platform module level without consumer participation; deferred until a consumer requests it or a service mesh decision is made
- [ ] proposal(issue-248-public-endpoints-module): OCSP stapling — enable OCSP stapling for production TLS certificates to allow clients to verify revocation status inline without a separate OCSP lookup.
      rationale: no documented Envoy Gateway `ClientTrafficPolicy` support path as of cert-manager v1.20.1; surfaces when Envoy Gateway adds explicit OCSP stapling configuration
- [ ] proposal(issue-248-public-endpoints-module): cert-manager KMS signer plugin — store TLS private keys in STACKIT KMS rather than Kubernetes Secrets using a cert-manager external key manager plugin.
      rationale: unstable plugin ecosystem; no production-ready STACKIT KMS integration for cert-manager signers; surfaces when a stable STACKIT cert-manager KMS plugin is available
- [ ] proposal(issue-248-rabbitmq-module): vhost customisation — per-consumer non-default vhost support.
      rationale: STACKIT provider exposes no vhost attribute; `'/'` is correct for generic use; per-consumer vhost is consumer-side configuration
- [ ] proposal(issue-248-rabbitmq-module): HA replica configuration — `stackit_rabbitmq_instance.replicas > 1`.
      rationale: single-replica default is sufficient; HA requires separate capacity planning and consumer awareness
- [ ] proposal(issue-248-dns-module): DNSSEC `dnssec_enabled` variable — add when `stackit_dns_zone` exposes a `dnssec_enabled` attribute in a future provider version.
      rationale: v0.88.0 does not expose this attribute; STACKIT manages DNSSEC at the platform level; a no-op contract input would mislead consumers
- [ ] proposal(issue-248-kms-module): KMS_KEY_ROTATION_PERIOD input — add when `stackit_kms_key` exposes `rotation_period` attribute in a future provider version.
      rationale: v0.88.0 does not expose this attribute; a no-op contract input would mislead consumers
- [ ] proposal(issue-248-kms-module): Vault HA/persistent storage for local lane — standalone mode with raft storage.
      rationale: dev-mode ephemeral storage is sufficient for local development; HA adds PVC provisioning disproportionate to local dev needs
- [ ] proposal(issue-248-object-storage-module): per-bucket credential scoping via STACKIT `credentials_group`.
      rationale: no active consumer need; surfaces when a consumer requests bucket-scoped access keys
- [ ] proposal(issue-248-object-storage-module): explicit test for object-storage smoke failing when runtime state file is entirely absent.
      rationale: `state_file_exists` has no unit test; smoke absent-state path is currently untested at module level
- [ ] proposal(issue-281-282-opensearch-bitnami-chart-fixes): Bitnami chart 2.x upgrade — targets OpenSearch 3.x, incompatible with 2.17/2.19 image line.
      rationale: requires STACKIT managed-service plan validation before migration; no current blocker
- [ ] (parked) proposal(issue-312-observability-csi-hardening): Extend Secrets Store CSI Driver hardening to Bitnami-chart modules (RabbitMQ, PostgreSQL, OpenSearch) — use CSI `secretObjects` sync to deliver STACKIT-managed credentials from Secrets Manager into K8s Secrets consumed by Bitnami `existingSecret` references. Tradeoff: audit trail is gained but etcd exposure is not eliminated (K8s Secret object is still created by the CSI sync). A separate ADR decision is required on whether audit trail alone satisfies the threat model for these modules, or whether Bitnami file-mount support is required first.
      trigger: on-scope: infra
      trigger: after: issue-312-observability-csi-hardening
      rationale: Bitnami charts consume credentials via K8s Secret env refs (existingSecret), not file mounts — CSI secretObjects sync still writes to etcd. Deferred until policy decision on partial hardening or Bitnami chart file-mount support.
- [ ] (parked) proposal(issue-277-argocd-health-na): per-resource-type ignoreResourceUpdates tuning for noisy types (ConfigMap, Endpoints)
      trigger: on-scope: infra
      rationale: no current CPU pressure evidence on local Docker Desktop; surfaces when future ArgoCD or infra work is scoped
- [ ] (parked) proposal(issue-171-managed-cache): bitnami/redis local lane migration — migrate bitnami/redis Helm chart to the replacement chart when issue #324 (bitnami chart migration) is in scope.
      trigger: after: issue-324
      rationale: same bitnami deprecation risk as postgres/rabbitmq/opensearch local lane; no actionable scope until issue #324 determines the migration target chart and version
- [ ] (parked) proposal(issue-171-managed-cache): Redis Cluster/HA mode — replace single-instance `stackit_redis_instance` with a multi-replica or cluster configuration.
      trigger: triage: next-session
      stale-after: 2
      rationale: single-instance default is sufficient for current consumer use cases (session store, rate-limiting, idempotency cache); HA requires separate capacity planning and consumer awareness
- [ ] (parked) proposal(issue-171-managed-cache): KMS envelope encryption of Redis password — wrap `MANAGED_CACHE_PASSWORD` (as stored in STACKIT Secrets Manager) with a STACKIT KMS key before writing to SM.
      trigger: after: issue-312
      rationale: KMS module is a separate optional module; same deferral pattern as issue-312-observability-csi-hardening KMS envelope entry; surfaces when KMS hardening is in scope for managed-service modules

### on-scope: observability

- [x] (done) proposal(issue-248-observability-module): Faro browser telemetry endpoint — incorporated into 2026-05-26-issue-248-observability-enhancements (PR #327). Faro receiver added to both local and STACKIT lanes (port 12347); CORS `allowed_origins` wired via OTC env substitution `${env:FARO_CORS_ALLOWED_ORIGINS}` with `extraEnvs` default `*` — consumers override via ArgoCD Application `extraEnvs`; `FARO_ENDPOINT` added to module contract outputs. Also covers: dashboard provisioning (kubectl convention dir + ConfigMap + Grafana sidecar); OTEL pipeline improvements (memory_limiter, filter/drop-healthcheck-spans, spanmetrics on local lane).
      trigger: on-scope: observability
- [x] (rejected) proposal(issue-248-observability-module): `OBSERVABILITY_RETENTION_DAYS` shell contract — rejected. Retention is enforced at the TF layer (STACKIT object storage lifecycle, Loki compactor). The OTEL Collector and shell scripts have no mechanism to act on a retention days value; adding it to the shell contract would create a dangling env var that consumers export but nothing consumes. Correct ownership: TF module inputs.
      trigger: on-scope: observability
- [x] (rejected) proposal(issue-248-observability-module): Langfuse integration — rejected. Consumer-specific LLM observability tooling; not appropriate for the generic blueprint module. Consumers may integrate Langfuse in their own app layers.
      trigger: on-scope: observability
- [ ] (parked) proposal(issue-248-observability-module): OTel semconv forwards-compatibility for healthcheck filter — add `url.path` as third filter condition in `filter/drop-healthcheck-spans` to cover OTel HTTP semconv v1.20+ SDKs (which emit `url.path` instead of `http.target`)
      trigger: on-scope: observability
      rationale: coverage gap, not a regression; SDKs on older semconv still filtered correctly; low priority for blueprint scope, surfaces when a consumer reports unfiltered healthcheck spans with new SDK
- [ ] (parked) proposal(issue-248-observability-module): Replace `grafana/k8s-monitoring` with separate charts — disruptive refactor (Grafana + Prometheus + Loki + Tempo as individual Helm releases); low value vs. maintenance cost given k8s-monitoring covers the same stack as a single chart.
      trigger: on-scope: observability
      rationale: k8s-monitoring covers the full local observability stack; splitting would add per-chart upgrade and config burden; deferred until a consumer reports a concrete capability gap blocked by the bundled chart
- [ ] (parked) proposal(issue-248-observability-module): Evaluate a provider-backed Logs/LogMe module or baseline observability extension using STACKIT Terraform resources
      trigger: on-scope: observability
      rationale: no active consumer need for a dedicated Logs service module; surfaces when a consumer requests LogMe or a second observability extension
- [ ] (parked) proposal(issue-312-observability-csi-hardening): Automated credential rotation trigger — emit an event-driven rotation when STACKIT Secrets Manager expiry fires, rather than relying on the CSI driver poll interval (default 2 min).
      trigger: on-scope: observability
      rationale: CSI driver already polls SM on a configurable interval; event-driven rotation is a separate feature with no current consumer request; surfaces when observability security hardening is in scope
- [ ] (parked) proposal(issue-312-observability-csi-hardening): Local lane CSI driver support — eliminate K8s Secret on the local lane once Docker Desktop ships native Secrets Store CSI Driver support.
      trigger: triage: next-session
      stale-after: 2
      rationale: conditional on external platform capability; Docker Desktop does not support Secrets Store CSI Driver natively as of 2026-05-27; no actionable scope until that changes
- [ ] (parked) proposal(issue-312-observability-csi-hardening): KMS envelope encryption of Secrets Manager credentials — wrap stored secrets with a STACKIT KMS key before writing to SM.
      trigger: on-scope: observability
      rationale: KMS module is a separate optional module; sensible hardening but out of scope for observability CSI work; surfaces when KMS hardening is in scope

### on-scope: workflows

- [x] (done) proposal(issue-248-workflows-local-lane): Local lane Airflow support — implemented in PR #316 (merged). apache-airflow/airflow chart v1.20.0 (Airflow 3.1.8); ArgoCD + Helm; git-sync sidecar; LocalExecutor; WORKFLOWS_LOCAL_ENABLED toggle; webserverConfig.py OIDC; WORKFLOWS_LOCAL_DAGS_* and WORKFLOWS_LOCAL_OIDC_* env vars.
- [x] (done) proposal(issue-248-workflows-local-lane): Automate port-forward within local-workflows smoke script — implemented in PR #317. Smoke script sources port_forward.sh and calls start_port_forward/wait_for_local_port/stop_port_forward; make infra-local-workflows-smoke is fully self-contained.
- [ ] (parked) proposal(issue-248-workflows-local-lane): Automate `airflow-git-credentials` Kubernetes secret creation — add `infra-local-workflows-init-secrets` make target (following `langfuse_keycloak_reconcile.sh` pattern) that creates the secret from env vars before deploy.
      trigger: on-scope: workflows
      rationale: one-time manual operation per cluster; deferred until an init-secrets reconcile pattern is needed across multiple modules
- [ ] (parked) proposal(issue-248-workflows-module): Provider-backed migration — replace REST API contract with `stackit_workflows_instance` Terraform provider resource when an official resource is released in a future provider version
      trigger: on-scope: workflows
      rationale: no TF provider resource exists as of v0.96.0; tracked in STACKIT platform expansion section; migration path documented in ADR-issue-248-workflows-module.md
- [x] (done) proposal(issue-248-workflows-module): Python version split strategy — implemented in PR #317. README "DAG Development Setup" section documents 3.12 vs ≥3.13 split; infra-local-workflows-dags-venv creates .venv-dags pinned to Python 3.12; /dags/ repository structure convention documented with coding agent guidance.
- [ ] (parked) proposal(issue-248-workflows-local-lane): Track Airflow version in dags-venv guidance — `local_workflows_dags_venv.sh` and README both hard-code `apache-airflow==3.1.8`; derive from `WORKFLOWS_LOCAL_HELM_CHART_VERSION` or a companion var so the install hint stays in sync when the chart is upgraded.
      trigger: on-scope: workflows
      rationale: acceptable for current cut (chart v1.20.0 → Airflow 3.1.8); flagged in PR #317 review by @claude; surfaces when chart is next upgraded

### on-scope: blueprint

- [ ] proposal(issue-248-dns-module): domain contract JSON pattern — single SSOT JSON file (per-environment hostnames, acme emails, dns_zones list) driving TF tfvars + ArgoCD Helm values via a renderer script with --check mode; cross-cutting refactor affecting all optional modules.
      rationale: pattern observed in an existing consumer deployment; requires refactor of all optional module env var surfaces; deferred until blueprint multi-module configuration surface is next in scope
- [ ] proposal(issue-248-public-endpoints-module): ReferenceGrant per-namespace enforcement — replace `allowedRoutes.namespaces.from: All` with explicit `ReferenceGrant` resources requiring platform sign-off per consumer namespace to attach HTTPRoutes to the shared Gateway.
      rationale: architectural change to the consumer onboarding model; current self-service HTTPRoute attachment is intentional for developer velocity; surfaces when a consumer requires namespace-level isolation at the Gateway routing layer
- [ ] proposal(issue-241-make-override-warnings): extend `?=` override-point pattern to other blueprint-managed targets.
      rationale: no consumer request for specific targets; same pattern directly applicable
- [ ] proposal(issue-164): value-based template scanning — detect hardcoded version strings in templates, not just variable name references.
      rationale: variable-name grep covers the common case; value scanning risks false positives and multi-format string handling
- [ ] proposal(issue-270-test-ownership-contract): active delete-on-upgrade for stale relocated test files in consumer repos.
      rationale: no active consumer complaint; D-3 in architecture.md documents the deferral
- [ ] proposal(issue-268-consumer-workarounds-catalogue): `env_var` action kind — modify `.envrc` as a workaround action.
      rationale: no concrete use case yet; risk of persistent consumer environment pollution
- [ ] proposal(issue-258-259-260-261-v110-engine-hotfix): Full POSIX shell parser in `upgrade_shell_behavioral_check.py` — replace grep-based heuristic with `shellcheck --format=json`.
      rationale: heuristic covers all known production failure classes; full parser requires new external binary dependency
- [ ] proposal(issue-272-273-v110-docs-hotfix): `blueprint-align-pnpm-pins` migration target — takes `docs/package.json` as canonical and rewrites all other `packageManager` fields.
      rationale: improved error message (Option A) is sufficient for operators to resolve drift manually; automation belongs in a dedicated work item
- [ ] proposal(issue-265-271-source-exists-inference): active cleanup of stale consumer-created files in `blueprint_managed_roots` paths.
      rationale: `blueprint_managed_roots` exclusivity contract governs this; no new risk introduced; revisit when upgrade resolution logic is next touched
- [ ] proposal(issue-265-271-source-exists-inference): `quality-ci-upgrade-validate` runs only on push to main, not PRs — a breaking upgrade regression could merge undetected.
      rationale: making it a non-blocking PR annotation or required status closes the gap
- [ ] proposal(issue-267-269-pipeline-finalize-auto-clone): deepen clone for ancestry traversal — current `--depth 1` sufficient for Stage 5 `git show`.
      rationale: no current stage needs ancestry; adding depth only when a future stage requires it avoids unnecessary network cost
- [ ] proposal(issue-267-269-pipeline-finalize-auto-clone): standalone finalize precondition guard — aborts with an unhelpful postcheck failure if called before Stage 3–7 artifacts exist.
      rationale: usage block documents the precondition; standalone UX improvement is out of scope for the original work item
- [ ] proposal(issue-267-269-pipeline-finalize-auto-clone): sync pass target expansion — dynamic discovery of sync targets instead of the current explicit three-target list.
      rationale: current list is complete; dynamic discovery adds robustness when a new sync target is added
- [ ] proposal(issue-206): source-only seed change advisory — emit an advisory plan entry when a `source_only` file has changed blueprint content between tags.
      rationale: surfaces when blueprint maintainers next improve seed workload content (health probes, security contexts, resource limits) or a consumer reports silently missing a seed update
- [ ] proposal(issue-217): extract `_assert_descriptor_kustomization_agreement` as shared module helper for future smoke scenario reuse.
      rationale: no additional callers today; surfaces when the next blueprint smoke scenario is developed
### on-scope: quality

- [ ] proposal(issue-286-288-ci-template-draft-guard-drift-hook): add root dotfiles to `_QG_INFRA_GATE_PATHS` for `infra-validate` drift coverage beyond the commit hook.
      rationale: commit hook is faster and more targeted (~1–2 s); extending path-gating has broader scope implications
- [ ] proposal(quality-hooks-keep-going-mode): parallel execution of independent quality-hooks checks.
      rationale: real optimization but non-trivial (log ordering, signal propagation, interleaved output); see ADR-20260428 Alt D and ADR-20260430 Alt D
- [ ] proposal(quality-hooks-keep-going-mode): structured JSON summary output for machine consumers of the keep-going summary block.
      rationale: no current consumer; plain-text v1 contract is sufficient; design when a concrete integration need arises
- [ ] proposal(issue-272-273-v110-docs-hotfix): preflight pnpm version drift detection — scan all `package.json` `packageManager` fields and report drift before any install runs.
      rationale: out of scope for a two-line hotfix; surfaces when quality hook scope is next extended
- [ ] proposal(issue-265-271-source-exists-inference): `test_pyramid_contract.json` path references drift silently when files move — automate path existence check.
      rationale: demonstrated by `tests/infra/` → `tests/blueprint/` moves causing stale assertions
- [ ] (parked) proposal(issue-275-sdd-bypass-track): SPEC_READY_EXCEPTION: chore + AGENTS.decisions.md machine-verifiable validation (Option B)
      trigger: on-scope: quality
      rationale: checker needs branch/PR context to look up AGENTS.decisions.md entry — makes quality-sdd-check non-deterministic in local runs; convention + code review sufficient
- [ ] (parked) proposal(issue-248-observability-module): `blueprint-template-smoke` declare -A fix — `prune_codex_skills.sh` uses bash associative arrays (`declare -A`) incompatible with macOS `/bin/sh`; pre-existing defect on main before PR #308
      trigger: on-scope: quality
      rationale: pre-existing defect confirmed on main before this branch; repo-wide cleanup item; no consumer impact until blueprint-template-smoke is a blocking gate
- [ ] (parked) proposal(issue-353-vgate-e2e-classification): Playwright test existence check — machine-verify at least one playwright test file exists on disk when has-user-facing-flow: true
      trigger: on-scope: quality
      rationale: naming convention per repo is not standardized; false-positive risk for repos creating tests in a separate work item; classification-field enforcement is the primary gate
- [ ] (parked) proposal(issue-353-vgate-e2e-classification): Cross-repo V-gate classification audit report — list all specs with their V-gate classification status across consumer repos
      trigger: on-scope: quality
      rationale: requires aggregation infrastructure; belongs in a dedicated observability work item
- [ ] (parked) proposal(issue-353-vgate-e2e-classification): Frontend-stack-mismatch heuristic warning — non-blocking stderr warning when frontend-stack-profile is non-none and has-user-facing-flow: false
      trigger: on-scope: quality
      rationale: warning UX surface needs separate design pass; primary risk addressed by step01 inference and template signal-list comment

### on-scope: a11y

- [ ] proposal(issue-238-239-240-a11y-compliance): wire `quality-a11y-acr-check` into `quality-ci-blueprint`.
      rationale: revisit when CI blueprint gains a stable ACR or a skip mechanism; false-positive risk currently blocks this
- [ ] proposal(issue-238-239-240-a11y-compliance): automated W3C JSON fetch in `sync_acr_criteria.py`.
      rationale: adds network dependency at CI time; surface when any a11y-scope work item is next in flight

### on-scope: skills

- [x] (incorporated: issue-347-human-sdd-c7-symmetry) proposal(issue-247-step05-slice-done-gate): automated SKILL.md content scanner — verify SKILL.md contains required guardrail patterns and the smoke gate step as automated regression protection
      trigger: on-scope: skills
      rationale: incorporated as FR-015 in #347 — extended check_sdd_assets.py with structural-section presence check + C7 addendum byte-equality gate across all seven step skills

### on-scope: c7-emission

- [x] (rejected) proposal(issue-347-human-sdd-c7-symmetry): JSONL line signing / HMAC — rejected. Q-2 resolved as "no signing"; committed-file + git-blame audit trail is sufficient anti-tamper for the local-cli scope. Consciously discarded at PR #348 closure.
- [ ] (parked) proposal(issue-347-human-sdd-c7-symmetry): consumer-repo C7 emission — emit lifecycle events from consumer repos once `artifacts/c7/*.jsonl` is a stable contract on the blueprint side
      trigger: triage: next-session
      stale-after: 2
      rationale: defer until first consumer adopter requests metrics-dashboard symmetry; re-evaluate after first 30 PRs ship with local-cli emitter post-merge
- [ ] (parked) proposal(issue-347-human-sdd-c7-symmetry): IDE-extension direct emission (VS Code / JetBrains) — extend helper beyond CLI-only to emit directly from editor extensions
      trigger: on-scope: c7-emission
      rationale: low urgency; validate local-cli CLI pattern first across real work items before adding IDE surface complexity

### after: issue-368

- [ ] (parked) proposal(issue-368-factory-cost-telemetry-routing-fixture): embedding-based router implementation — replace the bigram-overlap step02 routing algorithm with embedding-match when T-104 fixture failure rate ≥ 20% (see `test_step02_routing_fixture.EMBEDDING_UPGRADE_THRESHOLD`).
      trigger: after: issue-368
      rationale: evidence-gathering fixture (Slice 4, #361) is the trigger condition; embedding-match router ships only when the fixture proves bigram routing is insufficient; no implementation timeline until failure data exists

### after: issue-350

- [ ] (parked) proposal(issue-368-factory-cost-telemetry-routing-fixture): cost telemetry consumer dashboard — build a dashboard over `outcome_details.ticket_token_summary` and per-phase `outcome_details.token_usage` events in the C7 ingest pipeline.
      trigger: after: issue-350
      rationale: downstream of C7 ingest (#350); no consumer has requested a dashboard UI yet; surfaces when ingest is live and a consumer requests cost visibility

### on-scope: factory

- [ ] (parked) proposal(issue-368-factory-cost-telemetry-routing-fixture): per-expert prompt-cache efficiency — apply prompt-cache discipline (system prompt caching, aggressive cache-friendly message ordering) to Opus-tier expert invocations to reduce per-ticket token cost.
      trigger: on-scope: factory
      rationale: needs first-run telemetry baseline from outcome_details.token_usage to quantify benefit; see ADR-issue-364 § 11 Future Work; surfaces on next factory-scope work item after baseline is established

- [ ] (parked) proposal(issue-361-orchestrator-service): horizontal-scaling for the orchestrator pod — v1 ships `replicas: 1` (single-writer to the per-ticket token accumulator). Multi-replica with a shared per-ticket lock service is deferred until throughput needs are observed. Re-evaluate against real-world `outcome_details.token_usage` data from the orchestrator's first months in production.
      trigger: on-scope: factory
      rationale: orchestrator-scoped (factory-wide tag is correct because throughput data only becomes available after factory-runtime work ships); parked at PR #372 step07 publish triage; relocated from `### after: issue-361` to `### on-scope: factory` per Codex P2 review of PR #372 3rd-review pass (entry now lives under a section that matches its trigger heading).

### after: consumer-app-descriptor-adoption

- [ ] decommission: remove deprecated generated `apps/catalog/manifest.yaml` compatibility artifact.
      trigger: after: consumer-app-descriptor-adoption
      rationale: `apps/descriptor.yaml` becomes the canonical app metadata source; keeping generated catalog output forever creates a duplicate contract surface
- [ ] decommission: remove deprecated `_is_consumer_owned_workload()` bridge guard after descriptor adoption becomes mandatory or two blueprint minor releases have passed, whichever is later.
      trigger: after: consumer-app-descriptor-adoption
      rationale: descriptor ownership and kustomization-ref fallback supersede the path-prefix bridge; tracking prevents it from becoming permanent hidden behavior

### after: github-teams-provisioned

- [ ] (parked) proposal(issue-337-factory-phase-0-foundations): operational team provisioning on GitHub — create the eight teams named in `.github/CODEOWNERS` (gate-1: `@sbonoc/factory-product`, `@sbonoc/factory-architecture`, `@sbonoc/factory-security`, `@sbonoc/factory-operations`; gate-2: `factory`, `infra`, `docs`, `governance`) and populate each with ≥ 2 members; the first factory `agent-ready` label MUST NOT be applied until this is complete.
      trigger: after: github-teams-provisioned
      rationale: operational prerequisite, not a code change; Operations sign-off on PR #345 attests to provisioning intent; also tracked in `docs/blueprint/autonomous-factory/design-contracts.md` C6 `### Open Decisions` against #337 close

### after: issue-336

- [ ] (parked) proposal(issue-337-factory-phase-0-foundations): solo-operator profile enforcement layer — GitHub Actions check reads `spec.spec_driven_development_contract.readiness_gate.sod_policy.solo_operator` in `blueprint/contract.yaml`, scans the PR for the literal `SOLO_OPERATOR_ATTESTATION: confirmed` marker on a canonical sign-off comment, validates the five-item normative checklist from `ADR-issue-337-separation-of-duties-at-factory-velocity.md § Satisfaction paths`, and applies the SoD count adjustment (Path 2 satisfies the multi-author rule alternatively). Factory-bot suppression remains immutable across both paths.
      trigger: after: issue-336
      rationale: enforcement is in #336's scope (GitHub Actions webhook pipeline owns SoD evaluation); ADR + `sod_policy` toggle make the rule mechanically discoverable so #336 cannot ship without consuming it; ships the ADR amendment under PR #345 declaratively without expanding Phase 0 scope to runtime code

- [ ] (parked) proposal(issue-336-webhook-handler): in-cluster webhook-receiver authentication + rotation policy — the receiver has TWO ingress paths and they need different auth primitives. (1) **GitHub Actions → receiver** (the trigger-handoff path clarified on PR #372): use GitHub Actions OIDC — workflows mint short-lived OIDC tokens via `id-token: write`; receiver verifies against `token.actions.githubusercontent.com` JWKS and asserts `repo` (+ `workflow`, `ref` when applicable) claims; NO shared secret to rotate (JWKS rotates automatically). (2) **GitHub webhook deliveries → receiver** (for events the workflows do not intercept): use GitHub's native HMAC signature (`X-Hub-Signature-256` over the raw payload with a shared secret); rotate the secret quarterly (90 days) via ESO `ExternalSecret` against STACKIT Secrets Manager using a two-phase atomic rotation (set new secret in GitHub webhook config and let GitHub dual-sign for ~24h, ESO syncs the new secret to the receiver, then remove the old secret). Defense-in-depth: GitHub IP allowlist on path 2 (sourced from `meta.hooks` API), NetworkPolicy restricting receiver ingress to the cluster ingress gateway only, per-environment OIDC audiences so a leaked token from one receiver cannot replay against another. Plain API key in a custom header is strictly weaker than HMAC (no replay protection, no native GitHub support) and is REJECTED.
      trigger: after: issue-336
      rationale: NFR-SEC-001 dependency — the receiver is an internet-exposed authenticated endpoint and its auth surface MUST be pinned before #336 ships any code. Raised on PR #372 (parent intake of #361 orchestrator); orchestrator is downstream subscriber on RabbitMQ and never touches the receiver's auth surface, so the decision belongs squarely to #336's scope. ESO-managed secret pattern aligns with #312 observability-csi-hardening and #334 factory-bot-identity precedents. See PR #372 conversation for the investigation that drove these recommendations.

- [ ] (parked) proposal(issue-361-orchestrator-service): orchestrator local-cluster smoke lane — the orchestrator's runtime depends on the OpenHands Agent Server (`#335`) and RabbitMQ trigger queue (`#336`) Helm charts. Until both ship reusable Helm charts under `scripts/templates/infra/`, the orchestrator's local-cluster smoke lane cannot pull them in. Author the local-cluster smoke lane (kind-cluster fixture + an `infra-helm-orchestrator-smoke` make target under the existing `infra-helm-*` family) once both blockers are resolved.
      trigger: after: issue-336
      rationale: hard-blocked on `#335` + `#336` shipping their Helm charts. `after: issue-336` is the later-resolving of the two blockers; entry surfaces only when both are done. Parked at PR #372 step07 publish triage; relocated to `### after: issue-336` to match its trigger heading (per Codex P2 review on PR #372 3rd-review pass — entries scanned by trigger heading after #336 resolves would have missed this if left under `### after: issue-361`).

### after: issue-347

- [ ] (parked) proposal(issue-347-human-sdd-c7-symmetry): widen `local-cli` `event_id` derivation to six-input form including `decision_author` + `branch_sha` — currently `scripts/lib/sdd/c7_emit.py::derive_event_id` hashes `ticket_id|phase|rerun_round|emitter` (the same four-input form as `emitter: orchestrator`). Two different human operators running the same SDD step on the same `ticket_id` from different branches collide on this four-input form, and the Central Brain (#343) ingest pipeline (per its Journey A) deduplicates them into a single graph node — losing per-decision provenance the Brain needs for ADR-recall and cross-team awareness. Fix: amend `derive_event_id` to a six-input form when `emitter == "local-cli"` (inputs: `ticket_id|phase|rerun_round|emitter|decision_author|branch_sha`); add `decision_author` (populated from `gh auth status` or `BLUEPRINT_DECISION_AUTHOR` env var, MUST NOT equal factory bot login per Contract C5) + `branch_sha` (populated from `git rev-parse --short HEAD`) as required-when-`local-cli` extension fields in the `LifecycleEvent` Pydantic model; update `design-contracts.md` § C7 with the corresponding two extension-field rows + amend the `event_id` JSON-schema description; extend `tests/sdd/test_c7_emit*.py` to assert the six-input collision-resistance property + that the helper rejects emission when `decision_author` equals the configured factory bot login.
      trigger: after: issue-347
      rationale: `#347` is the canonical owner of the `local-cli` helper + its pytest. The contract amendment was originally authored on PR #372 strategic-alignment audit (commit `0ac3d514` F2) but reverted on PR #372 5th-review pass per Codex P2-1 — the parallel helper implementation was missing, AND every checked-in `local-cli` C7 event prior to the helper amendment would be contract-violating. Landing both atomically in `#347`'s scope is the only honest path; the Brain (#343) is Draft and the dedup-collision concern is real but not blocking until the Brain ingest pipeline is authored.

- [ ] (parked) proposal(issue-336-webhook-handler): absorb #361 parent-merge operator runbook into #336 webhook handler on `pr-merged` event — when the #361 parent coordination PR (and any future parent-coordination PR) merges, the #336 webhook handler should automatically: (1) invoke the parent's `file_children.sh` to file the declared child issues, (2) invoke `add_deferred_triggers.sh` to append deferred-filing backlog entries, (3) inject the `## Integration Acceptance Criteria` section from the parent spec into the parent issue body. Today these three steps are a manual human-operator runbook (per parent spec `pr_context.md` § Operator Runbook), which contradicts Epic #332's "two human gates only, every step in between autonomous" architecture — the runbook is a third HITL touchpoint between gate-1 spec sign-off and gate-2 bounded-context merge. Absorbing into #336 eliminates the touchpoint AND establishes the right primitive that `blueprint-ticket-decompose-light` runtime invocations will reuse.
      trigger: after: issue-336
      rationale: raised by PR #372 strategic-alignment audit 2026-06-19 against Epic #332 "two human gates only" vision. Today's manual runbook lives in PR #372's `pr_context.md` as a temporary measure because #336 webhook handler does not yet exist; once #336 ships, the runbook MUST be deprecated in favor of webhook-driven absorption. Future parent coordination PRs MUST NOT replicate the manual runbook pattern; this entry instructs #336's scope to absorb the responsibility universally. The two helper scripts (`file_children.sh` + `add_deferred_triggers.sh`) shipped by PR #372 are designed to be webhook-invocable (idempotent + env-overridable + token-driven), so absorption is mechanical — #336 just needs to invoke them in the right pr-merged handler.

### after: issue-361

- [ ] (parked) execute #361 parent-merge operator runbook — file 4 child issues (`#361.1` + `#361.2` + `#361.4` + `#361.5`) via `bash specs/2026-06-18-issue-361-orchestrator-service/file_children.sh`; append `#361.3` deferred-filing triggers via `bash specs/2026-06-18-issue-361-orchestrator-service/add_deferred_triggers.sh`; manually add the 5-checkbox `## Integration Acceptance Criteria` section to the `#361` issue body (per T-003 + FR-013 + Contract C4). Canonical runbook with per-step verification + rollback: `specs/2026-06-18-issue-361-orchestrator-service/pr_context.md § Operator Runbook`. Both scripts are idempotent; either the human operator or any agent with `gh` auth can execute the runbook end-to-end. Mark this entry `(done)` after Steps 1+2+3 complete.
      trigger: after: issue-361
      rationale: PR #372 is a parent coordination spec — merging it does NOT (by design) file child GitHub issues, append the deferred-trigger backlog entries, or update the parent `#361` issue body. All three side effects are deliberate operator actions held until the spec is signed off and merged so children cite the final FR text and no phantom issues exist if the PR were abandoned. Without this backlog reminder the post-merge state would silently drift: spec says 5 children exist; GitHub would still show only `#361` open. See FR-014 / FR-015 / T-003 / FR-017 / Contract C4 for the binding contracts and the rationale.

- [x] (rejected) proposal(issue-361-orchestrator-service): promote parent #361 coordination spec to a step04 plan-slicer execution — the 5-child decomposition declared at intake is the manual equivalent of `blueprint-ticket-decompose-light`. Once that skill ships (governance authored in `#360`, runtime owned by this work item across `#361.1`..`#361.5`), the parent decomposition could in principle be replayed through the skill for symmetry-of-evidence. Rejected at PR #372 step07 publish triage 2026-06-19 — cosmetic with no new value: the decomposition outcome is identical whether authored manually or via the skill. Consciously discarded.

### after: epic-343-promote

- [ ] (parked) proposal(epic-343-central-brain): #343-perspective review of the C7 emission shape before Epic #343 leaves Draft — verify the C7 minimum fields + extension fields (specifically the F2 amendments authored at PR #372 strategic audit 2026-06-19: `local-cli` six-input `event_id` form, `token_usage[expert_slug].routing_key` sub-key, `outcome_details.touches_services[]` extension field, `outcome_details.decision_author` + `outcome_details.branch_sha` extension fields) satisfy the Brain's graph-traversal needs (Journey A spec→PR recall; Journey C SRE incident→PR correlation by service touch). Confirm or amend the shape BEFORE Epic #343 promotes from Draft to active backlog so the ingestion-pipeline schema doesn't need to do gymnastics to consume historical events.
      trigger: after: epic-343-promote
      rationale: PR #372 strategic-alignment audit 2026-06-19 amended design-contracts.md § C7 to preemptively address known Brain ingestion needs (per Epic #343 Customer Journeys A + C), but the Brain epic is Draft and no Brain-perspective reviewer has signed off the amendments. This entry parks a defensive review obligation so that when Epic #343 promotes to active backlog, the first work item under it MUST confirm the C7 shape OR file an amendment to fix any remaining gaps before the ingestion pipeline is authored. Avoids the failure mode where the Brain team ships an ingestion pipeline against a C7 shape that requires costly post-hoc gymnastics.

---

## Long Horizon

Ideas without a delivery commitment. Promote to active only when a concrete triggering use case exists.

### Blueprint and quality tooling

- [ ] Add an automated bundled-skill contract verifier to enforce parity across `.agents/skills/**`, consumer-template fallbacks, install make targets, and docs references.
- [ ] Add a contract-level traceability verifier that checks every declared requirement ID in `spec.md` maps to implementation paths and at least one automated test assertion.
- [ ] Add a declarative module action manifest (`apply/plan/smoke/destroy`) to replace duplicated wrapper branching and keep runtime/CI execution paths deterministic.
- [ ] Extract artifact/schema validation orchestration into a shared Python package entrypoint consumed by blueprint wrappers (single validation surface for state/schema contracts).
- [ ] Add a repository-wide script trace identifier contract propagated across wrapper calls and metrics to improve CI/runtime diagnosability for multi-script failures.
- [ ] Auto-generate docs snippets for canonical blueprint lifecycle and audit targets from source metadata to reduce docs drift and manual synchronization load.
- [ ] Split CI into path-aware lane selection for contract/docs-only vs infra/runtime-heavy changes while preserving full strict gates on merge/main updates.
- [ ] Backport the new runtime-credentials ESO source-to-target contract (including mandatory Keycloak/IAP runtime targets) and drift-safe platform extension surface to existing generated-consumer repositories.
- [ ] Add a CI-grade execute-mode full e2e lane (ephemeral cluster + `test-e2e-all-local-execute`) so merge gating covers real apply paths, not only dry-run orchestration.
- [ ] Tune and baseline `E2E_*_BUDGET_SECONDS` from collected CI metrics (p95 per lane) and fail budgets only once the baseline is stable.
- [ ] Extend the consumer seed resync workflow with optional merge-assist coverage for selected init-managed identity files without weakening customization boundaries.
- [ ] Add pluggable async message-contract provider support beyond Pact while preserving the canonical producer/consumer lane contract and upgrade safety guarantees.

### on-scope: platform

- [ ] proposal(issue-248-public-endpoints-module): service mesh / mTLS east-west — encrypt and mutually authenticate pod-to-pod traffic using a service mesh (Istio, Linkerd, or Cilium); fully realises zero-trust for east-west traffic alongside the public-endpoints north-south TLS edge.
      rationale: separate architectural decision with major operational implications (sidecar injection, mTLS policy, control plane overhead); surfaces when a platform-wide zero-trust east-west policy is formally adopted
- [ ] proposal(issue-248-public-endpoints-module): SPIFFE/SPIRE workload identity — cryptographic workload identity for service-to-service authentication without shared secrets; prerequisite for mTLS without a full service mesh.
      rationale: requires platform-wide identity infrastructure; surfaces alongside or after the service mesh decision

### STACKIT platform expansion

- [ ] Add a DNS contract mode where generated-consumer repos can provide pre-created Keycloak/IAP DNS entries instead of blueprint-managed STACKIT DNS record reconciliation.
- [ ] Add optional Neo4j Keycloak realm/client reconciliation (gated by `KEYCLOAK_OPTIONAL_MODULE_RECONCILIATION_ENABLED`).
- [ ] Continue migrating `workflows` to provider-backed STACKIT execution when official resources become available.
- [ ] Evaluate provider-backed relational/NoSQL data-service modules (`mariadb`, `mongodbflex`, `sqlserverflex`).
- [ ] Evaluate a provider-backed File Storage module using STACKIT SFS Terraform resources.
- [ ] Evaluate whether STACKIT Application Load Balancer, CDN, and Public IP resources should become first-class edge modules.
- [ ] Evaluate whether STACKIT network and security primitives (`network`, `network_area`, `routing_table`, `security_group`) should become first-class foundation capabilities.
- [ ] Evaluate whether STACKIT identity/project primitives (`service_account`, role assignments, Resource Manager folders/projects) should become blueprint-managed bootstrap/foundation capabilities.
- [ ] Evaluate whether STACKIT compute-oriented primitives (`server`, `volume`, `edgecloud`, `modelserving`) belong in blueprint scope for future workload patterns.
