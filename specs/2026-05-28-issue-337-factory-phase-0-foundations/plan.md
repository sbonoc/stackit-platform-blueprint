# Implementation Plan

## Implementation Start Gate
- Implementation tasks MUST remain unchecked until `SPEC_READY=true`.
- If required inputs are missing, add `BLOCKED_MISSING_INPUTS` in `spec.md` and keep the gate closed.

## Constitution Gates (Pre-Implementation)
- Simplicity gate: eleven ADRs (one per Phase 0 decision plus this meta-ADR), three short autonomous-factory documents, one CODEOWNERS edit, reciprocal updates to one existing document. No abstractions beyond the ADR-per-decision and document-per-topic shape; no schemas, registries, or sidecar tooling.
- Anti-abstraction gate: plain Markdown rendered by the existing `docs/blueprint/` pipeline; no new templating, no new YAML/JSON sidecars beyond the existing `template_sync_allowlist` extension.
- Integration-first testing gate: `make docs-build`, `make docs-smoke`, `make quality-sdd-check` pass on both `main` (baseline) and the feature branch (post-implementation). No new link or anchor regressions.
- Positive-path filter/transform test gate: N/A — no filter or payload-transform logic in scope.
- Finding-to-test translation gate: N/A — no deterministic smoke or `curl` execution path; `make docs-smoke` is the documentation validation check.

## Delivery Slices
1. Slice 1 — Open Decisions resolution gate (✓ COMPLETE Step 02/03). Q-1 through Q-7 resolved in commits `27b89e1` + `ab57634`; all four canonical sign-offs recorded; SPEC_READY=true achieved in commit `715014a` (Step 03). Meta-ADR `Status: approved` set in the same Step 03 commit.
2. Slice 2 — Author the ten content ADRs. For each FR-001 through FR-010, create the matching `docs/blueprint/architecture/decisions/ADR-issue-337-<topic>.md` with `Status: approved` from inception (this PR's spec-level sign-off envelope covers them per the meta-ADR pattern — see traceability Follow-up 8). Each ADR includes Context, Decision Drivers, Options Considered, Decision, Consequences, References sections; each ADR cites its #339 contract dependency (e.g., FR-005 cites #339 NFR-SEC-001 verbatim; FR-001 cites #339 Contract C3); each ADR carries the extensibility-tier classification statement from its matching FR. Slice 2 exit criterion: ten ADR files exist; all link back to the meta-ADR; `make docs-build` shows them in the ADR index.
3. Slice 3 — Author the three autonomous-factory documents. Create `docs/blueprint/autonomous-factory/instrumentation-plan.md` per FR-012 + FR-013 (declaring durable-bus pick from Q-5, dashboard target from Q-4, retention, owner, per-`owner_team` breakdown shape, source-of-truth field per metric per NFR-OBS-001). Create `docs/blueprint/autonomous-factory/pre-factory-baselines.md` per FR-014 (four baseline values measured over the Q-6 window with per-`owner_team` breakdown row). Create `docs/blueprint/autonomous-factory/triage-decomposition-data-feed.md` per FR-015 (Markdown table; one row per ticket cycle; `### Sample Size` subsection if fewer than 30 cycles per Q-7). Slice 3 exit criterion: three documents exist; all pass `make docs-build` + `make docs-smoke`.
4. Slice 4 — Populate `.github/CODEOWNERS` per FR-011. Replace the placeholder content with two layers: `# === Gate 1: Spec sign-off layer ===` mapping the four canonical sign-off roles to the Q-3 team slugs, and `# === Gate 2: Bounded-context merge layer ===` mapping each bounded context to its team. Preserve existing ownership boundaries declared in `AGENTS.md` (docs, scripts, Make targets). Verify the file contains zero `@your-org/...` placeholders. Slice 4 exit criterion: AC-002 satisfied; Operations confirms team membership ≥ 2 for every named team (or, if Q-3 Option C is chosen, records the deferred provisioning condition in a CODEOWNERS comment block).
5. Slice 5 — Reciprocal updates to #339 design-contracts.md. Per FR-016: populate C6 `### Blueprint instance` with the Q-3 gate-1 slugs + bounded-context enumeration; populate C7 `### Blueprint instance` with `stackit-managed-grafana` + Q-4 retention + Q-4 owner; resolve C7 `### Open Decisions` durable-bus pick to the Q-5 value. Per FR-017: extend C8 to enumerate the ten content ADRs with stability tier `stable` + extensibility tier per each FR's classification statement; enumerate the three autonomous-factory documents with stability tier `stable` + extensibility tier `extensible`. Regenerate the #339 spec's `evidence_manifest.json` SHA-256 entries for `design-contracts.md` and its bootstrap mirror. Slice 5 exit criterion: AC-006 satisfied; `make quality-sdd-check` passes against #339's spec directory.
6. Slice 6 — `template_sync_allowlist` extension + bootstrap mirror sync. Extend `blueprint/contract.yaml` `template_sync_allowlist` to include the three autonomous-factory documents authored in Slice 3. Run `python3 scripts/lib/docs/sync_blueprint_template_docs.py`. Verify zero diff on re-run (AC-009). Slice 6 exit criterion: bootstrap mirror under `scripts/templates/blueprint/bootstrap/docs/blueprint/autonomous-factory/` carries byte-identical copies of the three documents.
7. Slice 7 — Empty `.agents/personas/consumer/.gitkeep` per FR-018. Create the directory if absent and the `.gitkeep` file. Slice 7 exit criterion: AC-010 satisfied (the directory exists for the OpenHands loader discoverability precondition).
8. Slice 8 — Validation and publish prep. Run `make quality-sdd-check`, `make docs-build`, `make docs-smoke`, `make quality-hardening-review`. Record results in `evidence_manifest.json` via `make spec-evidence-manifest`. Sign-offs are already recorded (Step 03 commit `715014a`); meta-ADR already at `Status: approved`; ten content ADRs are authored in Slice 2 with `Status: approved` from inception under this PR's spec-level sign-off envelope — no separate status-flip pass needed in Slice 8. Slice 8 exit criterion: AC-001, AC-003, AC-004, AC-005, AC-007, AC-008, AC-011 all satisfied; publish artifacts (`pr_context.md`, `hardening_review.md`, `evidence_manifest.json`) finalized for Step 07 PR-packager.

## Change Strategy
- Migration/rollout sequence: additive only. New files (ten content ADRs, meta-ADR, three autonomous-factory documents, `.agents/personas/consumer/.gitkeep`). One existing file replaced (`.github/CODEOWNERS`). One existing file edited in scoped subsections (`docs/blueprint/autonomous-factory/design-contracts.md` C6/C7/C8). One bootstrap mirror added per `template_sync_allowlist` extension. One `blueprint/contract.yaml` field extended.
- Backward compatibility policy: no consumers of these new files exist at PR-open time; consumers are Phase 1 tickets that adopt the ADRs and documents during their own implementation. The CODEOWNERS replacement removes placeholder routing — at merge the placeholder is replaced by the populated routing; mitigation is to confirm no in-flight PRs require the placeholder routing at merge.
- Rollback plan: revert the PR. No runtime side effects; no migrations to undo. Phase 1 tickets that begin work after this PR merges MUST treat a rollback as equivalent to "Phase 0 decisions not yet recorded" and pause their dependent work. The CODEOWNERS revert restores placeholder routing, which is acceptable rollback state because no factory `agent-ready` label can be applied without a populated CODEOWNERS by definition.

## Validation Strategy (Shift-Left)
- Unit checks: N/A — no code units.
- Contract checks: N/A — no OpenAPI/Pact contracts.
- Integration checks: N/A — no integration code.
- E2E checks: N/A — no UI or end-to-end runtime flow.
- Documentation checks: `make docs-build` (deterministic build), `make docs-smoke` (link/anchor regressions). `make quality-sdd-check` validates this spec set, the reciprocal #339 spec set, and the ten new ADRs. `make quality-hardening-review` validates the hardening posture.

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
- Notes: governance-documentation change; no make targets added, modified, or removed.

## Documentation Plan (Document Phase)
- Blueprint docs updates: ten new ADRs under `docs/blueprint/architecture/decisions/` (the meta-ADR plus FR-001…FR-010 content ADRs) + three new governance documents under `docs/blueprint/autonomous-factory/` (instrumentation plan, pre-factory baselines, triage+decomposition data feed) + reciprocal C6/C7/C8 edits to the existing `docs/blueprint/autonomous-factory/design-contracts.md` per FR-016/FR-017 — enumerated below.
  - `docs/blueprint/architecture/decisions/ADR-issue-337-factory-phase-0-foundations.md` (new — meta-ADR)
  - `docs/blueprint/architecture/decisions/ADR-issue-337-llm-model-router-policy.md` (new)
  - `docs/blueprint/architecture/decisions/ADR-issue-337-persona-skill-contract.md` (new)
  - `docs/blueprint/architecture/decisions/ADR-issue-337-trigger-authorization-model.md` (new)
  - `docs/blueprint/architecture/decisions/ADR-issue-337-sovereignty-zdr-posture.md` (new)
  - `docs/blueprint/architecture/decisions/ADR-issue-337-separation-of-duties-at-factory-velocity.md` (new)
  - `docs/blueprint/architecture/decisions/ADR-issue-337-reject-rerun-cap.md` (new)
  - `docs/blueprint/architecture/decisions/ADR-issue-337-per-ticket-wall-clock-cost-ceiling.md` (new)
  - `docs/blueprint/architecture/decisions/ADR-issue-337-reviewer-model-heterogeneity.md` (new)
  - `docs/blueprint/architecture/decisions/ADR-issue-337-triage-size-threshold.md` (new)
  - `docs/blueprint/architecture/decisions/ADR-issue-337-light-decomposition-policy.md` (new)
  - `docs/blueprint/autonomous-factory/instrumentation-plan.md` (new — FR-012/FR-013)
  - `docs/blueprint/autonomous-factory/pre-factory-baselines.md` (new — FR-014)
  - `docs/blueprint/autonomous-factory/triage-decomposition-data-feed.md` (new — FR-015)
  - `docs/blueprint/autonomous-factory/design-contracts.md` (modified — C6/C7 `### Blueprint instance`, C7 `### Open Decisions`, C8 ADR enumeration per FR-016/FR-017)
- Consumer docs updates: the three autonomous-factory documents authored here are consumer-facing surface (#339 Contract C8 category (a)). Consumer repos receive them via the bootstrap template mirror per the `template_sync_allowlist` extension; no per-consumer-repo edits in this work item.
- Mermaid diagrams updated: meta-ADR carries a `flowchart TD` diagram showing the eleven-ADR + three-document fan-out to Phase 1 tickets and to #338 (caption already authored in `ADR-issue-337-factory-phase-0-foundations.md`).
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
  - include requirement/contract coverage (FR-001 through FR-018; NFR-SEC-001, NFR-SEC-002, NFR-OBS-001, NFR-REL-001, NFR-OPS-001, NFR-OPS-002; AC-001 through AC-011)
  - include key reviewer files (eleven ADRs, three autonomous-factory documents, `.github/CODEOWNERS`, the #339 design-contracts.md edit set)
  - include validation evidence (`make quality-sdd-check`, `make docs-build`, `make docs-smoke`, `make quality-hardening-review` results) + rollback notes (single-PR revert; no runtime impact; reverting invalidates Phase 1 ADR citations until restored and reverts CODEOWNERS to placeholder state which gates the first factory `agent-ready` label)

## Operational Readiness
- Logging/metrics/traces: none added by this work item. FR-012 declares what WILL be observed once Phase 1 lands; this is the plan, not the implementer. The #339 Contract C7 event schema referenced by FR-012 is also a definition, not an emitter (emitters land in #335 and #336).
- Alerts/ownership: none added. Document maintenance ownership: Architecture for the ten content ADRs and meta-ADR; Operations for the instrumentation plan + baselines + CODEOWNERS; Security co-signs FR-003/FR-004/FR-005 ADRs; Product co-signs FR-007/FR-008 ADRs. Amendments to any ADR follow the same SDD/sign-off flow as the original.
- Runbook updates: none.

## Risks and Mitigations
- Risk 1 — Open Decisions Q-1 through Q-7 block SPEC_READY transition. Mitigation: each question carries an Agent recommendation with rationale and a fallback option; user can ratify Option A for the majority in one PR review pass; Q-3 has a parking option (C) that preserves AC satisfaction if team provisioning is not yet complete; Q-5 has a 1-day availability spike bounded as a Phase 0 prerequisite. SPEC_READY can flip to `true` once the four canonical sign-offs are recorded and every Open Decision is either resolved or explicitly parked under `### Open Decisions` in a downstream-tracked deferral.
- Risk 2 — Reciprocal #339 design-contracts.md edits create perceived re-litigation of #339's already-signed-off sections. Mitigation: edits are confined to subsections explicitly deferred by #339 (Q-2, Q-3, durable-bus pick, C8 ADR enumeration); the `### Identical rule` content is untouched; the four sign-offs on THIS work item cover the deltas without re-opening #339; the #339 spec's `evidence_manifest.json` SHA-256 is regenerated to reflect the new design-contracts.md content (no separate sign-off required).
- Risk 3 — Reviewer fatigue on a large PR (eleven ADRs + three documents + CODEOWNERS + reciprocal edits + bootstrap mirror). Mitigation: per-family review allocation (Architecture/Operations/Security/Product); per-artifact revertibility (NFR-REL-001); #339 precedent demonstrates sign-off velocity at this scope.
- Risk 4 — Bootstrap mirror sync drift if the three autonomous-factory documents are edited later without re-running `sync_blueprint_template_docs.py`. Mitigation: AC-009 requires zero-diff verification post-sync; the `template_sync_allowlist` enforces detection at the next `make quality-sdd-check` run.
- Risk 5 — `.github/CODEOWNERS` regression if a future PR removes a team slug without updating gate-1 + gate-2 routing. Mitigation: the meta-ADR documents the two-layer routing as the C6 identical rule applied to the blueprint instance; future edits to CODEOWNERS land via a fresh SDD work item with Operations co-sign per the established convention.
