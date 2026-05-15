# ADR — Lightweight SDD bypass track via SPEC_READY_EXCEPTION field

## Status

approved

## Sign-offs

- ADR technical decision sign-off: approved

## Context

The current `quality-sdd-check` gate enforces a uniform 10-artifact SDD contract for every `specs/` subdirectory. This was designed for feature and enhancement delivery but creates a perverse-incentive problem for non-feature change types (bug fixes, refactors, blueprint upgrades, chores):

- **Option A (ungoverned)** — skip the gate entirely. No traceability, no audit trail.
- **Option B (governance theater)** — create 10 stub artifacts just to satisfy the checker. Audit trail is present but meaningless; traceability tables are empty or invented.

The motivating case is `sbonoc/dhe-marketplace` PR #62 — a blueprint v1.10.0 upgrade corrective convergence. The corrective changes (backend test alignment, smoke script bug, WCAG additions, test-tier reclassification) are not a feature. Completing a full SDD spec cycle was disproportionate. The workaround was a `AGENTS.decisions.md` deviation record — a process patch, not a structural fix.

## Decision

Add a **field-gated exception mechanism** to the existing `spec.md` format and `check_sdd_assets.py` checker:

**1 — Two new optional fields in the Spec Readiness Gate section of `spec.md`:**

```
- SPEC_READY_EXCEPTION: <none|bug-fix|upgrade|refactor|chore|authorized-deviation>
- authorized-by: <github-handle>
```

Default values for new scaffolded specs: `none` / `none`. Existing `spec.md` files require no modification.

**2 — Reduced artifact requirement in `check_sdd_assets.py`:**

When `SPEC_READY_EXCEPTION` is set to a recognised value (not `none`) and `authorized-by` is non-empty, the checker:
- Skips existence checks for `plan.md`, `tasks.md`, `architecture.md`, `traceability.md`, `graph.json`, `evidence_manifest.json`, `context_pack.md`, `hardening_review.md`.
- Requires only `{spec.md, pr_context.md}` to be present and minimally valid.
- Demotes "implementation tasks checked while SPEC_READY is not true" from a violation to a non-blocking warning.
- Emits a structured log metric: `[METRIC] name=sdd_exception_gate_total value=1 type=<exception-type> authorized_by=<handle>`.

**3 — Scaffold template update:**

New `spec.md` scaffolds include `SPEC_READY_EXCEPTION: none` and `authorized-by: none` so the exception status is explicit from day one.

**4 — AGENTS.md policy update:**

New subsection documents the lightweight bypass track, per-type minimum traceability expectations, and the `authorized-by` requirement for audit visibility.

### Tiered minimum traceability (informative)

| Change type | `SPEC_READY_EXCEPTION` value | Minimum artifacts | Recommended traceability evidence in pr_context.md |
|---|---|---|---|
| Feature / Enhancement | `none` (or absent) | All 10 current artifacts | Full SDD — no change |
| Bug fix | `bug-fix` | `spec.md` + `pr_context.md` | Failing test (red) → fix commit → passing test (green) |
| Blueprint upgrade | `upgrade` | `spec.md` + `pr_context.md` | Link to `artifacts/blueprint/upgrade/` pipeline report |
| Refactor | `refactor` | `spec.md` + `pr_context.md` | Before/after suite green; no behavior change assertion |
| Chore / maintenance | `chore` | `spec.md` + `pr_context.md` OR no `specs/` dir + `AGENTS.decisions.md` entry | `AGENTS.decisions.md` entry with change rationale |

## Alternatives Considered

**Option B — Separate lightweight spec template (`spec.lite.md`):** scaffold creates a different file name when a `--type bug-fix` flag is passed; checker detects the file name. Rejected: fragments the artifact surface, requires CLI changes to the scaffold, and creates two parallel spec validation code paths that will drift independently.

**Option C — Remove the 10-artifact requirement for all specs (flatten to spec.md + pr_context.md always):** Rejected: traceability, graph.json, and tasks.md are high-value artifacts for feature work; removing them universally reduces governance quality without a net benefit.

## Consequences

- Blueprint maintainers and consumer engineers can start a bypass-track work item by scaffolding, setting `SPEC_READY_EXCEPTION`, and working directly toward `{spec.md, pr_context.md}` — no stub artifact ceremony.
- The `authorized-by` field provides an explicit human-readable audit trail for every exception-path evaluation visible in `git log` and CI metric output.
- Traceability for exception-path specs is lighter: requirement-to-test linkage is documented in pr_context.md as prose evidence rather than a machine-verifiable `traceability.md` table. This is a deliberate tradeoff for non-feature change types.
- `pr_context.md` required-section content validation is skipped on the bypass path; only presence is checked. This is intentional — the lightweight track removes ceremony, and section-content enforcement is disproportionate for non-feature changes. Engineers are expected to fill in the summary and evidence in good faith.
- No existing `spec.md` file requires modification. The new fields default to `none` and the checker is fully backward-compatible.
- Rollback: set `SPEC_READY_EXCEPTION: none` (or remove the field) to immediately restore full-SDD validation.

## References

- Issue: https://github.com/sbonoc/stackit-platform-blueprint/issues/275
- Spec: `specs/2026-05-14-issue-275-sdd-bypass-track/spec.md`
- Motivating case: `sbonoc/dhe-marketplace` PR #62
