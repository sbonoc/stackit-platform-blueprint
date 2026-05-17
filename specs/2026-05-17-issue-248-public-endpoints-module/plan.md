# Implementation Plan

## Implementation Start Gate
- Implementation tasks MUST remain unchecked until `SPEC_READY=true`.
- If required inputs are missing, add `BLOCKED_MISSING_INPUTS` in `spec.md` and keep the gate closed.

## Constitution Gates (Pre-Implementation)
- Simplicity gate:
  - Keep initial implementation scope minimal and explicit.
  - Avoid speculative future-proof abstractions.
- Anti-abstraction gate:
  - Prefer direct framework primitives over wrapper layers unless justified.
  - Keep model representations singular unless boundary separation is required.
- Integration-first testing gate:
  - Define contract and boundary tests before implementation details.
  - Ensure realistic environment coverage for integration points.
- Positive-path filter/transform test gate:
  - For any filter or payload-transform logic, at least one unit test MUST assert that a matching fixture value returns a record.
  - Positive-path assertions MUST verify relevant output fields remain intact after filtering/transform.
  - Empty-result-only assertions MUST NOT satisfy this gate.
- Finding-to-test translation gate:
  - Any reproducible pre-PR finding from smoke/`curl`/deterministic manual checks MUST be translated into a failing automated test first.
  - The implementation fix MUST turn that test green in the same work item.
  - If no deterministic automation path exists, publish artifacts MUST record the exception rationale, owner, and follow-up trigger.

## Delivery Slices

### Slice 1 — cert-manager feature gate + test contract scaffold (red → green)
Register `test_contract.py` in `test_pyramid_contract.json` first (prevents pre-commit hook failure), then write failing assertions for AC-005, AC-011, AC-012, AC-020. Enable cert-manager Gateway API feature gate (AC-005). All assertions green. Note: AC-020 assertion scaffolded here (static analysis of destroy script) but turns green only after slice 2 implements the destroy ordering.

### Slice 2 — HTTPS listener + external-dns annotation + Issuer + Certificate + security policies (red → green)
Write failing assertions for AC-001, AC-002, AC-003, AC-004, AC-013, AC-015, AC-017, AC-018, AC-019. Implement:
- Gateway template: add HTTPS listener + external-dns annotation (AC-001, AC-004).
- `public_endpoints.sh`: add manifest rendering helpers for Issuer, Certificate (with `renewBefore`, AC-015, NFR-OBS-002), gateway TLS policy (HSTS + min TLS 1.2, AC-017, AC-013, NFR-SEC-006, NFR-SEC-002), and NetworkPolicy manifests (AC-018, NFR-SEC-007); add profile-aware `PUBLIC_ENDPOINTS_ACME_SERVER` default (NFR-SEC-004).
- `public_endpoints_apply.sh`: apply Issuer + Certificate + gateway TLS policy + NetworkPolicy manifests; extend runtime state with `cluster_issuer_name`, `cluster_issuer_type`, `tls_secret_name` (AC-009); emit KMS warning for `stackit-prod` without KMS module (AC-019, NFR-SEC-008).
- `public_endpoints_destroy.sh`: delete Certificate before Issuer before gateway baseline (NFR-REL-001, AC-020).
Run pytest — confirm all assertions green.

### Slice 3 — AppProject edge + contract YAML + smoke validations + profile-aware ACME (red → green)
Write failing assertions for AC-006, AC-007, AC-008, AC-010, AC-014. Implement:
- `appproject-edge.yaml` (all 4 envs): add cert-manager Issuer + Certificate to `namespaceResourceWhitelist` for `network` namespace (AC-010, FR-007).
- `module.contract.yaml`: add new optional env vars (FR-006, AC-016); document profile-aware ACME server default (NFR-SEC-004).
- `public_endpoints_smoke.sh`: add HTTPS listener check, external-dns annotation check, Issuer + Certificate manifest checks (AC-006, AC-007, AC-008).
- Verify `public_endpoints_init_env` profile-aware ACME server default (AC-014, NFR-SEC-004).
Run pytest — confirm all 20 AC assertions green.

### Slice 4 — Documentation + hardening review + publish
- Update `docs/platform/modules/public-endpoints/README.md` and bootstrap template mirror for TLS + external-dns design, including:
  - TLS Stack Execution Model + minimum TLS version note (NFR-SEC-002).
  - TLS Secret RBAC constraint: only Envoy Gateway controller SA may read the Secret (NFR-SEC-003).
  - Profile-aware ACME server defaults table (NFR-SEC-004).
  - HTTP plain-text security trade-off warning (NFR-SEC-005).
  - HSTS policy and network isolation design notes (NFR-SEC-006, NFR-SEC-007).
  - KMS module dependency section: encryption-at-rest for TLS Secret and ACME account key on `stackit-prod` (NFR-SEC-008).
  - Certificate `renewBefore` and expiry monitoring note (NFR-OBS-002).
  - Destroy warning for Certificate + Issuer lifecycle (NFR-REL-001).
  - Zero-trust parked items and follow-up triggers (BackendTLSPolicy, ReferenceGrant, OCSP, service mesh).
- Write ADR at `docs/blueprint/architecture/decisions/ADR-issue-248-public-endpoints-module.md`.
- Run full validation bundle: `make quality-sdd-check-all`, `make infra-validate`, `make quality-docs-check-changed`, `make docs-build`, `make docs-smoke`.
- Write `pr_context.md` and `hardening_review.md`.

## Change Strategy
- Migration/rollout sequence: cert-manager values update is additive (feature gate restart is graceful). AppProject whitelist changes are additive. New env vars have safe defaults so existing `PUBLIC_ENDPOINTS_ENABLED=false` consumers are unaffected.
- Backward compatibility policy: No existing env vars removed or renamed. The HTTPS listener is additive to the gateway template; existing HTTP routes continue to function.
- Rollback plan: Revert template changes and re-run `infra-public-endpoints-apply`. cert-manager restarts without the feature gate; issued certs remain in-cluster until manually deleted. DNS records created by SKE extension persist until zone TTL expires or destroyed explicitly.

## Validation Strategy (Shift-Left)
- Unit checks: `PYTHONPATH="$(pwd)" uv run pytest tests/infra/modules/public-endpoints/test_contract.py -v` — ≥10 assertions across all ACs.
- Contract checks: `make infra-validate`, `make quality-sdd-check-all`.
- Integration checks: `tests/infra/test_optional_modules.py::OptionalModulesTests::test_public_endpoints_module_flow` (existing integration test confirming gateway manifest presence, runtime state keys, and AppProject split).
- E2E checks: N/A — no live STACKIT cluster; smoke validates structural contracts against rendered artifacts.

## App Onboarding Contract (Normative)
- Required minimum make targets:
  - `apps-bootstrap` — N/A; infra/tooling-only change
  - `apps-smoke` — N/A; infra/tooling-only change
  - `backend-test-unit` — N/A; infra/tooling-only change
  - `backend-test-integration` — N/A; infra/tooling-only change
  - `backend-test-contracts` — N/A; infra/tooling-only change
  - `backend-test-e2e` — N/A; infra/tooling-only change
  - `touchpoints-test-unit` — N/A; infra/tooling-only change
  - `touchpoints-test-integration` — N/A; infra/tooling-only change
  - `touchpoints-test-contracts` — N/A; infra/tooling-only change
  - `touchpoints-test-e2e` — N/A; infra/tooling-only change
  - `test-unit-all` — N/A; infra/tooling-only change
  - `test-integration-all` — N/A; infra/tooling-only change
  - `test-contracts-all` — N/A; infra/tooling-only change
  - `test-e2e-all-local` — N/A; infra/tooling-only change
  - `infra-port-forward-start` — N/A; infra/tooling-only change
  - `infra-port-forward-stop` — N/A; infra/tooling-only change
  - `infra-port-forward-cleanup` — N/A; infra/tooling-only change
- App onboarding impact: no-impact
- Notes: HTTPS listener and external-dns annotation are opt-in via `PUBLIC_ENDPOINTS_ENABLED=true`; no generated consumer is affected unless they explicitly enable the module.

## Documentation Plan (Document Phase)
- Blueprint docs updates: `docs/platform/modules/public-endpoints/README.md` — add TLS Stack Execution Model, cert-manager Issuer setup, external-dns annotation, destroy warning for Certificate.
- Consumer docs updates: none (consumer HTTPRoute TLS is consumer responsibility, documented as guidance in README).
- Mermaid diagrams updated: architecture.md flowchart diagram (this file).
- Docs validation commands:
  - `make docs-build`
  - `make docs-smoke`

## Publish Preparation
- PR context file: `pr_context.md`
- Hardening review file: `hardening_review.md`
- Local smoke gate: N/A — no HTTP route handlers changed; this is infra manifest and script scope.
- Publish checklist:
  - include requirement/contract coverage
  - include key reviewer files (gateway template, public_endpoints.sh, appproject-edge.yaml, cert-manager.values.yaml, test_contract.py)
  - include validation evidence + rollback notes

## Operational Readiness
- Logging/metrics/traces: Existing `[public-endpoints]` log prefix covers all new script paths. cert-manager emits cert expiry metrics (opt-in via observability module). No new alerting added.
- Alerts/ownership: cert expiry monitoring out of scope for this work item; parked for observability module.
- Runbook updates: module README destroy warning section added for Certificate + Issuer lifecycle.

## Risks and Mitigations
- Risk: `gatewayHTTPRoute` challenge requires CRDs before cert-manager places the challenge HTTPRoute — mitigated by `public_endpoints_wait_for_gateway_api_crds` gate in deploy phase.
- Risk: cert-manager feature gate addition causes controller restart — mitigated by additive-only change; cert-manager restart is graceful and issued certs are unaffected.
