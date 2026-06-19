# PR Context

## Summary
- Work item: `2026-06-18-issue-361-orchestrator-service` — parent coordination spec for issue #361 (autonomous-factory orchestrator service, Child B of #333, Phase 1 of Epic #332).
- Objective: Decompose #361 into 5 child work items along layer / feature / governance-docs boundaries so the pure-core slices can ship while the runtime-client slice waits on #335 + #336 spec-complete; close #369 inside `#361.5` as a governance-docs sibling; ship the orchestrator service across the 5 children without merging any runtime code in THIS PR.
- Scope boundaries: This PR ships ONLY: the parent SDD-spec artifact set (`spec.md`, `architecture.md`, `plan.md`, `tasks.md`, `traceability.md`, `graph.json`, `pr_context.md`, `hardening_review.md`, `evidence_manifest.json`, `context_pack.md`), `docs/blueprint/architecture/decisions/ADR-issue-361-orchestrator-service.md`, two helper bash scripts (`file_children.sh` + `add_deferred_triggers.sh`), a pytest covering the scripts (`tests/blueprint/test_issue_361_file_children_script.py`), and one C7 lifecycle event per SDD-step (intake + resolve-questions). No runtime Python / Helm / NetworkPolicy / PERSONA.md / C3 matrix edits land here.

## Requirement Coverage
- Requirement IDs covered: FR-001 .. FR-017 (17 FRs); NFR-SEC-001 / NFR-OBS-001 / NFR-REL-001 / NFR-OPS-001 / NFR-A11Y-001 (5 NFRs); AC-001 .. AC-013 (13 ACs).
- Acceptance criteria covered: AC-001 .. AC-013 (13 ACs total) — AC-010 + AC-011 + AC-013 verified directly in this PR by 7 pytest cases at `tests/blueprint/test_issue_361_file_children_script.py` (all green); AC-001 .. AC-009 + AC-012 are bound to child-owned tests with deterministic names (T-101..T-205, T-211) authored inside each child's `tests/` directory at child-implementation time, and the parent traceability matrix declares the contract.
- Contract surfaces changed:
  - `docs/blueprint/architecture/decisions/ADR-issue-361-orchestrator-service.md` (new).
  - `specs/2026-06-18-issue-361-orchestrator-service/file_children.sh` (new — operator-run at parent merge).
  - `specs/2026-06-18-issue-361-orchestrator-service/add_deferred_triggers.sh` (new — operator-run at parent merge).
  - `tests/blueprint/test_issue_361_file_children_script.py` (new — unit-classified).
  - `scripts/lib/quality/test_pyramid_contract.json` (added test classification row).
  - `artifacts/c7/2026-06-18-issue-361-orchestrator-service.jsonl` (2 C7 events: `phase: intake` + `phase: resolve-questions`).

## What this PR does NOT do (read this FIRST)

This PR is the parent **coordination spec** for `#361`. Two side effects that one might expect — and that this PR deliberately does NOT trigger:

- **Child GitHub issues are NOT filed by merging this PR.** The 4 child issues (logical names `#361.1`, `#361.2`, `#361.4`, `#361.5`; `#361.3` is deferred per Q-1) are filed by a human operator running `bash specs/2026-06-18-issue-361-orchestrator-service/file_children.sh` AFTER this PR is merged to `main`. The script is idempotent. Reason for the deferral: filing children during the PR would create phantom issues if the PR is abandoned, and would risk drift between mid-review FR edits and already-filed issue bodies. Filing-after-merge guarantees children cite the final, signed-off spec.
- **Parent `#361` is NOT auto-closed by merging this PR.** Per FR-017, this PR body uses `Tracks #361` (informational only) — never `Closes #361`. Per Contract C4, parent `#361` closes only as a deliberate human action AFTER all 5 child PRs merge AND every cross-child Integration AC checkbox on the `#361` issue body is ticked by a human bounded-context reviewer.

## Operator Runbook (run AFTER PR #372 merges — per FR-014 + FR-015 + T-003)

The runbook below is **idempotent** end-to-end — safe to re-run if any step fails partway through. Either the human operator or any agent (with `gh` auth in the operator's session) can execute it.

### Preconditions (verify BEFORE running anything)
1. **PR #372 is merged to `main`.** Confirm with `gh pr view 372 --json state --jq .state` — must print `MERGED`.
2. **gh CLI authenticated against this repo.** Confirm with:
   ```bash
   gh auth status
   gh repo view --json nameWithOwner --jq .nameWithOwner
   # Must print: sbonoc/stackit-platform-blueprint
   ```
   If `gh repo view` resolves to anything else, you are in the wrong working directory — `cd` to a clone of `sbonoc/stackit-platform-blueprint` and retry. The hardened script will refuse to run otherwise (exits 2 with a clear stderr message).
3. **GitHub labels exist on the repo.** All four labels (`agent-ready`, `enhancement`, `infrastructure`, `priority:p1`) MUST already be defined on `sbonoc/stackit-platform-blueprint`. Verify with `gh label list --json name --jq '.[].name' | sort` if uncertain.
4. **`main` is checked out and up-to-date with the merge:**
   ```bash
   git checkout main && git pull
   ```

### Step 1 — file the 4 child issues (`file_children.sh`)
```bash
bash specs/2026-06-18-issue-361-orchestrator-service/file_children.sh
```
**Behavior:** files EXACTLY 4 issues — `#361.1` (dispatch core), `#361.2` (C7 emitter + bus), `#361.4` (Helm chart), `#361.5` (`ux-ui-designer` + `#369` closure). Does NOT file `#361.3` (deferred per Q-1 — see Step 2 for how `#361.3` filing is mechanically surfaced later).

**Idempotency:** script pre-checks each child by exact title match via `gh issue list`. Re-runs create zero duplicates. On any `gh` failure (stale auth, network, search index lag) the script exits 2 without filing duplicates; investigate the stderr error message before re-running.

**Verification after Step 1:**
```bash
gh issue list --search "in:title (Child of #361)" --state open --json number,title --jq '.[] | "\(.number)  \(.title)"'
# Expected: 4 issues, one per Child 1/2/4/5, each titled `feat(orchestrator): <scope> (Child N of #361)`
```
Note the assigned GitHub issue numbers — they will be sequential (e.g., #373, #374, #375, #376) and are NOT the same as the logical names `#361.1`/`#361.2`/`#361.4`/`#361.5`. The script titles each issue `... (Child N of #361)` so the mapping is unambiguous.

### Step 2 — append `#361.3` deferred-filing triggers (`add_deferred_triggers.sh`)
```bash
bash specs/2026-06-18-issue-361-orchestrator-service/add_deferred_triggers.sh
git add AGENTS.backlog.md
git commit -m "chore(2026-06-18-issue-361): append #361.3 deferred-filing triggers per FR-015"
git push
```
**Behavior:** injects EXACTLY 2 entries into `AGENTS.backlog.md` under `### after: issue-335` / `### after: issue-336` (creating `### after: issue-335` if absent, preserving any pre-existing entries under `### after: issue-336`). Each entry instructs the future operator to file `#361.3` and cites the FR-016 `git rm` + FR-017 `Tracks #361` obligations for that future PR.

**Idempotency:** script greps for each entry token before injecting. Re-runs append zero new entries.

**Verification after Step 2:**
```bash
grep -c "trigger: after: issue-335" AGENTS.backlog.md  # expect: 1
grep -c "trigger: after: issue-336" AGENTS.backlog.md  # expect: ≥1 (was 1 pre-existing from #337; now 2)
```

### Step 3 — add Integration AC to parent `#361` issue body (per T-003 + FR-013 + Contract C4)
This step is manual (no script — `gh issue edit` body editing is too freeform for a script-level guarantee).

```bash
gh issue edit 361 --body-file - <<'EOF'
<original issue body>

## Integration Acceptance Criteria

The 5 checkboxes below are only satisfiable by cross-child behavior per Contract C4. The factory bot MUST NOT tick these — only a human bounded-context reviewer. Parent #361 closes only when all 5 children merge AND every box is ticked.

- [ ] AC-005 — end-to-end work-item dispatch produces all 8 expected C7 phase events (verified by T-201 in #361.3)
- [ ] AC-006 — reviewer-rotation picker selects a heterogeneous panel (verified by T-202 in #361.3)
- [ ] AC-007 — orchestrator deploys via Helm, runs as non-root, NetworkPolicy denies public egress (verified by T-203 in #361.4)
- [ ] AC-008 — schema-validation failure surfaces through the #336 reject-rerun cap path (verified by T-204 in #361.3)
- [ ] AC-009 — conditional-dispatch predicate gates `ux-ui-designer` correctly on UI vs non-UI tickets (verified by T-205 in #361.5; closes #369)
EOF
```
Replace `<original issue body>` with `gh issue view 361 --json body --jq .body` output before running. (Or just edit the issue body via the GitHub UI if that is more comfortable — the only requirement is that the 5 checkbox lines land in the issue body with the exact AC-005..AC-009 ID prefixes so cross-references stay searchable.)

**Verification after Step 3:**
```bash
gh issue view 361 --json body --jq .body | grep -c "^- \[ \] AC-00"  # expect: 5
```

### Cumulative end-state after Steps 1+2+3
- 4 new GitHub issues exist on `sbonoc/stackit-platform-blueprint` (the children).
- `AGENTS.backlog.md` carries 2 new entries that will mechanically surface `#361.3` filing when `#335` + `#336` reach spec-complete.
- `#361` issue body carries the 5-checkbox Integration AC section that gates parent close.
- `#361` itself remains OPEN — closure waits for all 5 children merged + all 5 checkboxes ticked by a human.

### What happens later (not part of this runbook, captured here for context)
- Each child runs its own SDD lifecycle (step01..step08) on its own branch and Draft PR. When a child PR merges, its `Tracks #361` keeps `#361` open.
- When `#335` + `#336` reach spec-complete, the parked backlog entries surface `#361.3` filing — at that point a human files `#361.3` as a standalone `gh issue create` (it is NOT in `file_children.sh`'s scope) and the `#361.3` body MUST cite FR-016 + FR-017 + include `git rm` of both helper scripts in its PR diff.
- When all 5 children's PRs are merged and a human has ticked every AC-005..AC-009 box in the `#361` issue body, the same human closes `#361` manually (`gh issue close 361`). At that point, both helper scripts have already been `git rm`ed by `#361.3`'s PR, so the parent decomposition is fully cleaned up.

### Rollback (if a step fails partway through)
- **Step 1 partial fail (e.g., 2 of 4 filed before gh outage):** simply re-run `bash file_children.sh`. Idempotency pre-check via `gh issue list` skips already-created children. Zero duplicates.
- **Step 2 partial fail (e.g., 1 of 2 entries injected before git push failed):** re-run the bash invocation; the grep-token pre-check skips the already-injected entry and injects only the missing one. Then re-commit and re-push.
- **Step 3 fail (e.g., wrong body uploaded):** edit again via `gh issue edit 361`. The only durable error mode is the factory bot accidentally ticking a checkbox — manually un-tick.
- **Disaster recovery (filed wrong-repo issues):** close them manually (`gh issue close <number> --reason "not planned"`). Titles all carry `(Child N of #361)` for unambiguous identification.

### Known operator footguns (review-acknowledged, mitigated)
- The hardened scripts refuse to run if `gh repo view` does not resolve to `sbonoc/stackit-platform-blueprint`. Override via `EXPECTED_REPO=...` only if you genuinely intend to file into a different repo (e.g., a consumer fork).
- `file_children.sh` re-run within seconds of the first run MAY find that GitHub's title-search index hasn't caught up yet. The script's exact-grep filter on `gh issue list` output prevents false positives in the "already exists" check; if duplicates somehow land, close them manually before re-running.
- The 4 children's assigned GitHub issue numbers (whatever GitHub assigns next) are NOT the same as the logical names `#361.1` / `#361.2` / `#361.4` / `#361.5` used throughout the spec. The script titles them `... (Child N of #361)` so the mapping is explicit; everywhere in the spec/ADR/architecture documentation the logical names are used.

## Key Reviewer Files
- Primary files to review first:
  - `specs/2026-06-18-issue-361-orchestrator-service/spec.md` — FR/NFR/AC contract for the 5-child decomposition.
  - `docs/blueprint/architecture/decisions/ADR-issue-361-orchestrator-service.md` — boundary rationale + alternatives considered.
  - `specs/2026-06-18-issue-361-orchestrator-service/architecture.md` — bounded contexts A–E.
- High-risk files:
  - `specs/2026-06-18-issue-361-orchestrator-service/file_children.sh` — operator-run at parent merge; mistakes here file wrong-repo issues. Hardened with preconditions and explicit failure-mode detection.
  - `specs/2026-06-18-issue-361-orchestrator-service/add_deferred_triggers.sh` — awk-driven backlog injection; mistakes here corrupt `AGENTS.backlog.md` (committed file).

## Validation Evidence
- Required commands executed: `make quality-sdd-check` — PASS (validated SDD assets, readiness gates, and language policy); `uv run python3 -m pytest tests/blueprint/test_issue_361_file_children_script.py` — 7 PASS / 0 FAIL; `make quality-hooks-fast` — PASS post-fix; `make quality-hooks-run` — strict gate PASS (`infra-audit-version`, `apps-audit-versions`, `blueprint-template-smoke` all PASS); `make quality-hardening-review` — PASS post-hardening_review.md authoring.
- Result summary: All gates green at PR open. C7 lifecycle events emitted via `local-cli` helper (`scripts/bin/sdd/c7_emit.py`) for `phase: intake` and `phase: resolve-questions`; both committed to `artifacts/c7/2026-06-18-issue-361-orchestrator-service.jsonl`.
- Artifact references:
  - `traceability.md` — 27-row requirement-to-delivery matrix (every FR/NFR/AC mapped to design + impl + test + docs + ops evidence).
  - `graph.json` — 35 nodes + edges per `validated_by` / `constrains` relations.

## Risk and Rollback
- Main risks: (R1) child-owned tests don't exist yet — AC-001..AC-009 + AC-012 cite test names children author at implementation time; mitigated by FR-013 + Contract C4 human-tick of Integration AC at parent close (the AC IDs anchor on real tests at that point). (R2) child runtime code paths are deferred to child intake — until each child runs its own SDD step01, the parent traceability cannot point at real implementation files; mitigated by per-child intake inheriting the parent FR + adding concrete paths. (R3) `#361.3` filing depends on `#335` + `#336` reaching spec-complete — mechanically triggered via `AGENTS.backlog.md` `after: issue-335` + `after: issue-336` entries authored by `add_deferred_triggers.sh`. (R4) `#336` in-cluster webhook-receiver authentication policy is not yet pinned — captured in `AGENTS.backlog.md` § `### after: issue-336` (commit `713e7b2a`) + GitHub issue comment on `#336` recommending GitHub Actions OIDC (Actions→receiver path) + HMAC `X-Hub-Signature-256` with quarterly ESO rotation (GitHub webhook→receiver path); does not block `#361` parent or any of its 5 children but `#336` MUST resolve it before shipping any receiver code.
- Rollback strategy: This PR ships only governance docs + two operator-run helper scripts + a pytest. Revert the merge commit. The helper scripts have no destructive side effects until the operator runs them — pre-merge revert is a clean no-op. If the helper scripts have already been run post-merge, the filed GitHub issues can be closed manually (titles all carry `(Child N of #361)` for unambiguous identification); the `AGENTS.backlog.md` entries can be removed by editing the file directly.

## Deferred Proposals

All proposals received an explicit outcome at step07 publish triage 2026-06-19 (per `blueprint-sdd-step07-pr-packager` guardrail 3 — no proposal silently dropped).

- **Embedding-based finding-text deduplication** (ADR-issue-364 § 11) — **already-parked** under `AGENTS.backlog.md` § `after: issue-368` (`proposal(issue-368-factory-cost-telemetry-routing-fixture): embedding-based router implementation`); no new action at this step. Surfaces if naive string-equality dedup proves insufficient (T-104 fixture failure rate ≥ 20%).
- **Per-expert prompt-cache discipline on Opus-tier invocations** — **already-parked** under `AGENTS.backlog.md` § `on-scope: factory` (`proposal(issue-368-factory-cost-telemetry-routing-fixture): per-expert prompt-cache efficiency`); no new action. Needs first-run telemetry baseline from `outcome_details.token_usage`.
- **Orchestrator local-cluster smoke lane** — **parked** at step07 publish triage (commit on this PR adds entry to `AGENTS.backlog.md` § `after: issue-336`). Trigger: `after: issue-336` — surfaces when both blocker tickets `#335` + `#336` ship their reusable Helm charts.
- **Horizontal-scaling for the orchestrator pod** (multi-replica with shared-lock service) — **parked** at step07 publish triage (commit on this PR adds entry to `AGENTS.backlog.md` § `after: issue-361`). Trigger: `triage: next-session` with `stale-after: 2` — orchestrator-scoped (not factory-wide), needs real-world `outcome_details.token_usage` throughput data which won't exist until the orchestrator ships.
- **IDE-extension direct C7 emission** (VS Code / JetBrains) — **already-rejected** at intake (recorded in PR #372 body's "Surfaced Backlog Proposals" table); local-cli emitter scope, not orchestrator scope. No new action.
- **Promoting parent `#361` coordination spec to a step04 plan-slicer execution** (replay decomposition through the eventual `blueprint-ticket-decompose-light` skill for symmetry-of-evidence) — **rejected** at step07 publish triage 2026-06-19 (recorded as `[x] (rejected)` in `AGENTS.backlog.md` § `after: issue-361`). Rationale: cosmetic — the decomposition outcome is identical whether authored manually or via the skill; re-running for "symmetry" produces no new value. Consciously discarded.
