# ADR — Consumer CI Draft-PR Skip and Bootstrap Template Drift Hook

## Status

approved

## Context

Two propagation gaps were identified in the blueprint v1.10.0 release:

**Issue #288 — Consumer CI template missing draft-PR skip:**
Commit `dd4e3f9e` (v1.10.0, 2026-05-06) added a draft-PR skip to the blueprint's own `.github/workflows/ci.yml`:
- `pull_request.types: [opened, synchronize, reopened, ready_for_review]` — GitHub delivers only non-draft lifecycle events
- `if: github.event_name == 'push' || github.event.pull_request.draft == false` — job-level guard for push events

This change was not propagated to `scripts/templates/consumer/init/.github/workflows/ci.yml.tmpl`, so consumer repos bootstrapped or upgraded from v1.10.0 continue to run full CI pipelines on every draft PR push, wasting CI minutes and misleading contributors.

**Issue #286 — Bootstrap drift check not triggered locally:**
`validate_bootstrap_template_sync` runs inside `infra-validate`, which is path-gated by `_QG_INFRA_GATE_PATHS` (prefixes: `infra/`, `scripts/templates/blueprint/`, `make/`, etc.). Root-level managed files (`.dockerignore`, `.gitignore`, `.editorconfig`, `.pre-commit-config.yaml`, `Makefile`) don't match any gate prefix. A developer modifying these files locally gets no pre-commit or pre-push feedback; drift is only caught in CI (`QUALITY_HOOKS_FORCE_FULL=true` bypasses the gate).

## Decision

### Issue #288 — Update `ci.yml.tmpl` to mirror blueprint CI

Apply the same two changes to `scripts/templates/consumer/init/.github/workflows/ci.yml.tmpl`:
1. Add `types: [opened, synchronize, reopened, ready_for_review]` to the `pull_request:` trigger.
2. Add `if: github.event_name == 'push' || github.event.pull_request.draft == false` to the `quality-fast` job.

These are direct copies from `.github/workflows/ci.yml` — no adaptation required.

### Issue #286 — Add commit-stage drift hook via new Make target fast path

**Option A (selected):** Add `--bootstrap-drift-only` flag to `validate_contract.py` and expose it as a `quality-validate-bootstrap-template-drift` Make target. Add a commit-stage pre-commit hook in `.pre-commit-config.yaml` (and its bootstrap template mirror) that fires when any tracked root-level managed file or its template counterpart changes.

**Option B (rejected):** Create a new wrapper script `scripts/bin/blueprint/validate_bootstrap_drift.sh`. Rejected because it adds a new file with no structural advantage over the flag path; the `--branch-only` precedent in `validate_contract.py` already establishes the fast-path flag pattern.

**Option C (rejected):** Extend `_QG_INFRA_GATE_PATHS` to include root dotfiles so `infra-validate` triggers locally. Rejected for this work item: changes the path-gating behavior in a broader way and would slow down all local quality hooks for root-dotfile edits; the commit-stage hook provides faster and more targeted feedback.

## Consequences

- **Positive:** Consumer repos generated or upgraded from blueprint skip CI on draft PRs, matching the blueprint's own behavior. Blueprint developers receive commit-time feedback on root dotfile drift before push.
- **Positive:** The `--bootstrap-drift-only` flag is consistent with `--branch-only`; no new script file introduced.
- **Neutral:** Commits touching tracked root-level managed files trigger an additional commit hook (~1–2s); acceptable relative to existing commit hook latency.
- **Negative (mitigated):** The path-gating gap in `_QG_INFRA_GATE_PATHS` is not addressed — local `infra-validate` still skips root dotfiles unless `QUALITY_HOOKS_FORCE_FULL=true`. The new commit hook fills the practical gap; extending `_QG_INFRA_GATE_PATHS` is deferred.

## Files Changed

### Source files changed (committed)
- `scripts/templates/consumer/init/.github/workflows/ci.yml.tmpl` — draft-PR types filter + job-level guard
- `scripts/bin/blueprint/validate_contract.py` — `--bootstrap-drift-only` fast path
- `scripts/templates/blueprint/bootstrap/make/blueprint.generated.mk.tmpl` — `quality-validate-bootstrap-template-drift` target
- `.pre-commit-config.yaml` — commit-stage drift hook
- `scripts/templates/blueprint/bootstrap/.pre-commit-config.yaml` — drift hook mirror
- `tests/blueprint/test_quality_contracts.py` — 5 new assertions

### Derived file regenerated
- `make/blueprint.generated.mk` — regenerated from template after target addition

## Security Notes

The `quality-validate-bootstrap-template-drift` hook uses `language: system` with a `make` entry pointing to the `quality-validate-bootstrap-template-drift` target. No remote execution, no credentials accessed, no shell injection surface.

## Deferred Proposals

- Proposal: Add root dotfiles to `_QG_INFRA_GATE_PATHS` so local `infra-validate` also catches drift — deferred; surfaces as `on-scope: quality` in `AGENTS.backlog.md`.
