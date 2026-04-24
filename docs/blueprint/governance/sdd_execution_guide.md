# SDD Execution Guide

This page is the practical, step-by-step walkthrough of how the
[SDD lifecycle](spec_driven_development.md) executes in this repository:
what command starts each step, what artifacts are produced, when commits
and PRs are created, and what checks run.

For normative rules, artifact contracts, guardrails, and sign-off policy,
see [Spec-Driven Development Operating Model](spec_driven_development.md).

---

## Step 0 — Scaffold

**Command:**

```bash
make spec-scaffold SPEC_SLUG=<work-item-slug>
```

**What happens:**

- Creates `specs/YYYY-MM-DD-<slug>/` with all required stub artifacts (see below).
- Checks out a dedicated branch `codex/YYYY-MM-DD-<slug>` automatically.
  Skip with `SPEC_NO_BRANCH=true` only when explicitly asked.

**Artifacts created (all stubs at this point):**

| File | Purpose |
|---|---|
| `spec.md` | Requirements, sign-offs, readiness gate fields |
| `architecture.md` | High-level bounded context exploration workspace |
| `plan.md` | Delivery slices and validation strategy |
| `tasks.md` | Gate checks, implementation tasks, publish tasks |
| `traceability.md` | REQ/NFR/AC → code → test → doc matrix |
| `graph.json` | Machine-readable traceability graph (nodes + edges) |
| `context_pack.md` | Execution handoff snapshot for coding agents |
| `evidence_manifest.json` | Deterministic file checksum evidence record |
| `pr_context.md` | Reviewer-facing summary (filled at Publish) |
| `hardening_review.md` | Security/quality findings (filled at Publish) |

**Git:** no commit yet — files exist on disk on the new branch.  
**Checks:** none.

---

## Step 1 — Discover + High-Level Architecture + Specify

These three phases fill in `spec.md`, `architecture.md`, and the ADR
before any planning or implementation begins.

### Discover

Scope boundaries, constraints, NFRs, and cross-cutting guardrails are
written into `spec.md`. Any missing input is marked
`[NEEDS CLARIFICATION: ...]`; the work item is set to
`BLOCKED_MISSING_INPUTS` and stays `SPEC_READY: false` until resolved.
Coding assistants must not fill missing requirements with assumptions.

### High-Level Architecture

Bounded contexts, module boundaries, and integration edges are captured
in `architecture.md`. Finalized decisions are recorded as an ADR:

- Blueprint maintainer track: `docs/blueprint/architecture/decisions/ADR-<slug>.md`
- Generated-consumer track: `docs/platform/architecture/decisions/ADR-<slug>.md`

The ADR starts with `Status: proposed`.

### Specify

Normative requirements (`REQ-###`, `NFR-###`, `AC-###`) are written
using `MUST` / `MUST NOT` / `SHALL` / `EXACTLY ONE OF` only.
Forbidden terms (`should`, `may`, `could`, `might`, `etc.`) are not
allowed in normative sections. Applicable `SDD-C-###` control IDs from
`.spec-kit/control-catalog.md` are declared in `spec.md`.
`SPEC_PRODUCT_READY: true` is set after the Product sign-off is granted.

**Git:** no commit at the end of this step — artifacts are still being refined.  
**Checks:** `make quality-sdd-check` — validates language policy (forbidden
terms), open-marker counts, readiness gate fields, and control ID presence.

---

## Step 2 — Plan

Delivery slices, task breakdown, and the traceability graph are defined.

**Artifacts updated:**

| File | Content added |
|---|---|
| `plan.md` | Sequenced delivery slices (red→green TDD, docs, runbook), validation strategy, rollback notes |
| `tasks.md` | Gate tasks `G-###`, implementation tasks `T-###`, validation tasks `T-2##`, publish tasks `P-###`, app-onboarding targets `A-###` — all unchecked |
| `graph.json` | Nodes for every REQ/NFR/AC, edges for `validated_by` and `constrains` relations |
| `traceability.md` | Full matrix mapping each requirement to design element, implementation path, test evidence, documentation evidence, operational evidence |

**Git:** no commit yet.  
**Checks:** `make quality-sdd-check` (graph.json schema, traceability completeness).

---

## Step 3 — Sign-off → `SPEC_READY: true`

The user grants all four sign-offs explicitly in conversation or PR
review. Coding assistants must not self-approve any sign-off.

| Sign-off | What it covers |
|---|---|
| Product | Requirements completeness, acceptance criteria |
| Architecture | Design decisions, ADR approval (`Status: proposed → approved`) |
| Security | NFR-SEC controls, threat model coverage |
| Operations | Runbook readiness, rollback strategy, observability |

Once all four are recorded, `spec.md` is updated:
`SPEC_READY: false → true`, ADR status `proposed → approved`.

**Git:** commit all spec artifacts + push + open **draft PR**.

```bash
git add specs/YYYY-MM-DD-<slug>/ docs/.../ADR-<slug>.md
git commit -m "feat(<slug>): SDD intake — spec, architecture, plan ready for implementation"
git push -u origin codex/YYYY-MM-DD-<slug>
gh pr create --draft --title "..." --body "..."
```

**Checks:** `make quality-sdd-check` must pass before the draft PR is opened.

---

## Step 4 — Implement

Code is written in TDD slices following the sequence in `plan.md`.

### Slice 1 — Failing tests (red)

Write all new tests first. Confirm each fails with the expected error
before writing any implementation. This is a hard gate — the test must
be red before the fix goes in.

### Slice 2 — Implementation (green)

Write the implementation. Confirm all new tests pass and the full suite
has no regressions.

### Additional slices

Schema updates, skill runbook changes, configuration updates — per the
plan.

**Git:** one commit per logical slice (or bundled), pushed to the feature
branch. The draft PR updates automatically.

```bash
git add <changed files>
git commit -m "..."
git push
```

**Checks per slice:**

```bash
# Targeted
python3 -m pytest tests/<module>/ -v -k "<marker>"

# Full suite — no regressions
python3 -m pytest tests/ -q
```

---

## Step 5 — Document + Operate

### Document

- Update `docs/` files to describe the new or changed behavior.
- Run the docs sync script to propagate changes to bootstrap templates:

```bash
python3 scripts/lib/docs/sync_blueprint_template_docs.py
```

- Update skill runbooks in `.agents/skills/*/SKILL.md` when
  operator-facing guidance changes.

### Operate

- Add or update runbooks, diagnostics guidance, and rollback steps to
  the relevant `docs/` or `SKILL.md` files.

**Git:** commit docs + skill updates, push.  
**Checks:**

```bash
make quality-docs-check-changed   # pyramid ratios + doc drift for changed paths
```

---

## Step 6 — Publish

Fill the remaining artifacts and run the final validation gate.

**Artifacts completed:**

| File | Content |
|---|---|
| `hardening_review.md` | Repo-wide findings fixed, observability/diagnostics changes, quality compliance notes, proposals-only section |
| `pr_context.md` | Summary, full REQ/NFR/AC coverage, key reviewer files, exact validation commands + results, risk + rollback, deferred proposals |
| `tasks.md` | All task boxes marked `[x]` |

**Git:** final commit + push.

```bash
git add specs/YYYY-MM-DD-<slug>/
git commit -m "..."
git push
```

**Checks (all must pass):**

```bash
make quality-hooks-fast        # SDD check + docs drift + infra contract tests + shell source graph
make quality-hardening-review  # hardening_review.md completeness
# quality-spec-pr-ready is embedded inside quality-hooks-fast:
#   - tasks.md fully checked
#   - pr_context.md fields non-empty
```

---

## Step 7 — PR Ready + CI

Mark the draft PR as ready for review and request a review pass.

```bash
gh pr ready <number>
gh pr comment <number> --body "@codex review this PR"
```

**CI checks triggered on push/ready:**

| Check | What it runs |
|---|---|
| `blueprint-quality` | Full quality gate: SDD check, docs sync drift, infra contract tests, test pyramid, pre-commit hooks |
| `generated-consumer-smoke` | End-to-end smoke on a generated-consumer repo applying the blueprint |
| `upgrade-e2e-validation` | Upgrade pipeline validation (skipped on non-upgrade-scope PRs) |

All must be green (or legitimately skipped) before merge.

---

## Summary

| Step | Key artifacts | Git operation | Checks |
|---|---|---|---|
| 0 Scaffold | All stub files in `specs/YYYY-MM-DD-<slug>/` | New branch, no commit | None |
| 1 Discover / Arch / Specify | `spec.md`, `architecture.md`, ADR (`proposed`) | None | `quality-sdd-check` |
| 2 Plan | `plan.md`, `tasks.md`, `graph.json`, `traceability.md` | None | `quality-sdd-check` |
| 3 Sign-off | `spec.md` (`SPEC_READY=true`), ADR (`approved`) | Commit + push + draft PR | `quality-sdd-check` |
| 4 Implement | Code, tests, schemas | Per-slice commits + push | `pytest` (targeted + full suite) |
| 5 Document / Operate | `docs/`, `SKILL.md`, bootstrap template sync | Commit + push | `quality-docs-check-changed` |
| 6 Publish | `pr_context.md`, `hardening_review.md`, `tasks.md` | Final commit + push | `quality-hooks-fast`, `quality-hardening-review` |
| 7 PR ready | — | Mark PR ready | CI: `blueprint-quality`, `generated-consumer-smoke`, `upgrade-e2e-validation` |

---

## Related

- [SDD Operating Model](spec_driven_development.md) — normative rules,
  artifact contracts, guardrails, sign-off policy, and normative language rules
- [Assistant Compatibility](assistant_compatibility.md) — how non-Codex
  assistants (including Claude Code) apply this lifecycle
