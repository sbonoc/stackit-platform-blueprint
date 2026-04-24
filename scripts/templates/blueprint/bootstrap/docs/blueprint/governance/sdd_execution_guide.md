# SDD Execution Guide

This page is the practical, step-by-step walkthrough of how the
[SDD lifecycle](spec_driven_development.md) executes in this repository:
what command starts each step, what artifacts are produced, when commits
and PRs are created, and what checks run.

For normative rules, artifact contracts, guardrails, and sign-off policy,
see [Spec-Driven Development Operating Model](spec_driven_development.md).

---

## One PR per work item

A single Draft PR is opened at the intake gate and remains open for the
entire lifecycle. Every subsequent commit — sign-off resolutions,
implementation slices, docs, publish artifacts — is pushed to the same
branch and accumulates in the same PR. The PR transitions from Draft to
Ready only when the work is fully implemented, verified, and published.
It is never closed early and a second PR is never opened for the same
work item.

---

## Step 0 — Scaffold

**Command:**

```bash
make spec-scaffold SPEC_SLUG=<work-item-slug>
```

**What happens:**

- Creates `specs/YYYY-MM-DD-<slug>/` with all required stub artifacts.
- Checks out a dedicated branch `codex/YYYY-MM-DD-<slug>` automatically.
  Skip with `SPEC_NO_BRANCH=true` only when explicitly asked.

**Artifacts created (stubs, populated in Step 1):**

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
| `pr_context.md` | Reviewer-facing summary (completed at Publish) |
| `hardening_review.md` | Security/quality findings (completed at Publish) |

**Git:** no commit yet.  
**Checks:** none.

---

## Step 1 — Populate artifacts (Discover → Plan)

The four pre-implementation phases are executed in a single pass
immediately after scaffolding. Every artifact must contain real content
before the Draft PR opens. Stub placeholders are not acceptable in the
Draft PR.

### Discover

Scope boundaries, constraints, NFRs, and cross-cutting guardrails are
written into `spec.md`. Requirements (`REQ-###`), non-functional
requirements (`NFR-###`), and acceptance criteria (`AC-###`) are defined
using `MUST` / `MUST NOT` / `SHALL` / `EXACTLY ONE OF` only.

### High-Level Architecture

Bounded contexts, module boundaries, and integration edges are captured
in `architecture.md`. Where the core decision is clear, the ADR is
drafted now at `Status: proposed`. Open questions do not block ADR
creation unless they affect the central decision itself.

- Blueprint maintainer track: `docs/blueprint/architecture/decisions/ADR-<slug>.md`
- Generated-consumer track: `docs/platform/architecture/decisions/ADR-<slug>.md`

### Specify

Applicable `SDD-C-###` control IDs from `.spec-kit/control-catalog.md`
are declared. The `Implementation Stack Profile` section is fully
populated with stack, test automation, managed-service, and local-first
fields.

### Plan

`plan.md` is written with sequenced delivery slices (red→green TDD,
docs, runbook). `tasks.md` is populated with all task rows (all
unchecked). `graph.json` nodes and edges are generated for every
REQ/NFR/AC. `traceability.md` maps every requirement to design element,
implementation path, test evidence, documentation evidence, and
operational evidence.

### Handling open questions

Any input that cannot be resolved by the agent is recorded as a
structured block directly in the relevant artifact — not left as an
empty placeholder:

```
> **[NEEDS CLARIFICATION]** *Concise statement of what needs to be decided.*
>
> **Options:**
> - **A)** Description — tradeoffs (agent recommendation)
> - **B)** Description — tradeoffs
>
> **Agent recommendation:** Option A because [rationale].
```

The same block format is used in `spec.md`, `architecture.md`,
`plan.md`, and ADRs. Open questions do not block artifact population —
all sections that can be filled with real content are filled. The
`[NEEDS CLARIFICATION]` token is tracked by `quality-sdd-check` and
must reach `0` before `SPEC_READY: true`.

**Git:** no commit during this step — artifact population flows directly into Step 2.  
**Checks:** `make quality-sdd-check` (language policy, open-marker counts,
readiness gate fields, control ID presence).

---

## Step 2 — Open Draft PR (Intake gate)

Once all artifacts are substantively populated, commit everything and
open the Draft PR. This is the single PR for the entire work item.

```bash
git add specs/YYYY-MM-DD-<slug>/ docs/.../ADR-<slug>.md
git commit -m "feat(<slug>): SDD intake — spec, architecture, plan ready for PO review"
git push -u origin codex/YYYY-MM-DD-<slug>
gh pr create --draft --title "feat(<slug>): ..." --body "..."
```

The PR description references `specs/YYYY-MM-DD-<slug>/pr_context.md`
and the originating issue.

**Git:** commit + push + Draft PR opened.  
**Checks:** `make quality-sdd-check` must pass before opening the PR.

---

## Step 3 — Open question resolution loop

The PO and other reviewers examine the Draft PR on GitHub. This is the
canonical review mechanism and works regardless of whether reviewers
have Claude Code.

### How reviewers answer open questions

Reviewers leave answers as PR comments — inline on the relevant artifact
section or as general PR comments referencing the question. No special
format is required: plain language answers are sufficient.

For sign-offs, the following deterministic phrase is recognized by the
agent and recorded in `spec.md`:

```
SPEC_PRODUCT_READY: approved
```

### How the agent integrates answers

The developer invokes the agent with:

> *"Read the PR comments on #N and resolve the open questions in the artifacts."*

The agent:

1. Reads all PR comments and inline review comments.
2. Replaces each resolved `[NEEDS CLARIFICATION]` block with the
   decision and its rationale.
3. Records any sign-off phrases in `spec.md`.
4. Commits the updated artifacts and pushes to the same branch
   (same PR auto-updates).
5. Posts a follow-up PR comment:
   *"Resolved N open questions. Updated: `spec.md`, `architecture.md`.
   Commit abc1234. Remaining open: K."*

This closes the feedback loop for the reviewer — they can see their
answers were picked up and review the updated artifact inline. When
reviewers later have Claude Code, they can trigger the same resolution
step themselves.

The loop repeats until all `[NEEDS CLARIFICATION]` markers are resolved
and `SPEC_PRODUCT_READY: true` is recorded.

**Git:** one commit per resolution round, pushed to the existing branch (same PR).  
**Checks:** `make quality-sdd-check` after each round to confirm marker count drops.

---

## Step 4 — Remaining sign-offs → `SPEC_READY: true`

Architecture, Security, and Operations sign-offs are collected — via PR
review, PR comments, or conversation. Once all four sign-offs are
recorded in `spec.md` and all zero-count fields are confirmed:

- `SPEC_READY: false → true`
- ADR status: `proposed → approved`

```bash
git add specs/YYYY-MM-DD-<slug>/spec.md docs/.../ADR-<slug>.md
git commit -m "feat(<slug>): all sign-offs collected — SPEC_READY"
git push
```

**Git:** commit + push (same PR).  
**Checks:** `make quality-sdd-check` must pass with `SPEC_READY: true`.

---

## Step 5 — Implement

Code is written in TDD slices following the sequence in `plan.md`. All
commits go to the same branch and appear in the same Draft PR.

### Slice 1 — Failing tests (red)

Write all new tests first. Confirm each fails with the expected error
before writing any implementation.

### Slice 2 — Implementation (green)

Write the implementation. Confirm all new tests pass and the full suite
has no regressions.

### Additional slices

Schema updates, skill runbook changes, configuration updates — per the
plan.

**Git:** one commit per logical slice, pushed to the same branch.  
**Checks per slice:**

```bash
python3 -m pytest tests/<module>/ -v -k "<marker>"   # targeted
python3 -m pytest tests/ -q                           # full suite, no regressions
```

---

## Step 6 — Document + Operate

### Document

- Update `docs/` files to describe the new or changed behavior.
- Run the docs sync script to propagate changes to bootstrap templates:

```bash
python3 scripts/lib/docs/sync_blueprint_template_docs.py
```

- Update skill runbooks in `.agents/skills/*/SKILL.md` when
  operator-facing guidance changes.

### Operate

- Add or update runbooks, diagnostics guidance, and rollback steps in
  the relevant `docs/` or `SKILL.md` files.

**Git:** commit + push (same PR).  
**Checks:**

```bash
make quality-docs-check-changed
```

---

## Step 7 — Publish

Fill the remaining artifacts, mark all tasks complete, and pass the
final validation gate.

**Artifacts completed:**

| File | Content |
|---|---|
| `hardening_review.md` | Repo-wide findings fixed, observability/diagnostics changes, quality compliance notes, proposals-only section |
| `pr_context.md` | Summary, full REQ/NFR/AC coverage, key reviewer files, exact validation commands + results, risk + rollback, deferred proposals |
| `tasks.md` | All task boxes marked `[x]` |

**Git:** final commit + push (same PR).  
**Checks (all must pass):**

```bash
make quality-hooks-fast        # SDD check + docs drift + infra contract tests + shell source graph
make quality-hardening-review  # hardening_review.md completeness
# quality-spec-pr-ready is embedded inside quality-hooks-fast:
#   - tasks.md fully checked
#   - pr_context.md fields non-empty
```

---

## Step 8 — Mark PR ready + CI

The single Draft PR is marked ready for final review. No new PR is
opened.

```bash
gh pr ready <number>
gh pr comment <number> --body "@codex review this PR"
```

**CI checks triggered:**

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
| 0 Scaffold | Stub files in `specs/YYYY-MM-DD-<slug>/` | New branch, no commit | None |
| 1 Populate artifacts | `spec.md`, `architecture.md`, ADR, `plan.md`, `tasks.md`, `graph.json`, `traceability.md` — all with real content | None | `quality-sdd-check` |
| 2 Draft PR (intake gate) | All populated artifacts committed | Commit + push + **Draft PR opened** | `quality-sdd-check` |
| 3 Open question resolution | Artifacts updated with PO answers; sign-offs recorded | Commit + push per round (same PR) | `quality-sdd-check` |
| 4 SPEC_READY | `spec.md` (`SPEC_READY=true`), ADR (`approved`) | Commit + push (same PR) | `quality-sdd-check` |
| 5 Implement | Code, tests, schemas | Per-slice commits + push (same PR) | `pytest` targeted + full suite |
| 6 Document / Operate | `docs/`, `SKILL.md`, bootstrap template sync | Commit + push (same PR) | `quality-docs-check-changed` |
| 7 Publish | `pr_context.md`, `hardening_review.md`, `tasks.md` | Final commit + push (same PR) | `quality-hooks-fast`, `quality-hardening-review` |
| 8 PR ready | — | **Draft → Ready** (same PR) | CI: `blueprint-quality`, `generated-consumer-smoke`, `upgrade-e2e-validation` |

---

## Related

- [SDD Operating Model](spec_driven_development.md) — normative rules,
  artifact contracts, guardrails, sign-off policy, and normative language rules
- [Assistant Compatibility](assistant_compatibility.md) — how non-Codex
  assistants (including Claude Code) apply this lifecycle
