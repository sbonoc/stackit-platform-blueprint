# PR Context

## Summary
- Work item: `2026-05-14-issue-268-consumer-workarounds-catalogue` — issue #268, child of tracking issue #262
- Objective: Ship a versioned workaround catalogue inside the consumer-upgrade skill and close the authoring feedback loop. The pipeline applies catalogue entries for the target version, reverts them when fixes land, and automatically files structured reports for newly discovered workarounds. Eliminates per-consumer rediscovery of known upstream defects.
- Scope boundaries: upgrade pipeline tooling only — no Kubernetes, no Crossplane, no HTTP endpoints, no UI. New artefact `artifacts/blueprint/workarounds_applied.json`. New stage insertion (Stage 1c / Stage 2c) in `upgrade_consumer_pipeline.sh`. New GitHub Actions scaffolder workflow.

## Requirement Coverage
- Requirement IDs covered: FR-001, FR-002, FR-003, FR-004, FR-005, FR-006, FR-007, FR-008, FR-009, FR-010, FR-011, FR-012, FR-013, FR-014; NFR-SEC-001, NFR-SEC-002, NFR-REL-001, NFR-REL-002, NFR-REL-003, NFR-OPS-001, NFR-A11Y-001 (N/A)
- Acceptance criteria covered: AC-001 through AC-013 (all)
- Contract surfaces changed: `SKILL.md` (workaround catalogue + filing step sections added); `bug_report.yml` (optional structured workaround section appended); new `workaround_report_scaffolder.yml` GHA workflow; `upgrade_consumer_pipeline.sh` (Stage 1c / Stage 2c added); new `manifest.yaml` + `v1.10.0/` catalogue entries

## Key Reviewer Files
- Primary files to review first:
  - `scripts/lib/blueprint/upgrade_workarounds.py` — engine (270 LOC): all action kinds, idempotency, revert, phase dispatch
  - `.agents/skills/blueprint-consumer-upgrade/workarounds/manifest.yaml` — catalogue schema and v1.10.0 entries
  - `.agents/skills/blueprint-consumer-upgrade/SKILL.md` — skill contract extension (workaround catalogue + filing step)
- High-risk files:
  - `scripts/bin/blueprint/upgrade_consumer_pipeline.sh` — new Stage 1c / Stage 2c blocks in critical pipeline path
  - `scripts/lib/blueprint/upgrade_workarounds.py` — `_contract_merge_apply` writes to `blueprint/contract.yaml` before Stage 2 reads it

## Validation Evidence
- Required commands executed: `make blueprint-test-unit` (34 new tests + full existing suite); `make quality-sdd-check`; `make quality-hooks-fast`
- Result summary: `make blueprint-test-unit` — 0 failures; `make quality-sdd-check` — all gates green; `make quality-hooks-fast` — all gates green except `blueprint-template-smoke` which fails on macOS due to pre-existing `declare -A` bash-4-only associative array in `prune_codex_skills.sh` (bash 3.2 shipped with macOS); this failure is pre-existing on this branch and on `main`; CI runs on Linux (bash 5+) and is unaffected
- Artifact references: `tests/blueprint/test_upgrade_workarounds.py` (22 tests), `tests/blueprint/test_workaround_report_parser.py` (8 tests), `tests/blueprint/test_workaround_report_filer.py` (4 tests); all three files registered in `scripts/lib/quality/test_pyramid_contract.json`

## Risk and Rollback
- Main risks: (1) Stage 1c runs before Stage 2's blueprint apply — a catalogue failure that exits non-zero will abort the pipeline before the main upgrade. Mitigated by `stage1c_rc` isolation: Stage 1c failure sets `stage1c_rc` and is surfaced via pipeline exit code, not a silent skip. (2) `contract_merge` workarounds mutate `blueprint/contract.yaml`; an invalid YAML action file produces a fatal error (per FR-010 design), so partial corruption is impossible. (3) `python_script` workarounds execute arbitrary Python with a minimal env allowlist (NFR-SEC-001); trust is inherited from blueprint author model — no new trust surface beyond existing make targets and shell scripts.
- Rollback strategy: remove the Stage 1c and Stage 2c blocks from `upgrade_consumer_pipeline.sh` (two self-contained blocks bounded by log lines). Delete or ignore `artifacts/blueprint/workarounds_applied.json`. No schema migrations, no database changes.

## Deferred Proposals
- Proposal 1 (`env_var` action kind — not implemented): Parked — trigger: on-scope: blueprint — modifying `.envrc` as a workaround action; excluded due to persistent environment pollution risk; no concrete use case yet; surfaces when workaround catalogue or blueprint upgrade tooling is next touched.
- Proposal 2 (manifest `action_path` CI validation — not implemented): Filed — https://github.com/sbonoc/stackit-platform-blueprint/issues/296 — quality gate verifying every `action_path` in `manifest.yaml` points to an existing file; prevents silent consumer-time failures; no current safeguard.
