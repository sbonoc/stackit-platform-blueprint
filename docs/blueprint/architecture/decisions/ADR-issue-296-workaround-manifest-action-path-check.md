# ADR — Workaround Manifest `action_path` CI Validation Gate

- Status: approved
- Work item: 2026-05-15-issue-296-workaround-manifest-action-path-check
- Closes: #296
- Date: 2026-05-15
- ADR technical decision sign-off: sbonoc

## Context

The workaround catalogue at `.agents/skills/blueprint-consumer-upgrade/workarounds/manifest.yaml` references action files via the `action_path` field. Each entry maps to a file under the skill's `workarounds/` subtree. Currently nothing in CI verifies that every referenced path resolves to an existing file.

A blueprint maintainer can commit a manifest entry with a typo in `action_path` and the error surfaces only at consumer upgrade time — after the release is shipped to consumers. The v1.10.0 entries were manually verified at the time of authoring (PR #292), but manual verification cannot scale as more versions are added.

The workaround catalogue was introduced in issue #268; the CI gate was explicitly deferred from that scope to keep the initial delivery self-contained (see `hardening_review.md` from PR #292).

## Decision

Add `scripts/bin/quality/check_workaround_manifest.py` — a standalone Python checker that reads `manifest.yaml`, resolves all `action_path` values relative to the skill root, and exits non-zero for any missing file. Expose it as the `quality-workaround-manifest-check` Make target and wire it into `quality-hooks-fast` unconditionally.

## Options Considered

### Option A — Standalone checker (Selected)

**Approach:** New `scripts/bin/quality/check_workaround_manifest.py`. New `quality-workaround-manifest-check` Make target (to be created). Unconditional `run_check` in `hooks_fast.sh`.

**Pros:**
- Single responsibility: the checker has exactly one concern — manifest path existence.
- `check_sdd_assets.py` remains focused on SDD governance artifacts.
- Independently testable; independently skippable if the skill is conditionally absent in future.
- Consistent with the existing checker pattern (`check_root_dir_prelude.py`, `check_docs_cross_reference.py`).

**Cons:**
- Adds a new script file rather than extending an existing one.

### Option B — Extend `check_sdd_assets.py`

**Approach:** Add a workaround manifest section inside `check_sdd_assets.py`.

**Pros:**
- Keeps the checker count low.

**Cons:**
- `check_sdd_assets.py` already has >1900 lines of SDD governance logic; adding workaround-catalogue logic conflates two unrelated governance domains.
- The workaround catalogue is scoped to `blueprint-consumer-upgrade` skill; `check_sdd_assets.py` is scoped to SDD artifact governance. The concerns are orthogonal.

**Rejected.** Separation of concerns wins.

## Consequences

- The `quality-workaround-manifest-check` Make target is available as a standalone check for local debugging.
- `quality-hooks-fast` gains one new check; fast gate wall-clock time increases by < 1 second.
- Any future `manifest.yaml` entry with a missing `action_path` file will fail fast at commit time rather than at consumer upgrade time.
- The checker does not validate action file content (YAML schema, patch syntax) — that is out of scope and would require knowledge of each `action_kind`.
