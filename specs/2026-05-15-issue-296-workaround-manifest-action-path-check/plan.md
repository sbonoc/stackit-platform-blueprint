# Implementation Plan

## Implementation Start Gate
- Implementation tasks MUST remain unchecked until `SPEC_READY=true`.
- If required inputs are missing, add `BLOCKED_MISSING_INPUTS` in `spec.md` and keep the gate closed.

## Constitution Gates (Pre-Implementation)
- Simplicity gate: Single checker script, single Make target, one `run_check` call — no abstractions beyond what is needed.
- Anti-abstraction gate: Direct `yaml.safe_load` + `Path.exists()` — no shared library, no class hierarchy.
- Integration-first testing gate: Pytest test covers both the happy path and the missing-file failure path, plus a live-manifest integration assertion against the real v1.10.0 entries.
- Positive-path filter/transform test gate: N/A — no filter or payload-transform logic.
- Finding-to-test translation gate: N/A — no reproducible pre-PR smoke/curl finding; the gap is latent. The pytest test for missing `action_path` is the regression test.

## Delivery Slices

### Slice 1 — Checker + Make target + hooks wiring + pytest test (single slice, TDD order)

**Red phase (tests first):**
1. Write `tests/blueprint/test_workaround_manifest_check.py` covering:
   - (a) subprocess exit 0 for a manifest with all files present (temp dir fixture)
   - (b) subprocess exit 1 + stderr output for a manifest with a missing `action_path` file (temp dir fixture)
   - (c) live-manifest assertion: all v1.10.0 `action_path` files exist on disk
   Run `pytest tests/blueprint/test_workaround_manifest_check.py` — confirm (a) and (b) fail because the checker does not exist yet; (c) is skipped or fails trivially.

**Green phase (implementation):**
2. Write `scripts/bin/quality/check_workaround_manifest.py`:
   - `SKILL_ROOT = REPO_ROOT / ".agents/skills/blueprint-consumer-upgrade"`
   - `MANIFEST_PATH = SKILL_ROOT / "workarounds/manifest.yaml"`
   - Read manifest via `yaml.safe_load`; iterate all versions → workarounds → `action_path`
   - Resolve each path as `SKILL_ROOT / action_path`
   - Collect violations (missing files); exit 0 (all present) or exit 1 (violations, stderr)
3. Add `quality-workaround-manifest-check` Make target to `make/blueprint.generated.mk` (`.PHONY` + recipe).
4. Add mirror target to `scripts/templates/blueprint/bootstrap/make/blueprint.generated.mk.tmpl`.
5. Add unconditional `run_check "quality-workaround-manifest-check"` to `scripts/bin/quality/hooks_fast.sh` after `quality-sdd-check-all`.
6. Run `pytest tests/blueprint/test_workaround_manifest_check.py` — all three cases PASS.
7. Run `make quality-workaround-manifest-check` — exits 0.
8. Run `make quality-hooks-fast` — `quality-workaround-manifest-check PASS` in summary.

## Change Strategy
- Migration/rollout sequence: Additive — new file + two modified files (blueprint.generated.mk, hooks_fast.sh) + template mirror. No breaking changes.
- Backward compatibility policy: Existing quality checks are unmodified. The new `run_check` is unconditional and always present after this change.
- Rollback plan: `git revert` the single implementation commit. Three files change: `scripts/bin/quality/check_workaround_manifest.py` (delete), `make/blueprint.generated.mk` (remove target + .PHONY entry), `scripts/bin/quality/hooks_fast.sh` (remove `run_check` line). Template mirror revert is automatic.

## Validation Strategy (Shift-Left)
- Unit checks: `pytest tests/blueprint/test_workaround_manifest_check.py` — covers happy path, missing-file failure, and live-manifest assertion.
- Contract checks: N/A — no API or Pact contract.
- Integration checks: `make quality-workaround-manifest-check` runs against the live manifest (same as live-manifest pytest assertion).
- E2E checks: `make quality-hooks-fast` confirms the check is wired and passes end-to-end.

## App Onboarding Contract (Normative)
- App onboarding impact: no-impact
- Notes: Pure tooling change — no app delivery workflow impact.
- Required minimum make targets (all N/A — tooling-only scope):
  - `apps-bootstrap` — N/A
  - `apps-smoke` — N/A
  - `backend-test-unit` — N/A
  - `backend-test-integration` — N/A
  - `backend-test-contracts` — N/A
  - `backend-test-e2e` — N/A
  - `touchpoints-test-unit` — N/A
  - `touchpoints-test-integration` — N/A
  - `touchpoints-test-contracts` — N/A
  - `touchpoints-test-e2e` — N/A
  - `test-unit-all` — N/A
  - `test-integration-all` — N/A
  - `test-contracts-all` — N/A
  - `test-e2e-all-local` — N/A
  - `infra-port-forward-start` — N/A
  - `infra-port-forward-stop` — N/A
  - `infra-port-forward-cleanup` — N/A

## Documentation Plan (Document Phase)
- Blueprint docs updates: none — no behavior change visible to consumers; `core-targets` reference doc update if `quality-workaround-manifest-check` is listed there (verify post-implementation).
- Consumer docs updates: none.
- Mermaid diagrams updated: none.
- Docs validation commands:
  - `make docs-build`
  - `make docs-smoke`

## Publish Preparation
- PR context file: `pr_context.md`
- Hardening review file: `hardening_review.md`
- Local smoke gate (HTTP route/filter changes): N/A — no HTTP route scope.
- Publish checklist:
  - include requirement/contract coverage
  - include key reviewer files
  - include validation evidence + rollback notes

## Operational Readiness
- Logging/metrics/traces: N/A — CI gate only; no runtime path.
- Alerts/ownership: N/A.
- Runbook updates: N/A.

## Risks and Mitigations
- Risk 1: `manifest.yaml` YAML schema changes could cause the checker to raise a `KeyError` rather than reporting a clean violation. Mitigation: the checker fails visibly (unhandled exception → non-zero exit) rather than silently passing, which is the safe failure mode.
- Risk 2: Template mirror (`blueprint.generated.mk.tmpl`) diverges from the live file. Mitigation: `quality-validate-bootstrap-template-drift` already runs in `hooks_fast.sh` and will catch drift; confirmed post-implementation.
