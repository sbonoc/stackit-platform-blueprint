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

## Active Work

### P1 — Next Up (priority order confirmed 2026-05-15)

- [x] P1 (Architecture gate): Issue #295 — CLOSED 2026-05-15. Audit confirmed blueprint templates contain no OpenMetadata content; `AGENTS.decisions.md` already records the architectural decision (OM is consumer/product-owned). No template changes required.
- [x] P1 (Bug — ArgoCD health): Issue #277 — CLOSED. `ignoreResourceUpdates.all` `/status` rule narrowed; health reporting restored. Merged PR #298.
- [x] P1 (SDD governance): Issue #275 — CLOSED. Lightweight bypass track shipped. Merged PR #299.
- [x] P1 (Quality tooling): Issues #293 + #294 — CLOSED. Three-layer AGENTS.md ↔ north_star.md anti-duplication contract shipped. Merged PR #301.
- [ ] (parked) proposal(issue-293-294-agents-north-star-cross-reference): Option B — body-heuristic duplication detection
      trigger: on-scope: quality
      rationale: OPTION_A (exact heading match) selected in spec as the starting point; Option B adds false-positive risk before consumer feedback on Option A is gathered.

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
- [ ] Issue #284 — support `ARGOCD_LOCAL_TARGET_REVISION` env var to track a non-default branch in local ArgoCD.
- [x] Issue #296 — workaround manifest `action_path` CI validation gate. Closed by PR #304.
- [ ] (no issue) Ownership checker robustness: support normalized equivalence for semantically-identical prune-glob expressions in ownership-matrix documentation checks.

### P2 — Platform modules

- [ ] Issue #248 remaining modules — STACKIT-managed service candidates (kms ✅, secrets-manager ✅ PR #305, dns SPEC_READY PR #306, public-endpoints ✅ PR #307, observability SPEC_READY PR #308, workflows, identity-aware-proxy). Gate on #295 removed — architecture decision recorded in `AGENTS.decisions.md`: OM is consumer/product-owned and not a blueprint module candidate.
- [ ] Issue #171 — managed-cache module: STACKIT Managed Redis as a first-class optional module (Helm/ArgoCD-managed, provider-backed via STACKIT Terraform).
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
- [ ] (parked) proposal(issue-277-argocd-health-na): per-resource-type ignoreResourceUpdates tuning for noisy types (ConfigMap, Endpoints)
      trigger: on-scope: infra
      rationale: no current CPU pressure evidence on local Docker Desktop; surfaces when future ArgoCD or infra work is scoped

### on-scope: blueprint

- [ ] proposal(issue-248-dns-module): domain contract JSON pattern — single SSOT JSON file (per-environment hostnames, acme emails, dns_zones list) driving TF tfvars + ArgoCD Helm values via a renderer script with --check mode; cross-cutting refactor affecting all optional modules.
      rationale: pattern observed in sbonoc/agentic-graphrag; requires refactor of all optional module env var surfaces; deferred until blueprint multi-module configuration surface is next in scope
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

### on-scope: a11y

- [ ] proposal(issue-238-239-240-a11y-compliance): wire `quality-a11y-acr-check` into `quality-ci-blueprint`.
      rationale: revisit when CI blueprint gains a stable ACR or a skip mechanism; false-positive risk currently blocks this
- [ ] proposal(issue-238-239-240-a11y-compliance): automated W3C JSON fetch in `sync_acr_criteria.py`.
      rationale: adds network dependency at CI time; surface when any a11y-scope work item is next in flight

### on-scope: skills

- [ ] (parked) proposal(issue-247-step05-slice-done-gate): automated SKILL.md content scanner — verify SKILL.md contains required guardrail patterns and the smoke gate step as automated regression protection
      trigger: on-scope: skills
      rationale: skill runbook is human-authored governance prose, not a machine-verifiable interface contract; automated scanner couples check to prose phrasing and requires updates on any reword; spec-to-code review gap is sufficient for now

### after: consumer-app-descriptor-adoption

- [ ] decommission: remove deprecated generated `apps/catalog/manifest.yaml` compatibility artifact.
      trigger: after: consumer-app-descriptor-adoption
      rationale: `apps/descriptor.yaml` becomes the canonical app metadata source; keeping generated catalog output forever creates a duplicate contract surface
- [ ] decommission: remove deprecated `_is_consumer_owned_workload()` bridge guard after descriptor adoption becomes mandatory or two blueprint minor releases have passed, whichever is later.
      trigger: after: consumer-app-descriptor-adoption
      rationale: descriptor ownership and kustomization-ref fallback supersede the path-prefix bridge; tracking prevents it from becoming permanent hidden behavior

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
- [ ] Define the Python version split strategy before STACKIT Workflows (Airflow) integration: establish how the blueprint tooling Python version will coexist with the Airflow runtime-constrained Python.
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
- [ ] Evaluate a provider-backed Logs/LogMe module or baseline observability extension using STACKIT Terraform resources.
- [ ] Evaluate a provider-backed File Storage module using STACKIT SFS Terraform resources.
- [ ] Evaluate whether STACKIT Application Load Balancer, CDN, and Public IP resources should become first-class edge modules.
- [ ] Evaluate whether STACKIT network and security primitives (`network`, `network_area`, `routing_table`, `security_group`) should become first-class foundation capabilities.
- [ ] Evaluate whether STACKIT identity/project primitives (`service_account`, role assignments, Resource Manager folders/projects) should become blueprint-managed bootstrap/foundation capabilities.
- [ ] Evaluate whether STACKIT compute-oriented primitives (`server`, `volume`, `edgecloud`, `modelserving`) belong in blueprint scope for future workload patterns.
