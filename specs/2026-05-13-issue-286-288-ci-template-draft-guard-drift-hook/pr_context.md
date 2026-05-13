# PR Context

## Summary
- Work item: `2026-05-13-issue-286-288-ci-template-draft-guard-drift-hook`
- Objective: Fix two blueprint v1.10.0 propagation gaps in CI/quality tooling. (1) Consumer CI template gains the draft-PR event type filter and job-level guard that blueprint's own CI has had since `dd4e3f9e`, stopping full pipeline runs on every draft PR push in new and upgraded consumer repos. (2) Bootstrap drift check receives a commit-stage pre-commit hook and standalone `quality-validate-bootstrap-template-drift` Make target so developers receive local feedback when tracked root-level managed files drift from bootstrap template counterparts — closing the gap where `infra-validate` path-gating silently skipped root dotfiles locally.
- Scope boundaries: CI YAML template, `validate_contract.py` (new fast-path flag only), Makefile template, pre-commit config (both source and template mirror), pytest assertions. No runtime provisioning changes. No HTTP routes, filters, or payload transforms. No app delivery workflow scope.

## Requirement Coverage
- Requirement IDs covered: FR-001, FR-002, FR-003, FR-004, FR-005, NFR-SEC-001, NFR-OBS-001, NFR-REL-001, NFR-OPS-001, NFR-A11Y-001
- Acceptance criteria covered: AC-001 through AC-009
- Contract surfaces changed: None — `blueprint/contract.yaml` unchanged. Pre-commit hook and Make target are additive; no existing hooks, CI steps, or targets removed.

| Req | Implementation file | Test |
|---|---|---|
| FR-001 | `scripts/templates/consumer/init/.github/workflows/ci.yml.tmpl` | `test_consumer_ci_template_has_draft_pr_types_filter` |
| FR-002 | `scripts/templates/consumer/init/.github/workflows/ci.yml.tmpl` | `test_consumer_ci_template_quality_fast_has_draft_pr_guard` |
| FR-003 | `scripts/templates/blueprint/bootstrap/make/blueprint.generated.mk.tmpl`, `make/blueprint.generated.mk` | `test_make_template_has_quality_validate_bootstrap_drift_target` |
| FR-004 | `.pre-commit-config.yaml`, `scripts/templates/blueprint/bootstrap/.pre-commit-config.yaml` | `test_precommit_has_bootstrap_drift_hook`, `test_precommit_template_has_bootstrap_drift_hook` |
| FR-005 | `scripts/bin/blueprint/validate_contract.py` | `make quality-validate-bootstrap-template-drift` exits 0 (AC-003 manual); exit 1 on drift (AC-004 manual) |
| NFR-SEC-001 | `.pre-commit-config.yaml` — `language: system`, `make` entry, no remote exec | Hook stanza review |
| NFR-REL-001 | All five changed files — new content appended; no existing keys removed | All pre-existing tests remain green; `make quality-hooks-fast` passes |

## Key Reviewer Files
- Primary files to review first:
  - `scripts/templates/consumer/init/.github/workflows/ci.yml.tmpl` — the customer-visible fix; reviewers should confirm the two YAML blocks match `.github/workflows/ci.yml` exactly (FR-001, FR-002)
  - `scripts/bin/blueprint/validate_contract.py` — `--bootstrap-drift-only` fast-path flag and early-exit block (FR-005); reviewers should confirm it calls `_validate_bootstrap_template_sync` only and does not alter the full-validation path
  - `.pre-commit-config.yaml` — new commit-stage hook placement and `files:` pattern (FR-004); reviewers should confirm the regex covers all six tracked root managed files
  - `tests/blueprint/test_quality_contracts.py` — 5 new assertions (lines 1765–1810); reviewers should confirm each assertion is tight enough to catch regression
- High-risk files:
  - `scripts/templates/blueprint/bootstrap/make/blueprint.generated.mk.tmpl` — new `quality-validate-bootstrap-template-drift` target (FR-003); any PHONY or recipe mistake here propagates to all consumer repos on next upgrade
  - `scripts/templates/blueprint/bootstrap/.pre-commit-config.yaml` — must mirror source `.pre-commit-config.yaml` exactly for the new hook; reviewers should diff the two files

## Validation Evidence
- Required commands executed: pytest (5 new tests), quality-hooks-fast (force-full), infra-validate, docs-build, docs-smoke, quality-hardening-review
  - `uv run python3 -m pytest tests/blueprint/test_quality_contracts.py -v -k "draft_pr or bootstrap_drift"` — 5/5 PASS (Slice 2 GREEN; Slice 1 RED at `6f78c75` confirmed all 5 fail before implementation)
  - `uv run python3 -m pytest tests/blueprint/ -v` — all pre-existing tests green; 2 pre-existing unrelated failures confirmed pre-existing via `git stash` isolation (not introduced by this work item)
  - `QUALITY_HOOKS_FORCE_FULL=true QUALITY_HOOKS_KEEP_GOING=true make quality-hooks-fast` — all checks pass at publish gate
  - `make infra-validate` — PASS
  - `make quality-validate-bootstrap-template-drift` — exit 0 (parity confirmed); pre-commit hook fires at commit time and passes (observed at commit `d868966`)
  - `make docs-build` — PASS
  - `make docs-smoke` — PASS
  - `make quality-docs-check-changed` — PASS
  - `QUALITY_HOOKS_FORCE_FULL=true make quality-hooks-fast` — run at publish gate (Step 8)
- Result summary: All 5 new pytest assertions green. Quality hooks pass. Infra-validate passes. Docs build and smoke pass. Commit-stage hook fires correctly and produces expected output. No regressions in pre-existing test suite.
- Artifact references: `specs/2026-05-13-issue-286-288-ci-template-draft-guard-drift-hook/`

## Risk and Rollback
- Main risks: Low. (1) New commit-stage hook adds ~1–2s latency on commits touching the six tracked root files — acceptable, consistent with existing hook latency. (2) Consumer repos bootstrapped before v1.11.0 keep their existing `ci.yml` without the draft-PR guard until they upgrade — no silent breakage. (3) The `_QG_INFRA_GATE_PATHS` path-gate gap for root dotfiles (local `infra-validate` still skips them) is not closed by this work item; the commit hook fills the practical gap.
- Rollback strategy: Revert commits `d868966` (Slice 2 implementation) and `6f78c75` (Slice 1 RED tests) via `git revert` on the merged commit. All changes are additive — no existing config keys modified, no targets removed — so rollback has no blast radius beyond restoring the pre-existing behavior.

## Deferred Proposals
- Proposal 1 (not implemented): Add root dotfiles (`.dockerignore`, `.gitignore`, `.editorconfig`, `.pre-commit-config.yaml`, `Makefile`) to `_QG_INFRA_GATE_PATHS` so local `infra-validate` (not just the new commit hook) also catches drift. Rationale for deferral: changes path-gating behavior broadly; the commit hook provides faster and more targeted feedback for the practical gap; full path-gate extension is a separate quality infrastructure decision. Parked — trigger: on-scope: quality
