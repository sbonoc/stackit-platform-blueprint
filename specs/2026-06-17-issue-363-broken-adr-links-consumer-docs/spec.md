---
id: spec-2026-06-17-issue-363
artifact_kind: spec
work_item_slug: 2026-06-17-issue-363-broken-adr-links-consumer-docs
owner_team: "@sbonoc/factory-governance"
schema_version: 1.0.0
---

# Specification — issue #363: broken local ADR links in consumer factory governance docs

## Spec Readiness Gate (Blocking)
- SPEC_READY: true
- SPEC_PRODUCT_READY: true
- Open questions count: 0
- Unresolved alternatives count: 0
- Unresolved TODO markers count: 0
- Pending assumptions count: 0
- Open clarification markers count: 0
- Product sign-off: approved
- Architecture sign-off: approved
- Security sign-off: approved
- Operations sign-off: approved
- Missing input blocker token: none
- ADR path: none
- ADR status: n/a
- SPEC_READY_EXCEPTION: bug-fix
- authorized-by: bonos

## Applicable Guardrail Controls (Normative)
- Applicable control IDs: SDD-C-013
- Control exception rationale: docs-only change; no runtime, no API, no schema, no secret handling. SDD-C-001 through SDD-C-012 and SDD-C-014 through SDD-C-021 do not apply.

## Implementation Stack Profile (Normative)
- Backend stack profile: none
- Frontend stack profile: none
- Test automation profile: make quality targets only
- Agent execution model: n/a
- Managed service preference: n/a
- Managed service exception rationale: n/a
- Runtime profile: n/a
- Local Kubernetes context policy: n/a
- Local provisioning stack: n/a
- Runtime identity baseline: n/a
- Local-first exception rationale: n/a
- Has user-facing flow: false <!-- inferred from intake: docs-only bug fix — no UI/flow signals found -->
- E2E gate classification: N/A

## Objective
- Business outcome: `make quality-docs-lint` passes in consumer repos that upgrade to blueprint v1.12.0+; no consumer is required to manually strip hyperlinks from inherited factory governance docs.
- Success metric: zero broken-link lint errors reported for the four affected files in both the blueprint repo and the bootstrap template mirror.

## Normative Requirements

### Functional Requirements (Normative)

- FR-001 — The four factory governance docs MUST have all 29 `[text](../architecture/decisions/ADR-*.md)` hyperlinks converted to plain text (link text preserved, hyperlink syntax removed). Additional inline references expressed as bare backtick identifiers (e.g. `` `ADR-issue-337-*.md` ``) MUST NOT be touched — the linter does not flag these.
- FR-002 — The bootstrap template mirror under `scripts/templates/blueprint/bootstrap/docs/blueprint/autonomous-factory/` MUST be updated to match the four edited source files (zero diff after `sync_blueprint_template_docs.py`).

### Non-Functional Requirements (Normative)
- NFR-OBS-001 — N/A — docs-only change; no logs, metrics, or traces involved.
- NFR-SEC-001 — N/A — no trust boundary, credential, or auth surface touched.
- NFR-REL-001 — Rollback: revert the commit. No data migration or coordination required.
- NFR-OPS-001 — N/A — no runbook surface affected.
- NFR-A11Y-001 — N/A — no user-facing flow.

## Contract Changes (Normative)
- Config/Env contract: none
- API contract: none
- OpenAPI / Pact contract path: none
- Event contract: none
- Make/CLI contract: none
- Docs contract: four `docs/blueprint/autonomous-factory/*.md` files lose local ADR hyperlinks; their link text is preserved. Bootstrap template mirror updated in the same commit.

## Blueprint Upstream Defect Escalation (Normative)
- Upstream issue URL: none (this IS the upstream)
- Temporary workaround path: consumer workaround already applied (link text stripped); this fix makes it the canonical form in source
- Replacement trigger: n/a
- Workaround review date: n/a

## Normative Acceptance Criteria

- AC-001 [`grep` finds no broken ADR hyperlinks] — verified by T-101, which MUST assert that `grep -rn '\.\./architecture/decisions/ADR' docs/blueprint/autonomous-factory/` exits with no matches.
- AC-002 [`make quality-docs-lint` passes] — verified by T-102, which MUST assert that `make quality-docs-lint` exits 0 with no broken-link errors for the four affected files.
- AC-003 [bootstrap template mirror in sync] — verified by T-103, which MUST assert that `uv run python3 scripts/lib/docs/sync_blueprint_template_docs.py --check` exits 0.
- AC-004 [`make quality-sdd-check` passes] — verified by T-104, which MUST assert that `make quality-sdd-check` exits 0.

## Explicit Exclusions
- Backtick-only ADR identifier references (e.g. `` `ADR-issue-337-triage-size-threshold.md` ``) are not hyperlinks and MUST NOT be touched.
- Consumer repos that already applied the workaround (stripped link text) are not retroactively updated — the blueprint source fix flows to them on next `make blueprint-upgrade-consumer`.
- Adding a new lint rule to prevent future broken-link regressions is deferred (see Potential Deferred Proposals).

## Potential Deferred Proposals
- lint guard: add a `lint_docs.py` check that rejects new `../architecture/decisions/ADR-*.md` links inside `docs/blueprint/autonomous-factory/` files, preventing recurrence. Deferred — low-urgency tooling improvement with no current requester.
