---
name: blueprint-sdd-step01-intake
description: Execute SDD Steps 1 and 2 — scaffold the work item if not already done, populate all artifacts with real content (Discover → Plan), and open the intake Draft PR with a live Open Questions table. Can be invoked by any project stakeholder. Consolidates the retired intake-decompose, po-spec, and clarification-gate skills.
---

# Blueprint SDD Step 01 — Intake + Draft PR

## Steps covered

- **Step 0** (auto) — Scaffold if not already done
- **Step 1** — Populate artifacts (Discover → High-Level Architecture → Specify → Plan)
- **Step 2** — Commit + open Draft PR with Open Questions table

## When to Use

Invoke when starting a new work item. The skill handles everything from
scaffolding through Draft PR creation in a single pass. If `make spec-scaffold`
was already run by the user, the skill detects the existing directory and skips
it; otherwise it runs the scaffold automatically.

## Actor

Any project stakeholder: **CPO / PO / CTO / Architect / Software Engineer**.
No local development environment is required beyond `make` and `gh` CLI access.

## Governance Context

`AGENTS.md` is the canonical policy source for this skill. Sections that apply in this phase:

- `§ Mandatory Workflow` — SDD-enabled execution is the default; opt-out requires explicit user instruction.
- `§ SDD Artifact Contract` — spec, architecture, plan, tasks, traceability, and graph artifacts must all be created.
- `§ Normative Language Policy (Spec Artifacts)` — MUST / MUST NOT / SHALL / EXACTLY ONE OF are the only accepted normative terms.
- `§ Clarification Marker Policy` — `[NEEDS CLARIFICATION]` is the only accepted form for unresolved inputs.
- `§ Guardrail Control Statements (Mandatory)` — applicable SDD-C-### controls must be declared in `spec.md`.
- `§ Cross-Cutting Guardrails (Must Be Captured in Discover + Specify)` — API and event contracts (OpenAPI, Pact) that define new or changed service interfaces must be drafted in Specify and recorded in `spec.md` under Contract Impacts before implementation begins.

> If `AGENTS.md` changes any of the above sections, update this block to reflect the affected sections.

## Guardrails

1. Every artifact section that can be filled with current knowledge MUST be
   filled. Stubs and placeholder text are not acceptable in the Draft PR.
2. Missing inputs are recorded as `[NEEDS CLARIFICATION]` structured blocks —
   never as empty sections or invented assumptions.
3. `SPEC_READY: false` and `SPEC_PRODUCT_READY: false` are the correct initial
   values; do not set either to `true` in this phase.
4. Do not self-approve any sign-off field.
5. Run `make quality-sdd-check` before committing. Fix all violations before
   opening the Draft PR.
6. The Draft PR opened in Step 2 is the single PR for the entire work item.
   Do not open a second PR.

## Workflow

```
0. AUTO-SCAFFOLD (if not already done)
   Check whether the spec directory exists:
     ls specs/*-<slug>/ 2>/dev/null
   If the directory does not exist, run:
     make spec-scaffold SPEC_SLUG=<slug>
   If the directory already exists, skip this step — the user ran it manually.

1. Confirm source requirements document(s) and scope boundaries.

2. Discover
   - Extract atomic requirements as REQ-###, NFR-###, AC-###.
   - Use only MUST / MUST NOT / SHALL / EXACTLY ONE OF in normative sections.
   - Declare applicable SDD-C-### control IDs in spec.md.
   - Populate Implementation Stack Profile (stack, test automation,
     managed-service, local-first fields).

3. High-Level Architecture
   - Write bounded-context decisions and integration edges in architecture.md.
   - Draft ADR at docs/<track>/architecture/decisions/ADR-<slug>.md
     (Status: proposed). Set ADR path in spec.md.
   - Choose Mermaid diagram type(s) that best illuminate the work item.
     Add a one-sentence caption per diagram.

4. Specify
   - Confirm all SDD-C-### control IDs are declared in the Applicable
     Guardrail Controls section of spec.md.
   - Confirm Implementation Stack Profile is fully populated.

5. Plan
   - Write sequenced delivery slices in plan.md (red→green TDD order).
   - Populate tasks.md with all gate checks and task rows (all unchecked).
   - Generate graph.json nodes and edges for every REQ/NFR/AC.
   - Populate traceability.md mapping every requirement to design,
     implementation, test, documentation, and operational evidence paths.

6. Handle open questions
   Use the structured block wherever an input cannot be resolved:

   > **[NEEDS CLARIFICATION]** Concise statement of what needs to be decided.
   >
   > **Options:**
   > - **A)** Description — tradeoffs (agent recommendation)
   > - **B)** Description — tradeoffs
   >
   > **Agent recommendation:** Option A because [rationale].

   Open questions do not block artifact population — fill every other section.

7. make quality-sdd-check     # fix all violations before continuing

BACKLOG SCAN (surface parked proposals before opening the Draft PR)
8. Read AGENTS.backlog.md and find all `(parked)` entries where:
   - `trigger: after: <slug>` — and <slug> matches the current work item slug, or
     was a recently completed item that this work item depends on or follows.
   - `trigger: on-scope: <tag>` — and <tag> matches any scope area described in the
     current work item's title, spec, or Implementation Stack Profile.
   If any match, surface them in the intake report as a "Surfaced Backlog Proposals"
   table (see Required Report Format). Do NOT automatically incorporate or promote them —
   present them so the user can decide: incorporate into this work item's scope,
   promote to a GitHub issue, or explicitly reject with rationale.

   git add specs/YYYY-MM-DD-<slug>/ docs/.../ADR-<slug>.md
   git commit -m "feat(<slug>): SDD intake — spec, architecture, plan ready for PO review"
   git push -u origin codex/YYYY-MM-DD-<slug>

10. Open Draft PR:
   gh pr create --draft \
     --title "feat(<slug>): <one-line objective>" \
     --body "$(cat <<'EOF'
   ## Summary
   <one paragraph: what this work item does and why>

   Closes #<issue>.

   ## Open Questions (N remaining)

   | # | Question | Artifact | Agent recommendation |
   |---|---|---|---|
   | Q-1 | <question> | `spec.md` § NFR-003 | Option A: ... |

   Answer by leaving a PR comment or inline comment on the relevant file.
   The agent will update the artifacts and this table after each round.

   ## Sign-off

   Grant each sign-off by leaving a PR comment with the **exact** phrase below:

   | Role | Exact PR comment phrase |
   |---|---|
   | Product | `SPEC_PRODUCT_READY: approved` |
   | Architecture | `ARCHITECTURE_SIGNOFF: approved` |
   | Security | `SECURITY_SIGNOFF: approved` |
   | Operations | `OPERATIONS_SIGNOFF: approved` |

   The agent will record each sign-off in `spec.md` and set `SPEC_READY: true`
   once all four are received.

   ---
   _Full reviewer package (`pr_context.md`) will be completed at Step 8
   before this PR is marked ready._
   EOF
   )"
```

If there are no open questions, omit the **Open Questions** section and the
sign-off instructions from the PR description. The PR is still Draft until
Step 9.

## ADR Diagram Selection

Choose Mermaid diagram type(s) that best illuminate the work item:

| Type | Use when |
|---|---|
| `sequenceDiagram` | HTTP request flows across services or components |
| `erDiagram` | Data models and entity relationships |
| `journey` | User-facing business flows and step sequences |
| `flowchart TD` | Data flows, decision branches, script control flow |
| `stateDiagram-v2` | Lifecycle state machines (orders, sessions, jobs) |
| `classDiagram` | Component or module structure |

Use multiple diagrams when the work item spans multiple concerns. If no
diagram adds clarity, state: "No diagram required — [one-line rationale]."

## Required Report Format

Return:

1. Scaffold status (auto-run or already existed).
2. Source requirements document(s) analyzed.
3. REQ-###, NFR-###, AC-### extracted (count per type).
4. SDD-C-### control IDs declared.
5. ADR path and diagram type(s) chosen with rationale.
6. `[NEEDS CLARIFICATION]` open questions list (count + brief description each).
7. `make quality-sdd-check` result.
8. Surfaced Backlog Proposals (from AGENTS.backlog.md scan):

   | Proposal | Trigger | Recommended action |
   |---|---|---|
   | <title> | on-scope: quality | incorporate / promote to issue / reject |

   If none match, state: "No parked proposals match this work item's scope."
9. Draft PR URL.

## Useful Commands

```bash
make spec-scaffold SPEC_SLUG=<slug>
make quality-sdd-check
```

## References

- Intake checklist: `references/intake_checklist.md`
