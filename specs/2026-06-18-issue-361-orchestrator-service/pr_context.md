# PR Context

## Summary
- Work item: `2026-06-18-issue-361-orchestrator-service` — parent coordination spec for issue #361 (autonomous-factory orchestrator service, Child B of #333, Phase 1 of Epic #332).
- Objective: Decompose #361 into 5 child work items along layer / feature / governance-docs boundaries so the pure-core slices can ship while the runtime-client slice waits on #335 + #336 spec-complete; close #369 inside `#361.5` as a governance-docs sibling; ship the orchestrator service across the 5 children without merging any runtime code in THIS PR.
- Scope boundaries: This PR ships ONLY: the parent SDD-spec artifact set (`spec.md`, `architecture.md`, `plan.md`, `tasks.md`, `traceability.md`, `graph.json`, `pr_context.md`, `hardening_review.md`, `evidence_manifest.json`, `context_pack.md`), `docs/blueprint/architecture/decisions/ADR-issue-361-orchestrator-service.md`, two helper bash scripts (`file_children.sh` + `add_deferred_triggers.sh`), a pytest covering the scripts (`tests/blueprint/test_issue_361_file_children_script.py`), and one C7 lifecycle event per SDD-step (intake + resolve-questions). No runtime Python / Helm / NetworkPolicy / PERSONA.md / C3 matrix edits land here.

## Requirement Coverage
- Requirement IDs covered: FR-001 .. FR-017 (17 FRs); NFR-SEC-001 / NFR-OBS-001 / NFR-REL-001 / NFR-OPS-001 / NFR-A11Y-001 (5 NFRs); AC-001 .. AC-013 (13 ACs).
- Acceptance criteria covered:
  - AC-010 + AC-011 + AC-013 verified by pytest at `tests/blueprint/test_issue_361_file_children_script.py` (7 test cases, all passing).
  - AC-001 .. AC-009 + AC-012 are bound to child-owned tests with deterministic names (T-101..T-205, T-211) that will be authored inside each child's `tests/` directory at child-implementation time. The parent traceability matrix declares the contract.
- Contract surfaces changed:
  - `docs/blueprint/architecture/decisions/ADR-issue-361-orchestrator-service.md` (new).
  - `specs/2026-06-18-issue-361-orchestrator-service/file_children.sh` (new — operator-run at parent merge).
  - `specs/2026-06-18-issue-361-orchestrator-service/add_deferred_triggers.sh` (new — operator-run at parent merge).
  - `tests/blueprint/test_issue_361_file_children_script.py` (new — unit-classified).
  - `scripts/lib/quality/test_pyramid_contract.json` (added test classification row).
  - `artifacts/c7/2026-06-18-issue-361-orchestrator-service.jsonl` (2 C7 events: `phase: intake` + `phase: resolve-questions`).

## Operator Runbook (run at parent PR merge — per FR-014 + FR-015)

Per FR-017, this PR (and every subsequent child PR) cites parent `#361` with `Tracks #361` — never `Closes #361`. Parent close is a deliberate human action AFTER all 5 children merge AND every Contract C4 Integration AC checkbox on the parent issue body is ticked.

### Preconditions (verify BEFORE running either script)
1. **gh CLI authenticated against this repo.** Confirm with:
   ```bash
   gh auth status
   gh repo view --json nameWithOwner
   # Must print: {"nameWithOwner":"sbonoc/stackit-platform-blueprint"}
   ```
   If `gh repo view` resolves to anything else, you are in the wrong working directory — `cd` to a clone of `sbonoc/stackit-platform-blueprint` and retry. The hardened script will refuse to run otherwise (exits 2 with a clear stderr message).
2. **GitHub labels exist on the repo.** All four labels (`agent-ready`, `enhancement`, `infrastructure`, `priority:p1`) MUST already be defined on `sbonoc/stackit-platform-blueprint`. They have been confirmed present at PR open time but verify with `gh label list --json name --jq '.[].name'` if uncertain.
3. **`main` is checked out and up-to-date** (the parent PR has just been merged):
   ```bash
   git checkout main && git pull
   ```

### Step 1 — file the 4 child issues (`file_children.sh`)
```bash
bash specs/2026-06-18-issue-361-orchestrator-service/file_children.sh
```
Files EXACTLY 4 issues: `#361.1`, `#361.2`, `#361.4`, `#361.5`. Does NOT file `#361.3` (Q-1 deferred). The script is idempotent — re-running creates zero duplicates (it pre-checks by exact title match via `gh issue list`). On any `gh` failure the script exits 2 without filing duplicates; investigate the error message before re-running.

### Step 2 — append #361.3 deferred triggers (`add_deferred_triggers.sh`)
```bash
bash specs/2026-06-18-issue-361-orchestrator-service/add_deferred_triggers.sh
git add AGENTS.backlog.md
git commit -m "chore(2026-06-18-issue-361): append #361.3 deferred-filing triggers per FR-015"
git push
```
Injects 2 entries into `AGENTS.backlog.md` under the matching `### after: issue-335` / `### after: issue-336` subsections (creating `### after: issue-335` if absent; preserving any pre-existing entries under `### after: issue-336`). Idempotent — re-running appends zero new entries.

### Step 3 — add Integration AC to parent #361 issue body (per T-003 + FR-013)
Manually edit the `#361` issue body via `gh issue edit 361` to add an `## Integration Acceptance Criteria` section containing the 5 cross-child checkboxes from `spec.md` § AC-005 through AC-009. Per Contract C4, the factory bot MUST NOT tick these — only a human bounded-context reviewer.

### Known operator footguns (review-acknowledged)
- The hardened scripts refuse to run if `gh repo view` does not resolve to `sbonoc/stackit-platform-blueprint`. Override via `EXPECTED_REPO=...` only if you genuinely intend to file into a different repo (e.g., a consumer fork).
- `file_children.sh` re-run within seconds of the first run MAY find that GitHub's title-search index hasn't caught up yet. The script's exact-grep filter prevents false positives, but if duplicates somehow land, close them manually before re-running.
- The 4 children's GitHub issue numbers (`#373`, `#374`, etc. — whatever GitHub assigns) are NOT the same as the logical names `#361.1` / `#361.2` / `#361.4` / `#361.5` used in the spec. The script titles them `... (Child N of #361)` so the mapping is explicit.

## Key Reviewer Files
- Primary files to review first:
  - `specs/2026-06-18-issue-361-orchestrator-service/spec.md` — FR/NFR/AC contract for the 5-child decomposition.
  - `docs/blueprint/architecture/decisions/ADR-issue-361-orchestrator-service.md` — boundary rationale + alternatives considered.
  - `specs/2026-06-18-issue-361-orchestrator-service/architecture.md` — bounded contexts A–E.
- High-risk files:
  - `specs/2026-06-18-issue-361-orchestrator-service/file_children.sh` — operator-run at parent merge; mistakes here file wrong-repo issues. Hardened with preconditions and explicit failure-mode detection.
  - `specs/2026-06-18-issue-361-orchestrator-service/add_deferred_triggers.sh` — awk-driven backlog injection; mistakes here corrupt `AGENTS.backlog.md` (committed file).

## Validation Evidence
- Required commands executed:
  - `make quality-sdd-check` — PASS (validated SDD assets, readiness gates, and language policy).
  - `uv run python3 -m pytest tests/blueprint/test_issue_361_file_children_script.py` — 7 PASS / 0 FAIL.
- Result summary: All gates green at PR open. C7 lifecycle events emitted via `local-cli` helper (`scripts/bin/sdd/c7_emit.py`) for `phase: intake` and `phase: resolve-questions`; both committed to `artifacts/c7/2026-06-18-issue-361-orchestrator-service.jsonl`.
- Artifact references:
  - `traceability.md` — 27-row requirement-to-delivery matrix (every FR/NFR/AC mapped to design + impl + test + docs + ops evidence).
  - `graph.json` — 35 nodes + edges per `validated_by` / `constrains` relations.

## Risk and Rollback
- Main risks:
  - **R1 — child-owned tests don't exist yet.** AC-001..AC-009 + AC-012 cite test names that children author at implementation time. Mitigated by FR-013 + Contract C4 human-tick of Integration AC at parent close (the AC IDs anchor on real tests at that point).
  - **R2 — child runtime code paths are deferred to child intake.** Until each child runs its own SDD step01, the parent traceability cannot point at real implementation files. Mitigated by per-child intake (each child inherits the parent FR + adds its own concrete paths).
  - **R3 — `#361.3` filing depends on #335 + #336 reaching spec-complete.** Mechanically triggered via `AGENTS.backlog.md` `after: issue-335` + `after: issue-336` entries authored by `add_deferred_triggers.sh`.
- Rollback strategy: This PR ships only governance docs + two operator-run helper scripts + a pytest. Revert the merge commit. The helper scripts have no destructive side effects until the operator runs them — pre-merge revert is a clean no-op. If the helper scripts have already been run post-merge, the filed GitHub issues can be closed manually (titles all carry `(Child N of #361)` for unambiguous identification); the `AGENTS.backlog.md` entries can be removed by editing the file directly.

## Deferred Proposals
- Embedding-based finding-text deduplication (ADR-issue-364 § 11) — out of scope for v1; surfaces if naive string-equality dedup proves insufficient. Backlog entry `proposal(issue-368-factory-cost-telemetry-routing-fixture): embedding-based router implementation` carries the trigger.
- Per-expert prompt-cache discipline on Opus-tier invocations — needs first-run telemetry baseline. Backlog entry `proposal(issue-368-factory-cost-telemetry-routing-fixture): per-expert prompt-cache efficiency` (trigger `on-scope: factory`).
- Orchestrator local-cluster smoke lane — deferred until `#335` + `#336` ship their reusable Helm charts.
- Horizontal-scaling for the orchestrator pod (multi-replica with shared-lock service) — v1 ships `replicas: 1`; deferred until throughput needs are observed.
- IDE-extension direct C7 emission — local-cli emitter scope, not orchestrator scope; rejected at intake.
