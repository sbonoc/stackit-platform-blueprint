# Specification

## Spec Readiness Gate (Blocking)
<!-- SPEC_PRODUCT_READY=true: intake gate — Product sign-off only; unlocks agent ADR drafting.
     SPEC_READY=true: implementation gate — all sign-offs required; unlocks coding. -->
- SPEC_READY: false
- SPEC_PRODUCT_READY: false
- Open questions count: 6
- Unresolved alternatives count: 0
- Unresolved TODO markers count: 0
- Pending assumptions count: 0
- Open clarification markers count: 6
- Product sign-off: pending
- Architecture sign-off: pending
- Security sign-off: pending
- Operations sign-off: pending
- Missing input blocker token: BLOCKED_MISSING_INPUTS
- ADR path: docs/blueprint/architecture/decisions/ADR-issue-347-human-sdd-c7-symmetry.md
- ADR status: proposed
- SPEC_READY_EXCEPTION: none
- authorized-by: none

## Applicable Guardrail Controls (Normative)
- Applicable control IDs: SDD-C-001, SDD-C-002, SDD-C-003, SDD-C-004, SDD-C-005, SDD-C-006, SDD-C-007, SDD-C-008, SDD-C-009, SDD-C-010, SDD-C-011, SDD-C-012, SDD-C-013, SDD-C-014, SDD-C-016, SDD-C-017, SDD-C-019, SDD-C-020, SDD-C-021, SDD-C-023, SDD-C-024
- Control exception rationale: none

## Implementation Stack Profile (Normative)
- Backend stack profile: python_plus_fastapi_pydantic_v2
- Frontend stack profile: vue_router_pinia_onyx
- Test automation profile: pytest_vitest_playwright_pact
- Agent execution model: specialized-subagents-isolated-worktrees
- Managed service preference: stackit-managed-first
- Managed service exception rationale: none
- Runtime profile: local-first-docker-desktop-kubernetes
- Local Kubernetes context policy: docker-desktop-preferred
- Local provisioning stack: crossplane-plus-helm
- Runtime identity baseline: eso-plus-argocd-plus-keycloak
- Local-first exception rationale: none

## Objective
- Business outcome: Human-driven SDD sessions emit Contract C7 lifecycle events with the same eleven-field minimum schema, the same durable-bus pipeline, and the same dedupe + replay guarantees as autonomous factory runs — so the metrics dashboard, the FR-008 reviewer-heterogeneity audit, and the future Central Brain index (Epic #343) see one coherent SDD timeline regardless of who (or what) drove the work.
- Success metric: After this work item ships, ≥ 95% of new PRs opened on the blueprint repo carry an `artifacts/c7/<slug>.jsonl` sink with ≥ 1 C7 event per executed SDD step, measured over the first 30 PRs post-merge; opt-outs (counted as `c7-emission-opted-out` extension events on the bus) MUST be ≤ 5% of new PRs over the same window.

## Normative Requirements

### Functional Requirements (Normative)
- FR-001 The C7 `emitter` JSON Schema enum (`docs/blueprint/autonomous-factory/design-contracts.md` Contract C7 § Emission mechanism) MUST be widened from `{orchestrator, webhook-handler}` to EXACTLY THREE values `{orchestrator, webhook-handler, local-cli}`. Any value outside this enum MUST be REJECTED by subscribers.
- FR-002 Every SDD step skill listed in `CLAUDE.md` § Skills (`blueprint-sdd-step01-intake` through `blueprint-sdd-step07-pr-packager`) MUST emit EXACTLY ONE C7 lifecycle event per step execution via a deterministic shared helper. The helper MUST be the sole writer of `emitter: local-cli` C7 events. LLM personas MUST NOT write C7 envelope fields and MUST NOT have direct write access to the JSONL sink.
- FR-003 The helper MUST append emitted events to `artifacts/c7/<work-item-slug>.jsonl` in the work-item working tree, one canonical JSON object per line, in append-only order. The file MUST be committed to the work-item branch.
- FR-004 For `emitter: local-cli` events the `event_id` field MUST be derived as `sha256(ticket_id|phase|rerun_round|emitter)` — the four-input variant. The five-input webhook discriminator variant MUST NOT be used; the JSONL append is the local single source of truth.
- FR-005 For `emitter: local-cli` events the `persona` field MUST be the SDD step skill basename (e.g., `blueprint-sdd-step01-intake`). The `model` field MUST be the best-effort LLM model identifier exposed by the operator's coding assistant, OR the sealed sentinel string `unknown` when no model identifier is resolvable. The eleven-field minimum schema MUST remain typed `string` and required — no nullable types and no emitter-conditional required-set variants.
- FR-006 Every C7 event from any emitter MUST carry the extension field `execution_mode` (string enum, two values): `autonomous` when `emitter ∈ {orchestrator, webhook-handler}`, `human-assisted` when `emitter: local-cli`. The field MUST be carried under `additionalProperties: true` and MUST NOT be added to the eleven-field required minimum.
- FR-007 Emission MUST be opt-out-able via a sealed mechanism: the environment variable `BLUEPRINT_SDD_C7_EMIT=0` SHALL suppress JSONL writes for the current shell session. The opt-out SHALL be audited: the first SDD step executed under opt-out MUST emit EXACTLY ONE `c7-emission-opted-out` extension event with reason carried in `additionalProperties.opt_out_reason`; subsequent steps under the same opt-out scope MUST NOT re-emit.

  > **[NEEDS CLARIFICATION: Q-1 — Opt-out mechanism surface — env var only, CLI flag only, or both?]**
  >
  > **Options:**
  > - **A)** Env var only (`BLUEPRINT_SDD_C7_EMIT=0`) — single surface, no flag plumbing through 7 skills + shell scripts. (Agent recommendation.)
  > - **B)** CLI flag only (`--no-c7` on every step skill) — discoverable via `--help`, but requires consistent flag plumbing in every skill runbook.
  > - **C)** Both — maximum discoverability, but doubles the surface to test and document.
  >
  > **Agent recommendation:** Option A. Env var travels through subshell invocation without per-skill plumbing; the opt-out audit event captures the reason so discoverability is not lost.

- FR-008 The #336 webhook handler MUST ingest `artifacts/c7/<work-item-slug>.jsonl` from the PR head SHA on EXACTLY THREE GitHub PR events: `pull_request.opened`, `pull_request.synchronize`, `pull_request.reopened`. Ingest MUST validate each JSONL line against the (amended) C7 JSON Schema, dedupe by `event_id`, and republish onto the durable bus with `emitter: local-cli` preserved.
- FR-009 Ingest MUST be idempotent: re-running ingest on the same JSONL contents MUST produce ZERO new bus emissions. Dedupe MUST be performed by the subscriber-side `event_id` check defined in Contract C7 § Emission idempotency.
- FR-010 Contract C7 (`docs/blueprint/autonomous-factory/design-contracts.md`) MUST be amended to: (a) widen issue #339 sealed-emitter rule from two emitters to three; (b) widen the JSON Schema `emitter.enum` to include `local-cli`; (c) extend the `persona` and `model` field descriptions to enumerate the `local-cli` sentinel rules; (d) document `execution_mode` in the extension-field vocabulary; (e) document the four-input `event_id` derivation for `local-cli`. The bootstrap mirror at `scripts/templates/blueprint/bootstrap/docs/blueprint/autonomous-factory/design-contracts.md` MUST be re-synced via `scripts/lib/docs/sync_blueprint_template_docs.py`.
- FR-011 A new ADR `docs/blueprint/architecture/decisions/ADR-issue-347-human-sdd-c7-symmetry.md` MUST be authored (Status: proposed at PR open, advanced to accepted on merge). The ADR MUST record decisions D-1 through D-4 from issue #347 verbatim and MUST reference Contract C7 + issue #339 sealed-emitter rule + `ADR-issue-337-c7-emission-mechanism.md` as the architectural baseline being extended.
- FR-012 Every `.agents/skills/blueprint-sdd-step*/SKILL.md` (seven skills) MUST receive a uniform "## C7 Emission" section that instructs the skill to invoke the shared helper at step boundary. The section text MUST be identical across all seven skills (modulo the per-skill `phase` enum value).
- FR-013 A `.gitattributes` rule `artifacts/c7/*.jsonl  linguist-generated=true  diff=none` MUST be added so PR diff renderers hide the JSONL sink by default.
- FR-014 Backfill of historical PRs MUST NOT be performed. Only PRs opened after this work item merges are audited under the `local-cli` emission surface.

### Non-Functional Requirements (Normative)
- NFR-SEC-001 The shared helper (`scripts/lib/sdd/c7_emit.py`) MUST be the sole writer of `emitter: local-cli` C7 events. LLM personas (Claude Code, Codex, Cursor, etc.) MUST NOT bypass the helper to write JSONL lines directly. This preserves the issue #339 sealed-emitter rule anti-LLM-hallucination property: the LLM calls the skill as a tool; the skill (deterministic Python) computes the envelope and appends.
- NFR-SEC-002 The #336 webhook handler MUST authenticate its GitHub contents API fetch using its existing GitHub App installation token. No new credential surface (PAT, deploy key, fine-grained token) MUST be introduced.
- NFR-OBS-001 Every event emitted under the `local-cli` surface MUST be observable on the metrics dashboard (Contract C7 § Blueprint instance) with `execution_mode` available as a Grafana panel facet (`autonomous` vs `human-assisted` segmentation).
- NFR-OBS-002 The FR-008 reviewer-model-heterogeneity audit predicate (defined in `ADR-issue-337-reviewer-model-heterogeneity.md`) MUST run against `local-cli`-emitted events. When both the `phase: implement` event and the paired `phase: agent-pr-review` event carry `model: unknown`, the predicate MUST mark the pair as inconclusive (logged, not page-worthy) rather than failing — `unknown`-model exemption.
- NFR-REL-001 Helper failure (disk full, malformed input, sink path not writable) MUST NOT block SDD step execution. The helper MUST log the failure to stderr and return success to its caller. SDD step pass/fail MUST be determined by the step's own work product, NOT by C7 emission success.
- NFR-OPS-001 The helper MUST be idempotent on rebase / squash conflict resolution: appending events from rebased commits MUST NOT produce duplicate `event_id` values once #336 dedupes downstream. (Duplicate lines in the local JSONL file after manual conflict resolution are tolerated; subscriber-side dedupe absorbs them.)
- NFR-A11Y-001 N/A — this work item adds no UI surface.

## Normative Option Decision
- Option A: Third sealed emitter `local-cli` with skill-as-tool deterministic helper, JSONL sink committed to branch, #336 ingest on PR-event triggers. (D-4 + D-3 locked.)
- Option B: Direct push from local helper to the durable bus over network (no JSONL sink, no #336 ingest). REJECTED — local environments do not have credentials for the STACKIT-managed bus; would require credential distribution to every operator; would lose the git-history audit trail.
- Selected option: OPTION_A
- Rationale: Option A preserves the issue #339 sealed-emitter rule anti-LLM-hallucination property by keeping emission deterministic and local. The committed JSONL sink doubles as a git-history audit trail that survives even if the bus pipeline regresses. #336 ingest centralises validation and dedupe at one well-understood surface. Option B's network coupling and credential distribution would invert the local-first runtime baseline (SDD-C-014).

## Contract Changes (Normative)
- Config/Env contract: New environment variable `BLUEPRINT_SDD_C7_EMIT` (default `1`; set `0` to opt out). Documented in `blueprint/contract.yaml` under `spec.spec_driven_development_contract.c7_emission`.
- API contract: #336 webhook handler adds three new event-type handlers (`pull_request.opened`, `pull_request.synchronize`, `pull_request.reopened`) that fetch `artifacts/c7/*.jsonl` via the GitHub contents API at PR head SHA. No new public HTTP endpoint exposed.
- OpenAPI / Pact contract path: none
- Event contract: Contract C7 § Emission mechanism widens `emitter` enum to three values; adds `local-cli` sentinel rules for `persona` and `model`; documents `execution_mode` extension field; documents four-input `event_id` derivation for `local-cli`. Bootstrap mirror re-synced.
- Make/CLI contract: Implementations MUST surface the helper through deterministic CLI invocation `python3 scripts/bin/sdd/c7_emit.py emit --phase <enum> --skill <basename> [--outcome <enum>]`; skill runbooks call this CLI rather than importing Python directly.
- Docs contract: New ADR `ADR-issue-347-human-sdd-c7-symmetry.md`. Update to `ADR-issue-337-c7-emission-mechanism.md` to reference the three-emitter rule (or alternatively a new "Extension" subsection). Update to `docs/blueprint/governance/sdd_execution_guide.md` describing the new `BLUEPRINT_SDD_C7_EMIT` env var and the JSONL sink path. Bootstrap mirrors re-synced for both.

## Blueprint Upstream Defect Escalation (Normative)
- Upstream issue URL: none
- Temporary workaround path: none
- Replacement trigger: none
- Workaround review date: none

## Normative Acceptance Criteria
- AC-001 A human SDD session executed from `make spec-scaffold` through `gh pr create --draft` on a fresh work item MUST produce AT LEAST ONE C7 event per executed SDD step in `artifacts/c7/<slug>.jsonl`. A full lifecycle (Step 01 through Step 07) MUST produce ≥ 7 events.
- AC-002 Every emitted `local-cli` event MUST validate against the amended C7 JSON Schema with `additionalProperties: true`; each event MUST carry `emitter: local-cli` AND `execution_mode: human-assisted`.
- AC-003 Re-pushing the same JSONL file to the PR head SHA (e.g., after a no-op force-push) MUST NOT produce duplicate bus events; #336's dedupe by `event_id` MUST absorb the retry. Verified by integration test asserting bus-emission count remains constant across two `pull_request.synchronize` events with identical head SHAs.
- AC-004 Setting `BLUEPRINT_SDD_C7_EMIT=0` and running any SDD step MUST suppress the per-step C7 event AND MUST emit EXACTLY ONE `c7-emission-opted-out` extension event on the first step under opt-out for the given work-item slug. Verified by unit test on the helper and integration test on #336 ingest.
- AC-005 The Grafana dashboard (Blueprint instance, per Contract C7 § Blueprint instance) MUST display `execution_mode` as a panel facet with `autonomous` and `human-assisted` counts visible side-by-side in the same view. Verified by manual operator screenshot attached to `pr_context.md`.
- AC-006 The `.gitattributes` rule MUST hide `artifacts/c7/*.jsonl` from the GitHub PR diff renderer. Verified manually on this work item's own Draft PR.
- AC-007 `make quality-sdd-check`, `make docs-build`, `make docs-smoke`, and the new helper's pytest unit/contract suite MUST pass with zero failures after all amendments + bootstrap mirror sync.

## Informative Notes (Non-Normative)
- Context: The current Contract C7 sealed two-emitter rule (issue #339 sealed-emitter rule) was authored to prevent LLM-hallucinated audit events. Human-driven SDD sessions were initially excluded as out-of-scope. With Epic #343 (Central Brain) in the pipeline and the solo-operator topology dominating real activity, the exclusion now leaves a substantial blind spot. This work item extends the sealed rule to three emitters by applying the same "deterministic wrapper around an LLM-driven phase boundary" pattern to local SDD execution.
- Tradeoffs:
  - Committed JSONL sink adds files to PR diffs. Mitigated by `.gitattributes` `diff=none` rule (FR-013).
  - Best-effort model ID with `unknown` sentinel (D-2) means the FR-008 reviewer-heterogeneity audit becomes inconclusive (not failing) when both implement and review steps lack model metadata. Documented exemption (NFR-OBS-002).
  - Skill-as-tool pattern requires every step skill runbook to call the helper. Mitigated by uniform addendum text (FR-012) and the runbook compatibility checker.
- Clarifications:
  - **[NEEDS CLARIFICATION: Q-2 — JSONL line signing — does each event carry an HMAC over its payload to prevent post-emit tampering?]**

    **Options:**
    - **A)** No signing in v1 — git itself is the integrity surface for committed files; tampering shows up in `git blame`. (Agent recommendation.)
    - **B)** HMAC each line with a shared secret distributed via STACKIT Secrets Manager — strongest tamper-evidence, but adds key management overhead and a secret-distribution flow to every operator's machine.

    **Agent recommendation:** Option A. Local-first runtime baseline (SDD-C-014) discourages mandatory secret distribution to operator workstations; the git history + #336 schema validation cover the realistic threat model.

  - **[NEEDS CLARIFICATION: Q-3 — Self-bootstrapping — does this work item #347 emit C7 events for its own SDD steps?]**

    **Options:**
    - **A)** No — the helper does not exist for the steps that author it; emission becomes mandatory for the first new work item started after #347 merges. (Agent recommendation.)
    - **B)** Yes — author the helper first as Slice 1, then retroactively emit events for steps 01–04 in a single backfill commit before Step 07 PR open.

    **Agent recommendation:** Option A. Backfilled events are not "real" lifecycle events — they are reconstructions, which dilutes the audit surface's truth claim. Cleaner to skip self-bootstrap and audit honestly from work item #N+1.

  - **[NEEDS CLARIFICATION: Q-4 — Coding-assistant model detection fallback chain — what env vars / heuristics does the helper consult?]**

    **Options:**
    - **A)** Read EXACTLY ONE OF `$CLAUDE_CODE_MODEL`, `$CODEX_MODEL`, `$CURSOR_MODEL` (in that priority order); fall through to `unknown`. (Agent recommendation.)
    - **B)** Same as A, plus parse the most-recently-modified `~/.claude/projects/*/...jsonl` session log for the active model identifier.
    - **C)** None — always emit `unknown` for human-assisted runs; document model-tracking as a follow-up.

    **Agent recommendation:** Option A. Env vars are the operator-controlled, explicit surface; parsing assistant session logs is fragile and changes shape between releases.

  - **[NEEDS CLARIFICATION: Q-5 — `rerun_round` semantics for human sessions — what counts as a rerun?]**

    **Options:**
    - **A)** Increment `rerun_round` by counting prior committed events for the same `(ticket_id, phase)` tuple in the local JSONL file; `rerun_round=0` on first emission for that step. (Agent recommendation.)
    - **B)** Always emit `rerun_round=0` from local-cli; let #336 ingest assign the rerun count from bus-side history. Adds coupling.

    **Agent recommendation:** Option A. Keeps the helper self-contained; matches the orchestrator's own rerun-counting semantics.

  - **[NEEDS CLARIFICATION: Q-6 — Skill addendum scope — does the addendum apply only to the seven `blueprint-sdd-stepXX-*` skills, or also to `blueprint-sdd-traceability-keeper` (cross-cutting) and the two consumer-ops skills?]**

    **Options:**
    - **A)** Seven step skills only. Cross-cutting skills have no `phase` enum entry and would need a separate enum extension. (Agent recommendation.)
    - **B)** Seven step skills + `traceability-keeper` with a new `phase: traceability` enum value. Increases #339 amendment scope.
    - **C)** All skills including consumer-ops. Out of scope for blueprint-repo C7; consumer-ops events would need their own contract surface.

    **Agent recommendation:** Option A. Stays inside the existing `phase` enum; consumer-ops emission is the cross-repo aggregation work explicitly out-of-scope per issue #347.

## Explicit Exclusions
- IDE-extension / VS Code / JetBrains integration — helper is CLI-only.
- Automatic backfill of historical PRs — only post-merge PRs are audited (FR-014).
- Cross-repo aggregation of consumer-repo C7 events — blueprint repo only; consumer-repo emission is a follow-up after `artifacts/c7/*.jsonl` is a stable contract.
- `blueprint-sdd-traceability-keeper` skill emission — pending Q-6 resolution; default exclusion.
- Consumer-ops skills (`blueprint-consumer-ops`, `blueprint-consumer-upgrade`) emission — outside the SDD lifecycle; different audit needs.
- Self-bootstrap emission for this work item #347 — pending Q-3 resolution; default exclusion.
