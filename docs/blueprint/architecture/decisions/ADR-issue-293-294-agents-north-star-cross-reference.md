# ADR — AGENTS.md ↔ north_star.md Anti-Duplication Contract

- Status: proposed
- Work item: 2026-05-15-issue-293-294-agents-north-star-cross-reference
- Closes: #293, #294
- Date: 2026-05-15

## Context

Consumer repositories initialized from the blueprint template contain two governance files that are both auto-loaded by code assistants:

- `AGENTS.md` — process, workflow, SDD lifecycle policy, quality-hook rules
- `docs/platform/architecture/north_star.md` — cross-cutting architecture invariants, bounded-context decisions, long-lived platform guidance

Because AGENTS.md is auto-loaded on every agent session, there is a recurring temptation to inline architecture content there directly (e.g. "OpenMetadata Integration Architecture" section) so agents see it without a separate read step. This has already caused measurable harm in the dhe-marketplace consumer: a substantial `## OpenMetadata Integration Architecture` section grew in AGENTS.md over multiple spec sessions, duplicating the content already in north_star.md. The duplication was caught and corrected in commit `9586424`, but the correction required manual audit. The pattern will recur in every consumer unless the template enforces the separation from initialization.

The blueprint's existing template provides only a soft pointer in `AGENTS.md § SDD Artifacts`:
_"Use the north-star architecture references: `docs/platform/architecture/north_star.md`"_

This is insufficient because:
1. It says where to look, not what must NOT be inlined.
2. There is no structural section in AGENTS.md that names the boundary explicitly.
3. There is no automated enforcement — convention is the only guardrail.

## Decision

**Enforce AGENTS.md = process-and-governance only; north_star.md = architecture content only** at two layers:

### Layer 1 — Template governance (FR-001, FR-002)

Update `scripts/templates/consumer/init/AGENTS.md.tmpl` with:

1. A new **"Architecture Invariants — Pointers"** section containing:
   - An explicit anti-duplication statement: AGENTS.md does NOT contain architecture content.
   - A pointers table: `Domain | north_star.md section | Canonical ADR(s)` — consumers extend this table one row per cross-cutting concern.
   - An instruction: new cross-cutting concerns go to `north_star.md` and the appropriate ADR, never inline in AGENTS.md.

2. A new **Mandatory Workflow rule** that before any SDD work item touching a domain in `north_star.md`, the agent MUST read the relevant `north_star.md` section and canonical ADR(s) in the Pointers table, and MUST NOT inline that content in AGENTS.md.

### Layer 2 — Programmatic enforcement (FR-003 through FR-006)

Add `scripts/bin/quality/check_docs_cross_reference.py`:
- Parse `##`/`###` headings from `AGENTS.md` and `docs/platform/architecture/north_star.md`.
- Normalize: lowercase, collapse whitespace.
- Report a violation for each AGENTS.md heading that exactly matches a north_star.md heading, UNLESS:
  - The heading appears verbatim in the "Architecture Invariants — Pointers" table in AGENTS.md (sanctioned navigation pointer), OR
  - The heading is listed in `.quality-docs-cross-reference-allowlist.yml` with a non-empty `justification` field.
- Exit 0 = clean; exit 1 = violations found.
- Graceful no-op when either file is absent.

Wire into `quality-hooks-fast` alongside `quality-docs-check-changed`.

## Detection Heuristic — Option A (Exact Normalized Heading Match)

Chosen over Option B (section-heading + body heuristic) because:
- Issue #294 explicitly recommends starting simple.
- Exact heading match catches the primary failure mode with zero false positives from body content.
- Body-heuristic option is parked for future iteration.

## Consequences

- New consumer repos initialized after this change have the anti-duplication contract visible from day one.
- Existing consumers are not auto-updated (AGENTS.md is consumer-owned post-init). They see the new hook on blueprint upgrade; clean consumers pass; consumers with duplication see violations on the next push and fix manually.
- The Pointers table exemption requires that table rows use the exact heading text from north_star.md as the domain key. Paraphrased rows will still trigger violations — by design.
- Option B (body-heuristic) is explicitly deferred as a parked proposal (on-scope: quality).
- `pr_context.md` required-section content validation is skipped for bypass-track specs; this hook applies to full-SDD work items where the spec is SPEC_READY.

## Alternatives Considered

- **Convention only (status quo):** Soft pointer in AGENTS.md with no structural section and no automated enforcement. Rejected — the dhe-marketplace drift proves convention fails silently across multiple sessions.
- **Option B — body heuristic:** Scan shared MUST/MUST-NOT clauses and bullet text across matched sections. Rejected for initial implementation (higher complexity, false-positive risk); parked for future iteration.
- **Auto-update existing consumers on upgrade:** Rejected — AGENTS.md is consumer-owned; blueprint-managed auto-overwrite would break the ownership contract.
