# Implementation Plan

## Implementation Start Gate
- Implementation tasks MUST remain unchecked until `SPEC_READY=true`.
- If required inputs are missing, add `BLOCKED_MISSING_INPUTS` in `spec.md` and keep the gate closed.

## Constitution Gates (Pre-Implementation)
- Simplicity gate:
  - Single deliverable file + single summary ADR. No abstractions introduced beyond what the seven contract sections require.
  - Avoid speculative future-proof abstractions: the document records what is decided today, with explicit `### Open Decisions` subsections for what is deferred.
- Anti-abstraction gate:
  - No wrapper layers. The document is plain Markdown rendered by the existing `docs/blueprint/` pipeline.
  - No additional schemas, registries, or YAML/JSON sidecars beyond the Contract C7 event-schema definition expressed inline.
- Integration-first testing gate:
  - Pre-Implementation: confirm `make docs-build` and `make docs-smoke` exit clean on `main` (baseline).
  - Implementation: rerun `make docs-build` and `make docs-smoke` after adding the deliverable and ADR; both MUST pass with no new link or anchor regressions.
- Positive-path filter/transform test gate:
  - N/A — no filter or payload-transform logic in scope. No code paths are added.
- Finding-to-test translation gate:
  - N/A — no deterministic smoke or `curl` execution path exists for this documentation-only work item. If `make docs-smoke` surfaces a finding, the fix is a documentation edit committed in the same PR.

## Delivery Slices
1. Slice 1 — Author the deliverable. Create `docs/blueprint/autonomous-factory/design-contracts.md` with the eight contract sections C1–C8, each ending in a `Referenced by:` line. C1–C4 written as identical conventions for blueprint + consumer repos. C5/C6/C7 written with the three required subsections (`### Identical rule`, `### Blueprint instance`, `### Consumer overlay`). C8 written with: (a) the four named surface categories from FR-013 (a–d); (b) per-item stability tier tags from FR-015 (`stable`/`preview`/`internal`); (c) per-item extensibility tier tags from FR-017 (`sealed`/`parameterized`/`extensible`) with default `extensible` and the FR-017(b) sealed list pinned exactly; (d) the LiteLLM external-service configuration shape per FR-014, written at `spec.factory_contract.litellm` under a new top-level `spec.factory_contract:` block in `blueprint/contract.yaml` (Q-4 RESOLVED — Option A); (e) the consumer-extension discovery convention from FR-018 with one worked example per artifact kind; (f) the semver compatibility posture from FR-019; (g) the `upstream-candidate: true` front-matter convention from FR-020. Open Decisions written under explicit `### Open Decisions` subsections naming the deferring ticket: Q-1 in C5 → blueprint-instance value resolved as `stackit-factory-bot`; reserve+verify in #334. Q-2 in C6 → blueprint-instance topology resolved as four flat sign-off team slugs `@sbonoc/factory-{product,architecture,security,operations}` + separate per-bounded-context teams; concrete team provisioning and full bounded-context list in #337. Q-3 in C7 → blueprint-instance dashboard target resolved as STACKIT-managed Grafana via the existing observability module; concrete dashboard URLs in #337. Q-4 in C8 → RESOLVED in this PR (see point (d) above). Q-5 in C8 → RESOLVED: Phase 1 factory upgrade-process ticket filed as #342; #342 substituted into FR-019 + AC-012 `Referenced by:` lines.
2. Slice 2 — Author the ADR. Create `docs/blueprint/architecture/decisions/ADR-issue-339-factory-design-contracts.md` with `Status: proposed`, linking the deliverable by relative path. ADR Mermaid diagram includes C8 and consumer-side edge to Context D. On all four sign-offs received, flip `Status: approved` (Step 8 PR-packager work).
3. Slice 3 — Documentation validation. Run `make docs-build` and `make docs-smoke`. Fix any link/anchor regressions in the same slice.
4. Slice 4 — Sign-off cycle. Sign-off comments from Product, Architecture, Security, Operations recorded in `spec.md` per `AGENTS.md § Sign-off Policy`. SPEC_READY flipped to `true` when all four are recorded (Q-4 and Q-5 already resolved; Q-1/Q-2/Q-3 resolved with concrete-value provisioning deferred to #334/#337 under `### Open Decisions`).

## Change Strategy
- Migration/rollout sequence: none — additive only. New files only, no edits to existing documents.
- Backward compatibility policy: N/A — no consumers of these new files exist at PR-open time; consumers are Phase 1 tickets that adopt the contracts during their own implementation.
- Rollback plan: revert the PR. No runtime side effects; no migrations to undo. Phase 1 tickets that begin work after this PR merges MUST treat a rollback as equivalent to "design contracts not yet decided" and pause their dependent work.

## Validation Strategy (Shift-Left)
- Unit checks: N/A — no code units.
- Contract checks: N/A — no OpenAPI/Pact contracts.
- Integration checks: N/A — no integration code.
- E2E checks: N/A — no UI or end-to-end runtime flow.
- Documentation checks: `make docs-build` (deterministic build), `make docs-smoke` (link/anchor regressions). `make quality-sdd-check` validates the spec set itself.

## App Onboarding Contract (Normative)
- Required minimum make targets:
  - `apps-bootstrap`
  - `apps-smoke`
  - `backend-test-unit`
  - `backend-test-integration`
  - `backend-test-contracts`
  - `backend-test-e2e`
  - `touchpoints-test-unit`
  - `touchpoints-test-integration`
  - `touchpoints-test-contracts`
  - `touchpoints-test-e2e`
  - `test-unit-all`
  - `test-integration-all`
  - `test-contracts-all`
  - `test-e2e-all-local`
  - `infra-port-forward-start`
  - `infra-port-forward-stop`
  - `infra-port-forward-cleanup`
- App onboarding impact: no-impact
- Notes: documentation-only change; no make targets added, modified, or removed.

## Documentation Plan (Document Phase)
- Blueprint docs updates:
  - `docs/blueprint/autonomous-factory/design-contracts.md` (new — the deliverable)
  - `docs/blueprint/architecture/decisions/ADR-issue-339-factory-design-contracts.md` (new — the summary ADR)
- Consumer docs updates: this document itself is a consumer-facing surface (Contract C8 enumerates `docs/blueprint/autonomous-factory/` and `docs/blueprint/architecture/decisions/` as part of the surface consumer repos inherit). No edits to existing consumer-facing docs are required by this work item; consumer repos discover the design contracts via the existing blueprint `contract.yaml` inheritance mechanism that already exposes `docs/blueprint/` content to consumers.
- Mermaid diagrams updated: ADR Mermaid diagram chosen: `flowchart TD` showing the eight contracts as nodes with dependency edges to consumer tickets (#333–#338, plus #341 Phase 0 Confidential K8s and #342 Phase 1 factory upgrade process) and a consumer-side edge to Context D (per-consumer factory instances). Caption: "Design-contract C1–C8 dependency edges — one node per contract, one outbound edge per `Referenced by:` entry; consumer-side edge represents Context D inheritance via blueprint `contract.yaml`, including the FR-018 namespaced-extension convention and the FR-019 semver factory contract version."
- Docs validation commands:
  - `make docs-build`
  - `make docs-smoke`

## Publish Preparation
- PR context file:
  - `pr_context.md`
- Hardening review file:
  - `hardening_review.md`
- Local smoke gate (HTTP route/filter changes):
  - N/A — no HTTP routes, query/filter logic, or new API endpoints in scope. Local smoke gate does not apply.
- Publish checklist:
  - include requirement/contract coverage (FR-001 through FR-020; NFR-SEC-001, NFR-OBS-001, NFR-REL-001, NFR-OPS-001, NFR-OPS-002; AC-001 through AC-012)
  - include key reviewer files (`docs/blueprint/autonomous-factory/design-contracts.md`, `docs/blueprint/architecture/decisions/ADR-issue-339-factory-design-contracts.md`)
  - include validation evidence (`make quality-sdd-check`, `make docs-build`, `make docs-smoke` results) + rollback notes (single-PR revert; no runtime impact; reverting invalidates consumer C8 inheritance until restored)

## Operational Readiness
- Logging/metrics/traces: none added by this work item. Contract C7 defines the event schema for downstream consumers; this is a definition, not an emitter.
- Alerts/ownership: none added. Document maintenance ownership: Architecture (with Security/Operations co-sign on amendments).
- Runbook updates: none.

## Risks and Mitigations
- Risk 1 — sign-off delay on three Open Decisions blocks SPEC_READY transition (RESOLVED 2026-05-28): Q-1/Q-2/Q-3 picked with concrete-value provisioning deferred per their `### Open Decisions` entries (Q-1 → #334, Q-2 → #337, Q-3 → #337). SPEC_READY can flip true once the four canonical sign-offs land — the deferred concrete-value provisioning is enforced as a non-closure condition on the deferring tickets, not on this PR.
- Risk 2 — `Referenced by:` lines drift as #333–#337 evolve scope -> mitigation: NFR-REL-001 mandates same-PR updates whenever a downstream ticket changes scope; reviewers enforce on the dependent ticket's PR.
- Risk 3 — first SDD application on factory governance sets a too-loose bar that downstream factory work inherits -> mitigation: chose full SDD ceremony (10 artifacts) over the chore bypass track; treat this PR's review bar as the reference quality bar for #333–#337.
