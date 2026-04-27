---
name: blueprint-sdd-step03-spec-complete
description: Execute SDD Step 4 — collect Architecture, Security, and Operations sign-offs, validate and finalise the ADR, flip SPEC_READY=true, and commit to the existing Draft PR branch. Renamed and adjusted from blueprint-sdd-spec-complete to fit the single-PR lifecycle model.
---

# Blueprint SDD Step 03 — Spec Complete

## Step covered

- **Step 4** — Remaining sign-offs → `SPEC_READY: true`

## When to Use

Invoke after `SPEC_PRODUCT_READY: true` is recorded in `spec.md` (Step 3
complete). This step collects the technical sign-offs from the CTO / Architect
(Architecture + Security) and the Software Engineer (Operations), finalises the
ADR, and flips `SPEC_READY: true` to unlock implementation.

## Actor

Software Engineer (invokes agent); CTO / Architect grants sign-offs via PR
review, PR comments, or direct conversation.

## What This Phase Produces

- ADR Technical Decision Layer validated and finalised (draft notice removed).
- `Architecture sign-off: approved` recorded in `spec.md`.
- `Security sign-off: approved` recorded in `spec.md`.
- `Operations sign-off: approved` recorded in `spec.md`.
- `ADR technical decision sign-off: approved` in the ADR file.
- ADR `Status: proposed → approved`.
- `SPEC_READY: true` set in `spec.md`.
- `make quality-sdd-check` passes with `SPEC_READY: true`.

## Governance Context

`AGENTS.md` is the canonical policy source for this skill. Sections that apply in this phase:

- `§ SDD Readiness Gate (Mandatory Before Implementation)` — all conditions that must be met before `SPEC_READY: true` may be set.
- `§ Sign-off Policy` — rules for recording Architecture, Security, Operations, and ADR sign-offs; self-approval is prohibited.

> If `AGENTS.md` changes any of the above sections, update this block to reflect the affected sections.

## Guardrails

1. MUST NOT set `SPEC_READY: true` while any required sign-off field is not approved.
2. MUST NOT leave the agent draft block-quote notice in the ADR after signing off.
3. All commits go to the existing Draft PR branch — no new PR is opened.
4. Do not self-approve any sign-off field. A sign-off may only be recorded when
   the canonical trigger phrase (see `§ Sign-off Policy` in `AGENTS.md`) appears
   verbatim in a PR comment or in a direct conversation message from the user.
   Plain-language variants ("approved", "looks good", "LGTM", "fine", silence,
   absence of objection) do NOT qualify. When in doubt, keep the field as
   `pending` and prompt the user to use the exact phrase.
5. If the ADR recommended option is technically unsound, the Architect overrides
   it and documents the override rationale. Never silently accept a wrong recommendation.
6. Run `make quality-sdd-check` before committing — it must pass.

## Sign-off Phrases (Deterministic)

Reviewers grant sign-offs by leaving a PR comment with the **exact** phrase below.
Plain-language approval is not sufficient. If a reviewer expresses approval without
the exact phrase, post a follow-up comment asking them to use the canonical form.

| Role | Exact PR comment phrase | Records in `spec.md` |
|---|---|---|
| Architecture | `ARCHITECTURE_SIGNOFF: approved` | `Architecture sign-off: approved` |
| Security | `SECURITY_SIGNOFF: approved` | `Security sign-off: approved` |
| Operations | `OPERATIONS_SIGNOFF: approved` | `Operations sign-off: approved` |

(Product sign-off `SPEC_PRODUCT_READY: approved` is handled by Step 02 and must already
be recorded before this step runs.)

## Workflow

```
0. Read all PR comments since Step 02 completed:
   gh pr view <number> --comments

1. Review ADR Technical Decision Layer with the Architect / CTO:
   a. Confirm or override the recommended option.
      - Confirm: remove draft notice, keep option, sign off.
      - Adjust: correct analysis or consequences, keep option, document adjustment.
      - Override: select different option, document override rationale, sign off.
   b. Validate Mermaid diagrams — correct type, accurate component names.
   c. Remove the agent draft block-quote notice.
   d. Set ADR metadata:
      - ADR technical decision sign-off: approved
      - Status: approved

2. Record sign-offs from PR comments in spec.md:
   - For each comment containing `ARCHITECTURE_SIGNOFF: approved`:
       Architecture sign-off: approved
   - For each comment containing `SECURITY_SIGNOFF: approved`:
       Security sign-off: approved
   - For each comment containing `OPERATIONS_SIGNOFF: approved`:
       Operations sign-off: approved
   If a sign-off phrase is absent, keep that field as `pending` and do not proceed.

3. Set SPEC_READY only when all four sign-offs are approved:
   - SPEC_READY: true

4. make quality-sdd-check      # must pass before commit

5. Commit to the existing branch (same Draft PR):
   git add specs/YYYY-MM-DD-<slug>/spec.md docs/.../ADR-<slug>.md
   git commit -m "feat(<slug>): all sign-offs — SPEC_READY"
   git push
```

## ADR Review Decision Points

When reviewing the agent's recommended option, apply exactly one of:

- **Confirm** — remove draft notice, keep recommended option, sign off.
- **Adjust** — correct option analysis or consequences, keep option, document
  adjustment rationale alongside the sign-off.
- **Override** — select a different option, document the override rationale, sign off.

## Required Report Format

Return:

1. ADR review decision (confirm / adjust / override) with rationale.
2. Mermaid diagram validation result — type correct, components accurate.
3. Sign-off status for all four roles (Product, Architecture, Security, Operations).
4. `make quality-sdd-check` result.
5. Commit SHA pushed to the existing Draft PR branch.

## Useful Commands

```bash
make quality-sdd-check
make quality-sdd-check-all
```

## References

- Spec completion checklist: `references/spec_complete_checklist.md`
