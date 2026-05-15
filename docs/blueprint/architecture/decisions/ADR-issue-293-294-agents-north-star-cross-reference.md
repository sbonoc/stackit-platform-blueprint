# ADR — AGENTS.md ↔ north_star.md Anti-Duplication Contract

- Status: proposed
- Work item: 2026-05-15-issue-293-294-agents-north-star-cross-reference
- Closes: #293, #294
- Date: 2026-05-15

## Context

### Auto-loading tiers and the structural root cause

Agent sessions operate on a tiered loading model:

- **Tier 1 — always auto-loaded**: `AGENTS.md` via the `CLAUDE.md` directive. Every agent session reads this file unconditionally.
- **Tier 2 — read on demand**: `docs/platform/architecture/north_star.md` (consumer), `docs/blueprint/architecture/north_star.md` (blueprint), ADRs. These are referenced as soft pointers but have no normative MUST-read instruction forcing agents to load them before starting work.

The Tier 2 gap is the structural root cause of the duplication pattern. Because `north_star.md` is not auto-loaded, agents have an incentive to inline its content into `AGENTS.md` so it is visible without a separate read step. This creates silent drift: `AGENTS.md` accumulates architecture content that already exists in `north_star.md`, but neither file enforces exclusivity.

### north_star.md ownership model

`docs/platform/architecture/north_star.md` is seeded from the blueprint at consumer init (`seed_mode: create_if_missing` in `contract.yaml`) and is thereafter fully consumer-owned — it is never overwritten on blueprint upgrade. `docs/blueprint/architecture/north_star.md` is blueprint-managed and drift-checked on upgrade. This ownership split is why the hooks use two different file paths depending on context (consumer vs. blueprint repo).

### Observed harm

The dhe-marketplace consumer demonstrates the failure mode: a substantial `## OpenMetadata Integration Architecture` section grew in `AGENTS.md` over multiple spec sessions, duplicating content already in `north_star.md`. The duplication was caught and corrected in commit `9586424`, but only through manual audit. The pattern will recur in every consumer unless the template enforces the boundary from initialization.

### Gap in the blueprint repo itself

The same Tier 2 gap exists in the blueprint repo's own `AGENTS.md`. The blueprint template provides only a soft pointer:
_"Use the north-star architecture references: `docs/platform/architecture/north_star.md`"_

This is insufficient for the same three reasons that apply to consumer repos:
1. It says where to look, not what MUST NOT be inlined.
2. There is no structural section naming the boundary explicitly.
3. There is no automated enforcement — convention is the only guardrail.

### Gap for existing consumers

Consumer repos initialized before this change have no automatic path to adopt the structural contract. `AGENTS.md` is consumer-owned post-init and is never auto-overwritten on blueprint upgrade. Without an active enforcement signal, existing consumers would silently miss the new contract indefinitely.

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
- `north_star.md` ownership is unchanged: the consumer path (`docs/platform/architecture/north_star.md`) remains seeded-at-init and consumer-owned; the blueprint path (`docs/blueprint/architecture/north_star.md`) remains blueprint-managed. No change to `contract.yaml`.
- Option B (body-heuristic) is explicitly deferred as a parked proposal (on-scope: quality).

## Alternatives Considered

- **Convention only (status quo):** Soft pointer in AGENTS.md with no structural section and no automated enforcement. Rejected — the dhe-marketplace drift proves convention fails silently across multiple sessions.
- **Option B — body heuristic:** Scan shared MUST/MUST-NOT clauses and bullet text across matched sections. Rejected for initial implementation (higher complexity, false-positive risk); parked for future iteration.
- **Auto-overwrite existing consumers on upgrade:** Rejected — AGENTS.md is consumer-owned; blueprint-managed auto-overwrite would destroy consumer-specific content and break the ownership contract.
- **Additive auto-patch on upgrade:** Insert only the missing sections into existing consumer AGENTS.md files without touching existing content. Rejected — auto-patching prose files is fragile: consumers may have reorganized sections, renamed headings, or restructured the Mandatory Workflow block; insertion point heuristics produce incorrect results. The check-and-signal approach (Layer 3) is safer: the consumer receives a clear violation message and adds the sections manually using the updated template as reference.
- **`AGENTS.decisions.md` decisions ledger:** A separate file of past decisions that agents MUST scan before each Discover phase. Rejected — no lifecycle management (entries get superseded with no staleness signal), context window cost grows unboundedly as the file grows, and the requirement duplicates what the ADR system already provides with proper lifecycle states. If needed in the future, it requires its own spec covering format contract, lifecycle fields, and index structure.
