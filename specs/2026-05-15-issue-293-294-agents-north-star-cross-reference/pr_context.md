# PR Context

## Summary

Implements a three-layer AGENTS.md ↔ north_star.md anti-duplication contract, closing #293 and
#294. The failure mode was observed in the dhe-marketplace consumer: cross-cutting architecture
invariants were inlined in AGENTS.md across multiple spec sessions because AGENTS.md is
auto-loaded by agents, creating silent drift from north_star.md.

Layer 1 (text governance): `scripts/templates/consumer/init/AGENTS.md.tmpl` gains an
"Architecture Invariants — Pointers" section with anti-duplication statement, example Pointers
table, and a Mandatory Workflow rule requiring agents to read the relevant `north_star.md` section
before touching a covered domain. The blueprint's own `AGENTS.md` gains the same rule (FR-007).

Layer 2 (heading-overlap detection): `check_docs_cross_reference.py` exits 1 when AGENTS.md and
north_star.md share normalized headings outside the Pointers table, with per-consumer allowlist
support (FR-003–006).

Layer 3 (structure enforcement): `check_agents_md_structure.py` exits 1 when an existing
consumer's AGENTS.md is missing the Pointers section header or the north_star.md Mandatory
Workflow rule, surfacing the gap on the next push after blueprint upgrade (FR-010–011). The check
is consumer-only, gated by `blueprint_repo_is_generated_consumer` in `hooks_fast.sh`.

See `specs/2026-05-15-issue-293-294-agents-north-star-cross-reference/` for full spec, ADR, and
traceability.

## Requirement Coverage
- Requirement IDs covered: FR-001, FR-002, FR-003, FR-004, FR-005, FR-006, FR-007, FR-010,
  FR-011, NFR-PERF-001, NFR-MAINT-001, NFR-COMPAT-001
- Acceptance criteria covered: AC-001, AC-002, AC-003, AC-004, AC-005, AC-006, AC-007, AC-008,
  AC-011, AC-012 — all 25 tests green (see traceability.md)
- Contract surfaces changed:
  - [ ] `blueprint/contract.yaml` changed — no change; `scripts/bin/quality/` is already a
    `blueprint_managed_root`; new scripts propagate automatically on consumer upgrade.
  - [x] docs/templates/tests were synchronized — `quality_hooks.md` and `troubleshooting.md`
    synced to bootstrap template mirrors; both new test files registered in
    `scripts/lib/quality/test_pyramid_contract.json`.
  - [x] generated consumer behavior changed — `quality-hooks-fast` now runs two additional
    checks: `quality-docs-cross-reference-check` (all repos) and
    `quality-docs-agents-md-structure-check` (consumer repos only).

## Key Reviewer Files
- Primary files to review first:
  - `scripts/bin/quality/check_docs_cross_reference.py` — new script; heading-overlap detection, Pointers-table exemption, allowlist parsing.
  - `scripts/bin/quality/check_agents_md_structure.py` — new script; structural element detection for existing consumers after blueprint upgrade.
  - `scripts/bin/quality/hooks_fast.sh` — both new checks wired in; structure check gated by `blueprint_repo_is_generated_consumer`.
  - `scripts/templates/consumer/init/AGENTS.md.tmpl` — template text: new Pointers section and Mandatory Workflow rule 13.
  - `AGENTS.md` (blueprint root) — Mandatory Workflow rule 13 added (blueprint-path variant).
- High-risk files:
  - `make/blueprint.generated.mk` — two new make targets; also mirrored in bootstrap template.
  - `tests/blueprint/test_docs_cross_reference.py` — 16 unit tests covering AC-001–AC-008.
  - `tests/blueprint/test_agents_md_structure.py` — 9 unit tests covering AC-011–AC-012.
  - `docs/blueprint/governance/quality_hooks.md` — governance docs for both new checks.

## Validation Evidence
```
uv run python3 -m pytest tests/blueprint/test_docs_cross_reference.py \
  tests/blueprint/test_agents_md_structure.py -v
→ 25 passed in 0.04s

make quality-hooks-fast
→ PASS — both new checks wired and green; structure check skipped in blueprint repo
  (blueprint_repo_is_generated_consumer=false) with quality_hooks_skip_total metric.

make infra-contract-test-fast
→ PASS — both new make targets present in contract target list.

make docs-build
→ [SUCCESS] Generated static files in "build".

make docs-smoke
→ PASS

make quality-hardening-review
→ PASS (no findings — exit 0)
```

## Risk and Rollback
- Main risks: Low. Additive quality checks only. No existing behaviour changed. Cross-reference
  check exits 0 for the blueprint repo (no AGENTS.md/north_star.md heading overlaps present).
  Structure check is consumer-only by design — blueprint repo logs a skip metric and continues.
  Risk for consumers: first push after blueprint upgrade may surface the structure check failure
  if AGENTS.md predates this contract; remediation is documented in
  `docs/platform/consumer/troubleshooting.md` § AGENTS.md structure check fails after blueprint
  upgrade.
- Rollback strategy: Revert the two `run_check`/`run_cmd` blocks from `hooks_fast.sh` (lines
  added in the implementation commit for cross-reference and structure checks) and the two make
  target entries from `make/blueprint.generated.mk`. No data migration required. No persistent
  state. Feature-flag alternative: set `QUALITY_HOOKS_FORCE_FULL=false` and remove the two
  `run_check` calls to effectively no-op both checks without a revert.

## Deferred Proposals (Not Implemented)
- Option B — body-heuristic duplication detection: detect paraphrased or body-level content
  duplication between AGENTS.md and north_star.md sections beyond exact heading match.
  Deferred per spec Normative Option Decision (OPTION_A selected). Issue #294 recommends
  starting simple; Option A catches the primary failure mode deterministically. Option B adds
  false-positive risk without consumer feedback from Option A first.
  Outcome: park — trigger: on-scope: quality

## Follow-Up
- File deferred proposal issue for Option B and add backlog entry (handled in publish step).
- Consumer repos that pre-date this blueprint version will see the structure check fail on
  their next push; they follow the troubleshooting guide to add the missing AGENTS.md sections.
- No rollout notes — quality gate changes take effect immediately on consumer upgrade.
