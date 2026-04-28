# Quality Hooks Operations Guide

This page documents the `quality-hooks-*` make targets: their inner-loop vs
pre-PR usage policy, keep-going mode, environment variables, path-gating and
phase-gating behaviour, the deduplication rationale, and the recommended
agent inner-loop usage pattern.

For the normative policy, see `AGENTS.md § Quality Hooks — Inner-Loop and Pre-PR Usage` in the repository root.

---

## Targets

| Target | Purpose | Typical gate |
|---|---|---|
| `make quality-hooks-fast` | Fast checks (shellcheck, SDD drift, CI sync, docs drift, path-gated infra) | Slice boundary / pre-PR |
| `make quality-hooks-strict` | Slower audit checks (version audit, template smoke) | Pre-push / PR Packager |
| `make quality-hooks-run` | Composite: fast then strict | Full pre-push gate |

---

## Inner-Loop vs Pre-PR Usage

**Per-slice gate**: `make test-unit-all` — run after every code edit within a slice.
Fast, targeted, no infra cost.

**Slice-batch / pre-PR gate**: `make quality-hooks-fast` — run at the boundary
between slices (before starting the next) and once more immediately before
publishing. Not run after every individual code edit.

**Pre-push gate**: `make quality-hooks-run` — runs both fast and strict phases.
Required by the PR Packager.

---

## Keep-Going Mode

By default the gate aborts on the first failure (fail-fast). Set
`QUALITY_HOOKS_KEEP_GOING=true` to switch to aggregation mode:

```bash
QUALITY_HOOKS_KEEP_GOING=true make quality-hooks-fast
# or
make quality-hooks-fast  # (with QUALITY_HOOKS_KEEP_GOING exported via .envrc or .claude/settings.json)
```

In keep-going mode:

- Each downstream check runs regardless of whether earlier checks failed.
- A consolidated summary block is emitted at the end showing PASS/FAIL per check and duration.
- The gate exits with code 1 if any check failed.
- Per-check failure output (last `QUALITY_HOOKS_KEEP_GOING_TAIL_LINES` lines, default 40)
  is re-emitted to stderr immediately after the check fails.
- A `quality_hooks_keep_going_total` metric is emitted on completion.

**Failure-cascade caveat**: A single root cause (e.g. a syntax error in a shared
helper) can produce failures in multiple aggregated checks. Fix the
earliest-reported failure first and re-run, rather than mass-applying fixes for
every line in the summary block.

---

## Environment Variables

| Variable | Default | Meaning |
|---|---|---|
| `QUALITY_HOOKS_KEEP_GOING` | unset (fail-fast) | Set to `true` to aggregate all independent failures |
| `QUALITY_HOOKS_KEEP_GOING_TAIL_LINES` | `40` | Lines of output to re-emit to stderr on per-check failure |
| `QUALITY_HOOKS_FORCE_FULL` | unset | Set to `true` to bypass path-gating and phase-gating |
| `QUALITY_HOOKS_PHASE` | set by script | Phase label (`fast` or `strict`) for keep-going metrics |

---

## Path-Gating (Infra Checks)

`infra-validate` and `infra-contract-test-fast` in the fast gate are skipped
(with a `quality_hooks_skip_total` metric) when no changed path matches the
gating set:

- `infra/`
- `blueprint/contract.yaml`
- `scripts/lib/blueprint/`
- `scripts/bin/blueprint/`
- `scripts/templates/blueprint/`
- `make/`
- `apps/`
- `pyproject.toml`
- `requirements*.txt`

The path check is a union of the merge-base diff and the current working-tree diff.

Set `QUALITY_HOOKS_FORCE_FULL=true` to force all checks regardless of changed paths.

---

## Phase-Gating (Spec-Readiness Check)

`quality-spec-pr-ready` is skipped on `codex/*` branches unless the current
spec's `spec.md` contains `- SPEC_READY: true`. This prevents false-positive
failures during SDD Steps 1–6 when publish artifacts are intentionally scaffold.

Step 7 (PR Packager) invokes `make quality-hooks-fast` with
`QUALITY_HOOKS_FORCE_FULL=true` to run the spec-ready check unconditionally.

---

## Deduplication Rationale

`quality-docs-lint` and `quality-test-pyramid` were removed as standalone
`run_cmd` invocations from `hooks_fast.sh`. They are now run exclusively by
`pre-commit` (which calls the same make targets via hooks). This prevents
double-execution when pre-commit is installed.

If `pre-commit` is not installed, a `log_warn` message directs the user to
install it (`https://pre-commit.com/`), and the quality-docs-lint and
quality-test-pyramid checks are skipped until pre-commit is available.

---

## Agent Inner-Loop Usage

Any agent session in this repository MUST have `QUALITY_HOOKS_KEEP_GOING=true`
in its environment. The `.envrc` (direnv) and `.claude/settings.json` files
at the repo root export this automatically.

Recommended inner-loop pattern for an agent implementing SDD slices:

```bash
# After each code edit within a slice:
make test-unit-all           # per-slice gate — fast, targeted

# At each slice boundary (before starting the next slice):
make quality-hooks-fast      # slice-batch gate — aggregates all fast checks

# Before publishing (PR Packager):
make quality-hooks-run       # full pre-push gate (fast + strict)
```
