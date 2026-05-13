# ADR — Pipeline Finalize Target and Auto-Clone Source URL

**Status:** approved
**Date:** 2026-05-13
**Issues:** #267 (finalize target), #269 (auto-clone source URL)
**Spec:** `specs/2026-05-13-issue-267-269-pipeline-finalize-auto-clone/`
**ADR technical decision sign-off:** approved

---

## Context

Two independent usability failures were identified during a real consumer upgrade (sbonoc/dhe-marketplace, v1.7.0 → v1.10.0):

1. **Auto-clone gap (Issue #269):** `BLUEPRINT_UPGRADE_SOURCE` accepts a URL as its documented canonical form, but Stages 1b and 5 invoke `subprocess.run(["git", ...], cwd=upgrade_source)` with the raw URL string, which is not a filesystem path. Stage 1b emits a non-fatal warning; Stage 5 fatal-exits. Consumers must clone manually to a tmp dir and re-run — an undocumented workaround costing ~3 minutes per upgrade.

2. **Finalize gap (Issue #267):** After `make blueprint-upgrade-consumer` completes the apply, consumers must run a large implicit sequence of sync and verify targets in the correct order. There is no canonical idempotent "finish the upgrade" target. A real consumer required 5 sequential `quality-hooks-run` fix cycles (~15 minutes) to converge to green.

---

## Decision

### Issue #269 — Normalize source URL to local path once before Stage 1b

Add a URL normalization block in `upgrade_consumer_pipeline.sh` immediately after `upgrade_source` is resolved and before Stage 1b. If `upgrade_source` does not point to a local directory with a `.git` subdirectory, the pipeline:

1. Validates the `upgrade_source` value against an allowlist of safe URL prefixes (`https://`, `git@`, `ssh://`) and local path prefixes (`/`, `./`, `../`); aborts with an actionable error on unknown prefix (NFR-SEC-001).
2. Clones with `git clone --quiet --depth 1 --branch "$upgrade_ref" "$upgrade_source" "$cloned_source_dir"`.
3. Registers `trap 'rm -rf "$cloned_source_dir"' EXIT` immediately after clone (NFR-REL-001).
4. Reassigns `upgrade_source="$cloned_source_dir"` for all subsequent stages.

Stage 2 engine (`upgrade_consumer.py`) gains a guard that skips its own internal clone when `upgrade_source` is already a local `.git` directory (FR-003).

**Rationale:** A single clone point eliminates the per-stage URL vs. local-path inconsistency without requiring changes to individual stages. Shallow clone (`--depth 1`) is sufficient because Stage 5 only needs `git show $upgrade_ref:$path` for the tag already at HEAD. The EXIT trap ensures no partial clone survives a pipeline failure.

### Issue #267 — Canonical finalize target (quality convergence layer)

Add `scripts/bin/blueprint/upgrade_consumer_finalize.sh` and the `blueprint-upgrade-consumer-finalize` make target. The script runs two passes:

**Sync pass** (aggregated failures, no fail-fast — writes derived artifacts):
1. `make quality-docs-sync-all`
2. `make quality-sdd-sync-consumer-init-assets`
3. `make quality-sdd-sync-policy-snippets`

If any sync target fails, subsequent sync targets still run. All failures are aggregated and reported together at the end of the sync pass.

**Verify pass** (fail-fast — read-only checks):
1. `make infra-validate`
2. `make quality-hooks-run`
3. `make blueprint-upgrade-consumer-validate`
4. `make blueprint-upgrade-consumer-postcheck`
5. `make blueprint-upgrade-fresh-env-gate`

The first failing verify target causes finalize to exit non-zero immediately with a summary banner naming the target and its exit code.

The pipeline's Stage 8 and Stage 9 are replaced by a single blueprint-upgrade-consumer-finalize invocation; Stages 3–7 remain as pipeline-internal steps. Stage 10 (residual report) continues via the EXIT trap.

**Rationale:** The sync pass must aggregate rather than fail-fast because sync failures are often independent (contract-metadata drift does not block SDD asset sync). The verify pass must fail-fast because failures are ordered — a failing `infra-validate` makes `quality-hooks-run` output unreliable. Separate sync and verify passes preserve the separation of concerns between mutation and validation.

---

## Considered Alternatives

### A1 — Per-stage URL cloning (rejected)
Each stage that needs a local path could clone independently. Rejected: wasteful (N clones for N stages), inconsistent (different stages may clone to different depths), and adds N failure surfaces.

### A2 — Error early with actionable message on URL input (rejected for #269)
Detect URL form at pipeline startup and print an actionable clone command. Rejected: the user still has to clone manually; the URL form is the documented canonical entrypoint; auto-clone is strictly better.

### A3 — Document the sync/verify order in SKILL.md only (rejected for #267)
Keep the current ad-hoc list in the runbook. Rejected: the list drifts as new sync targets are added; a make target is the authoritative executable specification of the convergence sequence.

### A4 — Move Stages 3–7 into finalize (Option B — rejected)
Make finalize wrap all post-Stage-2 work including Stages 3–7. Rejected: Stages 3–7 are content-fetching operations tightly coupled to the apply result and `BLUEPRINT_UPGRADE_SOURCE`/`BLUEPRINT_UPGRADE_REF`. Moving them into finalize would make standalone finalize invocation semantically ambiguous (it would re-run coverage-fetch and mirror-sync on an already-converged working tree). Option A (finalize = quality tail only) keeps finalize as a pure idempotent quality-convergence command.

---

## Consequences

- Positive: URL form of `BLUEPRINT_UPGRADE_SOURCE` now works transparently end-to-end; no consumer workaround required.
- Positive: consumers reach a green post-upgrade state with one command (blueprint-upgrade-consumer-finalize) instead of 5+ manual cycles.
- Positive: `blueprint-upgrade-consumer` pipeline behavioural output is preserved; only internal Stage 8+9 implementation changes.
- Positive: finalize is idempotent — safe to re-run after any partial failure.
- Neutral: standalone finalize is only meaningful after Stages 3–7 have run; this precondition is documented in the script usage block.
- Neutral: shallow clone (`--depth 1`) is sufficient for current stage operations but may need deepening if a future stage requires ancestry traversal.
