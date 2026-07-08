# Specification

## Spec Readiness Gate (Blocking)
<!-- SPEC_PRODUCT_READY=true: intake gate — Product sign-off only; unlocks agent ADR drafting.
     SPEC_READY=true: implementation gate — all sign-offs required; unlocks coding. -->
- SPEC_READY: false
- SPEC_PRODUCT_READY: false
- Open questions count: 0
- Unresolved alternatives count: 0
- Unresolved TODO markers count: 0
- Pending assumptions count: 0
- Open clarification markers count: 0
- Product sign-off: pending
- Architecture sign-off: pending
- Security sign-off: pending
- Operations sign-off: pending
- Missing input blocker token: BLOCKED_MISSING_INPUTS
- ADR path: docs/platform/architecture/decisions/ADR-issue-346-upgrade-precommit-clobber.md
- ADR status: proposed
- SPEC_READY_EXCEPTION: bug-fix
- authorized-by: bonos

## Applicable Guardrail Controls (Normative)
- Applicable control IDs: SDD-C-001, SDD-C-002, SDD-C-003, SDD-C-004, SDD-C-005, SDD-C-007, SDD-C-009, SDD-C-011, SDD-C-013, SDD-C-014
- Control exception rationale: SDD-C-006 (API contract), SDD-C-008 (OpenAPI/Pact), SDD-C-010 (event contract), SDD-C-012 (agent execution model), SDD-C-015–SDD-C-021 (frontend, e2e, identity, managed-service gates) — all N/A; this is a shell/Python upgrade-pipeline bug fix with no API surface, no UI, and no managed-service changes.

## Implementation Stack Profile (Normative)
- Backend stack profile: python_plus_fastapi_pydantic_v2
- Frontend stack profile: none
- Test automation profile: pytest_vitest_playwright_pact
- Agent execution model: none
- Managed service preference: stackit-managed-first
- Managed service exception rationale: N/A — no managed service interaction
- Runtime profile: local-first-docker-desktop-kubernetes
- Local Kubernetes context policy: docker-desktop-preferred
- Local provisioning stack: crossplane-plus-helm
- Runtime identity baseline: eso-plus-argocd-plus-keycloak
- Local-first exception rationale: N/A
- Has user-facing flow: false <!-- inferred from intake: no UI/flow signals found — confirm before SPEC_READY -->
- E2E gate classification: N/A

## Objective
- Business outcome: The blueprint upgrade pipeline (`make blueprint-upgrade-consumer`) MUST preserve consumer-added pre-commit hooks and never silently drop them. Operators who added app-specific pre-push gates (e.g. touchpoints/backend unit tests) MUST retain those hooks after every blueprint upgrade.
- Success metric: After running `make blueprint-upgrade-consumer` against any newer blueprint tag, consumer-added hook IDs absent from the blueprint baseline MUST appear verbatim in the upgraded `.pre-commit-config.yaml`. Zero silent data-loss incidents for hook additions that followed the blueprint installation.

## Normative Requirements

### Functional Requirements (Normative)

- FR-001 The upgrade engine MUST classify `.pre-commit-config.yaml` as requiring a YAML-aware hook-preserving merge when the consumer file diverges from the blueprint baseline, rather than issuing a verbatim source overwrite.

- FR-002 During the merge of `.pre-commit-config.yaml`, the engine MUST identify consumer-only hook entries — hooks whose `id` value is present in the consumer file but absent from the blueprint source file — and append them verbatim after the last blueprint hook block in the merged output, before the terminal newline.

- FR-003 Consumer-only hooks MUST be appended in their original YAML order relative to each other, preserving all hook fields exactly as authored (indentation, comments that fall within the hook block are excluded because YAML comments are not parsed into the AST, but all `key: value` fields MUST be preserved).

- FR-004 If the YAML-aware merge encounters a YAML parse failure on either the source or target file, the engine MUST fall back to the existing `git merge-file` 3-way merge behaviour and emit a `WARNING` log line naming the parse error, the affected file, and the fallback mode.

- FR-005 The `upgrade_preflight.json` plan artifact MUST record `"action": "merge-required"` and `"operation": "merge"` for any `.pre-commit-config.yaml` entry where the consumer file differs from the blueprint source, regardless of whether the YAML-aware merge will succeed cleanly.

- FR-006 The upgrade summary (`upgrade_summary.md`) MUST list the IDs of all consumer-only hooks that were preserved in the merge output, so the operator can verify the hook inventory is complete.

- FR-007 The `quality-validate-bootstrap-template-drift` pre-commit hook MUST continue to pass without modification: the blueprint bootstrap template at `scripts/templates/blueprint/bootstrap/.pre-commit-config.yaml` MUST remain identical to the repository root `.pre-commit-config.yaml` after any upgrade applied to the blueprint source repo itself.

- FR-008 Consumer-owned test automation (`tests/`) MUST include at least one positive-path assertion that a consumer hook added between blueprint upgrades survives the merge and is present in the output, with fixture files covering a realistic hook YAML structure.

### Non-Functional Requirements (Normative)

- NFR-SEC-001 The YAML merge MUST use `yaml.safe_load` exclusively (no `yaml.load` with arbitrary loaders). Parsed hook data MUST NOT be passed to shell or `eval`. The merged output MUST be produced by re-serialising the parsed structure or by string-concatenation of raw YAML blocks — never by executing hook `entry` values.

- NFR-OBS-001 The upgrade engine MUST emit a structured log line for each consumer-only hook preserved during merge (at `log_info` level or equivalent), including the hook `id` and the destination position in the merged file. On parse fallback (FR-004), the WARNING log MUST be emitted to stderr so it surfaces in the upgrade apply output.

- NFR-REL-001 The YAML-aware merge MUST be idempotent: running the upgrade twice against the same source ref and same consumer file MUST produce the same `.pre-commit-config.yaml` output without duplicating hook entries.

- NFR-OPS-001 The `upgrade_summary.md` artifact MUST include a human-readable section listing preserved consumer hook IDs; if no consumer-only hooks were found, the section MUST state "no consumer-only hooks detected". This gives operators a self-contained audit trail without requiring them to diff the files manually.

- NFR-A11Y-001 N/A — no user-facing UI in this work item.

## Normative Option Decision

- Option A: **YAML-aware hook-id preserving merge** — parse both files with `yaml.safe_load`, diff hook IDs, rewrite the merged file keeping blueprint hooks first then consumer-only hooks appended.
  - Pros: fully automated (no operator merge step), idempotent, deterministic, self-documenting via summary artifact.
  - Cons: more code complexity; YAML-round-trip may normalise whitespace/comments within hook blocks (acceptable — hook semantics are key:value only).

- Option B: **Change classification to `consumer_seeded_paths`** — move `.pre-commit-config.yaml` out of `required_files` so the upgrade engine never touches it.
  - Pros: zero risk of overwrite; minimal code change.
  - Cons: new blueprint hooks (e.g. `quality-c7-jsonl-validate`, `pnpm-lockfile-sync`) never reach consumers during upgrade; consumer must track blueprint changelog manually. Violates the "blueprint-managed baseline" contract for safety hooks.

- Option C: **Extension block reservation** — blueprint reserves a `# --- consumer hooks begin/end ---` marker block in the template; consumer adds custom hooks only between the markers; upgrade preserves the bracketed block verbatim.
  - Pros: very explicit; no YAML parsing.
  - Cons: requires consumers to migrate existing custom hooks into the marked block; upgrade still silently drops hooks added outside the block.

- Selected option: OPTION_A
- Rationale: Option A preserves the blueprint-managed classification (ensuring blueprint safety hooks always reach consumers) while eliminating silent data loss. The YAML-aware approach is deterministic and test-covered. Option B sacrifices automatic safety-hook propagation. Option C requires a migration step for existing consumers and is less safe for out-of-block additions.

## Contract Changes (Normative)
- Config/Env contract: none
- API contract: none
- OpenAPI / Pact contract path: none
- Event contract: none
- Make/CLI contract: `upgrade_plan.json` and `upgrade_apply.json` schema unchanged; `upgrade_summary.md` gains a "Preserved Consumer Hooks" section (additive). `upgrade_consumer.py` gains a new internal function `_yaml_merge_precommit_hooks`.
- Docs contract: none — operator runbook in `docs/platform/architecture/decisions/ADR-issue-346-upgrade-precommit-clobber.md`.

## Blueprint Upstream Defect Escalation (Normative)
- Upstream issue URL: https://github.com/sbonoc/stackit-platform-blueprint/issues/346
- Temporary workaround path: After `make blueprint-upgrade-consumer`, manually re-add consumer-only hooks to `.pre-commit-config.yaml` AND `scripts/templates/blueprint/bootstrap/.pre-commit-config.yaml`. Both files must stay identical to pass `quality-validate-bootstrap-template-drift`.
- Replacement trigger: Merged PR in blueprint repo that makes the upgrade pipeline preserve consumer-added hooks automatically (this work item).
- Workaround review date: 2026-08-29

## Normative Acceptance Criteria

- AC-001 [Consumer-only hooks survive a clean upgrade] — verified by T-101, which MUST assert that after calling `_yaml_merge_precommit_hooks(source_content, target_content)` where `target_content` contains one hook ID absent from `source_content`, the returned string contains that hook ID.

- AC-002 [Consumer-only hooks are appended after the last blueprint hook, not prepended] — verified by T-102, which MUST assert that the merged output positions the consumer-only hook block after the last hook entry that exists in the source file, and before the terminal newline.

- AC-003 [Multiple consumer-only hooks are all preserved in original order] — verified by T-103, which MUST assert that when the target has N consumer-only hooks (N ≥ 2), all N IDs appear in the merged output in the same relative order they appeared in the target.

- AC-004 [YAML parse failure triggers 3-way merge fallback] — verified by T-104, which MUST assert that when `_yaml_merge_precommit_hooks` is called with malformed YAML for either argument, it raises a `PrecommitYamlParseError` (or equivalent sentinel), which the calling upgrade engine catches and routes to the existing `_three_way_merge` fallback.

- AC-005 [Idempotency: running the merge twice produces identical output] — verified by T-105, which MUST assert that applying the YAML-aware merge function to its own output (with the same source) returns an identical string.

- AC-006 [upgrade_preflight action is merge-required, not update, when consumer file diverges] — verified by T-106, which MUST assert that the plan-step `_classify_entries` call sets `action == "merge-required"` for `.pre-commit-config.yaml` when the consumer added a hook absent from the blueprint source, even when the rest of the file matches.

- AC-007 [No consumer-only hook duplication on second upgrade] — verified by T-107, which MUST assert that if the merge output from AC-001 is used as the new target for a second merge against the same source, the consumer hook ID appears exactly once in the result.

- AC-008 [upgrade_summary lists preserved hook IDs] — verified by T-108, which MUST assert that the `upgrade_summary.md` string produced by `_write_summary` contains the preserved hook ID when a consumer-only hook was merged.

## Informative Notes (Non-Normative)
- Context: `.pre-commit-config.yaml` is classified as `required-file` in `blueprint/contract.yaml`. The current upgrade engine uses `_classify_entries` to decide the merge action: when `target_content == baseline_content`, it returns `ACTION_UPDATE` (safe overwrite); when target diverges from baseline, it returns `ACTION_MERGE_REQUIRED` and attempts a 3-way merge. The 3-way `git merge-file` merge is structurally-unaware of YAML hook semantics. When the new blueprint version also changed the file (e.g. added new hooks), the merge may produce conflicts, and the triage recommends `take_source` for `required-file` ownership, causing consumer additions to be silently lost.
- Tradeoffs: YAML round-trip via `safe_load` + re-serialise normalises whitespace and inline comments within hook blocks. This is acceptable because hook semantics are fully captured by YAML key:value fields; comments within a hook block (which are not preserved by YAML parsers) carry no operational meaning. Outer-file comments (e.g. at the top of the file) are lost during round-trip as well; the blueprint template has no top-level comments so this is a non-issue for new upgrades.
- Clarifications: The `quality-validate-bootstrap-template-drift` hook watches `scripts/templates/blueprint/bootstrap/.pre-commit-config.yaml` vs the root file. This constraint applies to the BLUEPRINT SOURCE REPO itself (when doing internal blueprint development), not to consumer repos. Consumer repos do not have a bootstrap template mirror of `.pre-commit-config.yaml` at that path.

## Explicit Exclusions
- Three-way merge for non-YAML files: this fix applies exclusively to `.pre-commit-config.yaml`; the general 3-way merge engine for other files is out of scope.
- Extension-block reservation: the consumer-managed marker block approach (Option C) is explicitly not implemented in this work item.
- Multi-file YAML hook sources: supporting `repos` entries that use `local` with `language: system` vs remote repos is in scope (both are YAML hook blocks); no external repo resolution is required.

## Potential Deferred Proposals
- Allowlist-based upgrade conflict triage override: Instead of `"required-file": "take_source"` as the triage recommendation, allow the `blueprint/contract.yaml` to declare per-path triage preferences (e.g. `"required-file-merge-preferred": true`). Would generalise the fix to other required files with consumer-local amendments. Deferred because it requires a contract schema change and is out of scope for a targeted bug fix.
- Incremental tag-to-tag upgrade mode (Issue #168): Consumer hooks added in intermediate releases could be tracked per-release. Deferred — blocked on the incremental upgrade track.
- Consumer migration guide (proposal from v1.12.2 bugfixes): Emit a warning when consumer hooks that were previously explicit are now part of the blueprint baseline, to guide cleanup. Deferred — out of scope for correctness fix.
