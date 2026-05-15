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

### Layer 1 — Template governance and blueprint AGENTS.md update (FR-001, FR-002, FR-007)

Update `scripts/templates/consumer/init/AGENTS.md.tmpl` with:

1. A new **"Architecture Invariants — Pointers"** section containing:
   - An explicit anti-duplication statement: AGENTS.md does NOT contain architecture content.
   - A pointers table: `Domain | north_star.md section | Canonical ADR(s)` — consumers extend this table one row per cross-cutting concern.
   - An instruction: new cross-cutting concerns go to `north_star.md` and the appropriate ADR, never inline in AGENTS.md.

2. A new **Mandatory Workflow rule** (FR-002) that before any SDD work item touching a domain in `north_star.md`, the agent MUST read the relevant `north_star.md` section and canonical ADR(s) in the Pointers table, and MUST NOT inline that content in AGENTS.md.

Update the blueprint's own `AGENTS.md` with:

3. The same north_star.md MUST-read Mandatory Workflow rule as item 2 above (FR-007), referencing `docs/blueprint/architecture/north_star.md`.

**Rationale for extending to the blueprint's own AGENTS.md**: AGENTS.md is always auto-loaded by agents, but `north_star.md` is only a soft pointer with no normative MUST-read instruction. This gap applies equally to the blueprint repo and consumer repos; fixing only the template would leave the blueprint repo with the same vulnerability.

**Rationale for NOT introducing `AGENTS.decisions.md`**: A flat decisions ledger has no lifecycle management — decisions get superseded or made obsolete with no mechanism to signal staleness. An agent following a MUST-read rule on a growing file gets actively wrong guidance when entries are stale, and context window cost grows unboundedly. The existing ADR system (numbered, with `proposed/accepted/superseded/obsolete` lifecycle) + `north_star.md` (current settled state) + Pointers table (domain → north_star section → canonical ADR) already provide selective, lifecycle-aware decision surfacing. No separate decisions ledger is introduced.

### Layer 2 — Programmatic duplication enforcement (FR-003 through FR-006)

Add `scripts/bin/quality/check_docs_cross_reference.py`:
- Parse `##`/`###` headings from `AGENTS.md` and `docs/platform/architecture/north_star.md`.
- Normalize: lowercase, collapse whitespace.
- Report a violation for each AGENTS.md heading that exactly matches a north_star.md heading, UNLESS:
  - The heading appears verbatim in the "Architecture Invariants — Pointers" table in AGENTS.md (sanctioned navigation pointer), OR
  - The heading is listed in `.quality-docs-cross-reference-allowlist.yml` with a non-empty `justification` field.
- Exit 0 = clean; exit 1 = violations found.
- Graceful no-op when either file is absent.

Wire into `quality-hooks-fast` alongside `quality-docs-check-changed`.

### Layer 3 — Structural enforcement for existing consumers (FR-010, FR-011)

Add `scripts/bin/quality/check_agents_md_structure.py`:
- Verify `AGENTS.md` contains `## Architecture Invariants — Pointers` section header.
- Verify `AGENTS.md` contains a reference to `north_star.md` within a `## Mandatory Workflow` section.
- Report a named violation per missing element with `[quality-docs-agents-md-structure-check]` prefix.
- Exit 0 = all elements present or file absent; exit 1 = one or more elements missing.

Wire into `quality-hooks-fast` alongside the duplication check. Propagate to consumer repos via bootstrap template path.

**Rationale**: AGENTS.md is consumer-owned and is never auto-overwritten on upgrade. Existing consumers that pre-date the template change would otherwise silently miss the structural contract. The structure check fires on the next push after blueprint upgrade, surfacing the gap with a clear violation message. The consumer adds the missing sections manually using the updated template as a reference. Auto-patching prose files is rejected as too fragile.

## Detection Heuristic — Option A (Exact Normalized Heading Match)

Chosen over Option B (section-heading + body heuristic) because:
- Issue #294 explicitly recommends starting simple.
- Exact heading match catches the primary failure mode with zero false positives from body content.
- Body-heuristic option is parked for future iteration.

## Consequences

- New consumer repos initialized after this change have the anti-duplication contract visible from day one, with a normative instruction to read the relevant north_star.md section and canonical ADR(s) before touching a covered domain.
- Blueprint's own `AGENTS.md` gains the same Mandatory Workflow rule (FR-007), closing the auto-loading gap in the blueprint repo itself.
- Existing consumers are not auto-overwritten. After blueprint upgrade they receive the new hooks; on the next push the structure check (Layer 3) fires if the required sections are absent, prompting the consumer to add them manually using the updated template as a reference.
- The Pointers table exemption requires that table rows use the exact heading text from north_star.md as the domain key. Paraphrased rows will still trigger violations — by design.
- Option B (body-heuristic) is explicitly deferred as a parked proposal (on-scope: quality).
- `pr_context.md` required-section content validation is skipped for bypass-track specs; this hook applies to full-SDD work items where the spec is SPEC_READY.

## Alternatives Considered

- **Convention only (status quo):** Soft pointer in AGENTS.md with no structural section and no automated enforcement. Rejected — the dhe-marketplace drift proves convention fails silently across multiple sessions.
- **Option B — body heuristic:** Scan shared MUST/MUST-NOT clauses and bullet text across matched sections. Rejected for initial implementation (higher complexity, false-positive risk); parked for future iteration.
- **Auto-update existing consumers on upgrade:** Rejected — AGENTS.md is consumer-owned; blueprint-managed auto-overwrite would break the ownership contract.
- **`AGENTS.decisions.md` decisions ledger:** A separate file of past decisions that agents MUST scan before each Discover phase. Rejected — no lifecycle management (entries get superseded with no staleness signal), context window cost grows unboundedly as the file grows, and the requirement duplicates what the ADR system already provides with proper lifecycle states. If needed in the future, it requires its own spec covering format contract, lifecycle fields, and index structure.
