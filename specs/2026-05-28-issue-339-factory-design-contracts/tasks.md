# Tasks

## Gate Checks (Required Before Implementation)
- [x] G-001 Confirm `SPEC_READY=true` in `spec.md`
- [x] G-002 Confirm open questions and unresolved alternatives are `0`
- [x] G-003 Confirm required sign-offs are approved
- [x] G-004 Confirm `Applicable Guardrail Controls` section includes `SDD-C-###` IDs
- [x] G-005 Confirm `Implementation Stack Profile` section is fully populated

## Implementation
- [x] T-001 Create `docs/blueprint/autonomous-factory/` directory and author `design-contracts.md` with sections C1–C8, each ending in a `Referenced by:` line and any open decisions under `### Open Decisions`. C1–C4 written as identical conventions (FR-004 through FR-007). C2 carries the FR-005 SDD-artifact front-matter required-key set (`id`, `artifact_kind`, `work_item_slug`, `owner_team`, `schema_version`) with one worked example per `artifact_kind` value (`spec`, `adr`, `traceability`, `evidence-manifest`) — satisfies AC-013. C5/C6/C7 written with the three required subsections `### Identical rule`, `### Blueprint instance`, `### Consumer overlay` (FR-008/FR-009/FR-010). C7 identical rule covers nine minimum lifecycle-event fields (including `owner_team`) and pins the durable-bus emission contract (durability, replayability, async fire-and-forget, consumer-position tracking by subscribers) with the concrete STACKIT-managed durable-bus platform pick deferred to #337 Phase 0 under `### Open Decisions` — satisfies AC-014. C7 also carries the one-line cross-link noting downstream observers (Epic #343 Central Brain ingest) subscribe to the same bus and that schema changes go through #339 sign-off. C8 written with: four named surface categories from FR-013(a–d); per-item stability tier tags from FR-015; per-item extensibility tier tags from FR-017 (default `extensible`; FR-017(b) sealed list pinned exactly — including the C7 durable-bus emission rule and the C2 SDD-artifact front-matter required-key set added in this work); LiteLLM external-service configuration shape per FR-014; FR-018 consumer-extension discovery convention with one worked example per artifact kind (persona shadow, skill add, SDD step add); FR-019 semver compatibility posture; FR-020 `upstream-candidate: true` front-matter convention. Each contract section MUST avoid the literal deferred-decision placeholder token outside `### Open Decisions` subsections (per FR-003); the literal placeholder token is enumerated once in the deliverable's review-conventions preamble (so the blueprint-side spec.md/tasks.md/traceability.md never carry it and the `unresolved_marker_tokens` validator stays green at SPEC_READY=true).
- [x] T-002 Author `docs/blueprint/architecture/decisions/ADR-issue-339-factory-design-contracts.md` (Status: proposed) with the `flowchart TD` Mermaid diagram including C8 node and Context D consumer-inheritance edge, and relative link to the deliverable.
- [x] T-003 Verify the new `docs/blueprint/autonomous-factory/` subdirectory and the design-contracts deliverable appear in the rendered docs navigation after `make docs-build`; no edits to existing blueprint docs required by this work item.
- [x] T-004 Verify the design-contracts deliverable is reachable to consumer repos via the existing blueprint `contract.yaml` documentation surface that consumer repos already inherit per Contract C8; no per-consumer-repo edits in this work item.
- [x] T-005 (Q-4 RESOLVED ahead of SPEC_READY in PR #340 comment https://github.com/sbonoc/stackit-platform-blueprint/pull/340#issuecomment-4563422931 — Option A: LiteLLM access lives at `spec.factory_contract.litellm` under a new top-level `spec.factory_contract:` block in `blueprint/contract.yaml`, grouping every factory per-instance value under one subtree. Field shape: `gateway_url` (string), `auth_secret_ref.store` + `auth_secret_ref.key` (ESO ClusterSecretStore reference), `model_allowlist` (list of strings). Final wording authored in T-001 Slice 1. SPEC_READY=true.)
- [x] T-006 (Q-5 RESOLVED ahead of SPEC_READY — Phase 1 factory upgrade-process ticket filed as #342 with the agreed scope (semver compatibility posture, per-artifact versioning, extended `/blueprint-consumer-upgrade` for factory artifacts, first-adopter upgrade roundtrip AC on Epic #332). #342 substituted into Contract C8 `Referenced by:` lines for FR-019 and FR-020. SPEC_READY=true.)

## Test Automation
- [x] T-101 Add or update unit tests — N/A (documentation-only change; no code units)
- [x] T-102 Add or update contract tests — N/A (no API/event/Pact contracts added; the C7 schema definition is documentation, consumers ship their own contract tests)
- [x] T-103 For any new or modified filter/payload-transform route, verify a positive-path unit test exists — N/A (no filter/transform logic)
- [x] T-104 Translate any reproducible pre-PR smoke/curl/deterministic-check finding into a failing automated test first — N/A (no smoke/curl path; docs validation is `make docs-smoke`)
- [x] T-105 Add boundary/integration tests where required — N/A (no integration boundaries introduced)

## Accessibility Testing (Normative — mark N/A with rationale for non-UI specs)
- [x] T-A01 Confirm NFR-A11Y-001 compliance scope is declared in `spec.md` — declared as `N/A — internal governance documentation. No UI surface is introduced or modified by this work item.`
- [x] T-A02 Run axe-core WCAG 2.1 AA scan — N/A (no UI surface)
- [x] T-A03 Verify keyboard operability — N/A (no UI surface)
- [x] T-A04 Verify focus indicator visible on focused interactive elements — N/A (no UI surface)
- [x] T-A05 Verify all non-text content has a programmatic label — N/A (no UI surface)

## Validation and Release Readiness
- [x] T-201 Run required Make validation bundles (`make quality-sdd-check`, `make docs-build`, `make docs-smoke`)
- [ ] T-202 Attach evidence to traceability document (`make quality-sdd-check` summary, `make docs-build` summary, `make docs-smoke` summary in `evidence_manifest.json`)
- [x] T-203 Confirm no stale TODOs/dead code/drift — verify zero deferred-decision placeholders (per FR-003) outside `### Open Decisions` subsections in the deliverable; verify no orphan tickets in `Referenced by:` lines
- [x] T-204 Run documentation validation (`make docs-build` and `make docs-smoke`)
- [ ] T-205 Run hardening review validation bundle (`make quality-hardening-review`)

## Publish
- [ ] P-001 Update `hardening_review.md` with repository-wide findings fixed and proposals-only section
- [ ] P-002 Update `pr_context.md` with requirement/contract coverage, key reviewer files, validation evidence, and rollback notes
- [ ] P-003 Ensure PR description follows repository template headings and references `pr_context.md`

## App Onboarding Minimum Targets (Normative)
- [x] A-001 `apps-bootstrap` and `apps-smoke` are implemented and verified for the affected app scope — N/A (no app scope affected by this documentation-only work item)
- [x] A-002 Backend app lanes (`backend-test-unit`, `backend-test-integration`, `backend-test-contracts`, `backend-test-e2e`) are available — N/A (no app scope affected)
- [x] A-003 Frontend app lanes (`touchpoints-test-unit`, `touchpoints-test-integration`, `touchpoints-test-contracts`, `touchpoints-test-e2e`) are available — N/A (no app scope affected)
- [x] A-004 Aggregate gates (`test-unit-all`, `test-integration-all`, `test-contracts-all`, `test-e2e-all-local`) are available — N/A (no app scope affected)
- [x] A-005 Port-forward operational wrappers (`infra-port-forward-start`, `infra-port-forward-stop`, `infra-port-forward-cleanup`) are available — N/A (no app scope affected)
