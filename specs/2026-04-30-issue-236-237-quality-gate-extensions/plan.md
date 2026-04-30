# Implementation Plan

## Implementation Start Gate
- Implementation tasks MUST remain unchecked until `SPEC_READY=true`.
- If required inputs are missing, add `BLOCKED_MISSING_INPUTS` in `spec.md` and keep the gate closed.

## Constitution Gates (Pre-Implementation)
- Simplicity gate: Two template file edits and five contract assertions. No new scripts, no abstractions.
- Anti-abstraction gate: Direct Makefile target definitions and YAML hook entries; no wrapper layers.
- Integration-first testing gate: Contract assertions written before template changes (TDD red → green).
- Positive-path filter/transform test gate: N/A — no filter or payload-transform logic.
- Finding-to-test translation gate: N/A — no pre-PR reproducible findings to translate.

## Delivery Slices

### Slice 1 — pnpm lockfile pre-push hook (Issue #236)
**Red phase:** Add two contract assertions in `tests/blueprint/test_quality_contracts.py`:
- `test_precommit_template_has_pnpm_lockfile_sync_hook`: asserts `pnpm-lockfile-sync` string is present in the bootstrap `.pre-commit-config.yaml`
- `test_precommit_template_pnpm_lockfile_sync_covers_workspace`: asserts `(^|/)package\.json$` string is present (workspace-wide files pattern)

Both assertions MUST fail before template changes.

**Green phase:** Add the `pnpm-lockfile-sync` hook block to `scripts/templates/blueprint/bootstrap/.pre-commit-config.yaml`.

### Slice 2 — Consumer quality gate extension stubs (Issue #237)
**Red phase:** Add three contract assertions in `tests/blueprint/test_quality_contracts.py`:
- `test_make_template_has_quality_consumer_pre_push_stub`: asserts `quality-consumer-pre-push` target with `@true` body is in `blueprint.generated.mk.tmpl`
- `test_make_template_has_quality_consumer_ci_stub`: asserts `quality-consumer-ci` target with `@true` body is in `blueprint.generated.mk.tmpl`
- `test_quality_ci_blueprint_calls_quality_consumer_ci`: asserts `quality-consumer-ci` string appears in the `quality-ci-blueprint` recipe block in `blueprint.generated.mk.tmpl`
- `test_precommit_template_has_quality_consumer_pre_push_hook`: asserts `quality-consumer-pre-push` hook with `stages: [pre-push]` is in the bootstrap `.pre-commit-config.yaml`
- `test_agents_md_template_has_consumer_extension_targets`: asserts `quality-consumer-pre-push` and `quality-consumer-ci` are documented in `scripts/templates/consumer/init/AGENTS.md.tmpl`

All five assertions MUST fail before template changes.

**Green phase:**
1. Add `quality-consumer-pre-push` and `quality-consumer-ci` stub targets to `scripts/templates/blueprint/bootstrap/make/blueprint.generated.mk.tmpl` and `make/blueprint.generated.mk`.
2. Add `@$(MAKE) quality-consumer-ci` as the final step of `quality-ci-blueprint` in both Makefile files.
3. Add the `quality-consumer-pre-push` pre-push hook to `scripts/templates/blueprint/bootstrap/.pre-commit-config.yaml`.
4. Add `quality-consumer-pre-push` and `quality-consumer-ci` to the `.PHONY` list in both Makefile files.
5. Update `scripts/templates/consumer/init/AGENTS.md.tmpl` to document `quality-consumer-pre-push` and `quality-consumer-ci` with tier placement convention.

### Slice 3 — Docs + validation
- Update `docs/blueprint/governance/quality_hooks.md` with consumer extension target documentation.
- Add or update `docs/platform/consumer/` with consumer guide for overriding the extension stubs.
- Sync `docs/blueprint/governance/quality_hooks.md` to bootstrap template mirror via `make quality-docs-sync-blueprint-template`.
- Run `make quality-docs-sync-core-targets` to regenerate `core_targets.generated.md` with the two new targets.
- Run `make infra-contract-test-fast` and `make quality-hooks-fast`.

## Change Strategy
- Migration/rollout sequence: Template changes land on upgrade; stubs are no-ops so no consumer action required. Consumers who want to use the extension point add overrides to `platform.mk` at their own pace.
- Backward compatibility policy: Additive only. No existing Makefile target or hook is removed or changed.
- Rollback plan: `git revert` the blueprint upgrade commit in the consumer repo. No runtime state, no database migrations.

## Validation Strategy (Shift-Left)
- Unit checks: 6 new contract assertions in `test_quality_contracts.py` (pytest, unit-classified).
- Contract checks: `make infra-contract-test-fast` — all assertions pass.
- Integration checks: N/A — no integration surfaces.
- E2E checks: N/A — no runtime paths.

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
- Notes: No app delivery Make targets are added or removed. `quality-consumer-pre-push` and `quality-consumer-ci` are quality gate extension stubs, not app onboarding targets.

## Documentation Plan (Document Phase)
- Blueprint docs updates: `docs/blueprint/governance/quality_hooks.md` — add Consumer Extension Targets section documenting `quality-consumer-pre-push` and `quality-consumer-ci`, when to override, and the `platform.mk` override pattern.
- Consumer docs updates: `docs/platform/consumer/` — add `consumer_quality_gates.md` (new file) documenting how to override the stubs and when each extension point fires.
- AGENTS.md template update: `scripts/templates/consumer/init/AGENTS.md.tmpl` — add `quality-consumer-pre-push` and `quality-consumer-ci` to the quality gate section with tier placement convention (Tier 1/unit → `quality-consumer-pre-push`; Tier 2/component → `quality-consumer-ci`).
- Mermaid diagrams updated: No existing diagrams changed; ADR contains a new flowchart.
- Docs validation commands:
  - `make docs-build`
  - `make docs-smoke`

## Publish Preparation
- PR context file: `pr_context.md`
- Hardening review file: `hardening_review.md`
- Local smoke gate (HTTP route/filter changes): N/A — no HTTP routes, filters, or API endpoints.
- Publish checklist:
  - include requirement/contract coverage
  - include key reviewer files
  - include validation evidence + rollback notes

## Operational Readiness
- Logging/metrics/traces: None required — the new hooks emit existing `pnpm install` and `make` stdout output.
- Alerts/ownership: None required.
- Runbook updates: None required — consumer extension stubs are self-documenting via Makefile `##` comments.

## Risks and Mitigations
- Risk 1: `pnpm install --frozen-lockfile --prefer-offline` fails when the local pnpm store is stale → consumer must run `pnpm install` with network access first. Mitigation: the hook `name` field documents this expectation; same failure mode as current CI.
