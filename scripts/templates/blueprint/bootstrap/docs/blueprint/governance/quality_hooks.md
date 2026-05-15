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
| `make quality-hooks-fast` | Fast checks (shellcheck, SDD drift, CI sync, docs drift, AGENTS.md ↔ north_star.md cross-reference, path-gated infra, ACR staleness) | Slice boundary / pre-PR |
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

**Root-dotfile gap**: Root-level managed files (`.dockerignore`, `.gitignore`,
`.editorconfig`, `.pre-commit-config.yaml`, `Makefile`) do not match any of
the above prefixes, so editing them locally silences the `infra-validate`
bootstrap-template drift check. CI catches this via `QUALITY_HOOKS_FORCE_FULL=true`,
but developers get no local feedback. The commit-stage hook described below
closes this gap.

---

## Bootstrap Template Drift Hook

A commit-stage pre-commit hook (`quality-validate-bootstrap-template-drift`)
fires whenever a root-level managed file or its bootstrap template counterpart
changes. It invokes `validate_contract.py --bootstrap-drift-only`, which runs
only `_validate_bootstrap_template_sync` — faster than the full `infra-validate`
path, and scoped to the drift check only.

The hook fires on paths matching:

```
^(\.dockerignore|\.gitignore|\.editorconfig|\.pre-commit-config\.yaml|Makefile|scripts/templates/blueprint/bootstrap/)
```

To invoke the check manually:

```bash
make quality-validate-bootstrap-template-drift
```

This target is also available in generated consumer repos (delivered via the
bootstrap template) so the same drift guard applies after blueprint upgrade.

---

## Phase-Gating (Spec-Readiness Check)

`quality-spec-pr-ready` is skipped on `codex/*` branches unless the current
spec's `spec.md` contains `- SPEC_READY: true`. This prevents false-positive
failures during SDD Steps 1–6 when publish artifacts are intentionally scaffold.

Step 7 (PR Packager) invokes `make quality-hooks-fast` with
`QUALITY_HOOKS_FORCE_FULL=true` to run the spec-ready check unconditionally.

---

## ACR Staleness Gate

`quality-hooks-fast` includes `quality-a11y-acr-check` as a recipe step after
the main `hooks_fast.sh` run. The check validates that
`docs/platform/accessibility/acr.md` (the Accessibility Conformance Report):

- exists (non-zero exit with remediation message if missing),
- has a non-placeholder `Report date (last reviewed):` field,
- and is within the configured staleness window (default: 90 days, configurable
  via `blueprint/contract.yaml` `spec.quality.accessibility.acr_staleness_days`
  or the `ACR_STALENESS_DAYS` env var).

The check is wired into the consumer-side fast gate only. It is intentionally
**not** added to `quality-ci-blueprint` to avoid false positives in the blueprint's
own CI where no consumer ACR exists by default.

---

## AGENTS.md ↔ north_star.md Checks

Two dedicated make targets enforce the architectural boundary between
`AGENTS.md` (process and governance only) and `north_star.md` (architecture
content only). Both run as part of `quality-hooks-fast`.

### `quality-docs-cross-reference-check` — heading duplication detection

Runs in **all repos** (blueprint and consumer). Detects when `AGENTS.md`
contains a `##`/`###` heading that exactly matches (case-insensitive,
whitespace-normalized) a heading in `docs/platform/architecture/north_star.md`
(consumer path) or `docs/blueprint/architecture/north_star.md` (blueprint
fallback). Each match is reported as a named violation unless:

- The heading appears in the **Architecture Invariants — Pointers table** in
  `AGENTS.md` (sanctioned navigation pointer — the domain name MUST match the
  exact `north_star.md` heading text), or
- The heading is listed in `.quality-docs-cross-reference-allowlist.yml` at
  the repo root with a non-empty `justification` field.

Exits 0 when no violations are found, 1 when at least one violation is
detected. Graceful no-op (exit 0) when `AGENTS.md` or the resolved
`north_star.md` path is absent.

**Allowlist format** (`.quality-docs-cross-reference-allowlist.yml`):

```yaml
entries:
  - heading: Architecture Invariants
    justification: Intentionally mirrored as a navigation pointer in AGENTS.md.
```

### `quality-docs-agents-md-structure-check` — structural contract enforcement

Runs in **consumer repos only** (skipped in the blueprint template source via
the `blueprint_repo_is_generated_consumer` gate). Verifies that `AGENTS.md`
contains the two required structural elements introduced by the
AGENTS.md ↔ north_star.md anti-duplication contract:

1. `## Architecture Invariants — Pointers` section header.
2. A `north_star.md` reference within the `## Mandatory Workflow` section.

Each missing element produces exactly one violation with the
`[quality-docs-agents-md-structure-check]` prefix. Exits 1 when any element is
absent. Exits 0 when all elements are present or when `AGENTS.md` is absent.

**Consumer remediation after blueprint upgrade**: if the structure check fires,
add the missing sections to your `AGENTS.md` using the updated
`scripts/templates/consumer/init/AGENTS.md.tmpl` as a reference. The template
is self-documenting. See also:
`docs/platform/consumer/troubleshooting.md` § *AGENTS.md structure check fails after blueprint upgrade*.

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

---

## Consumer Extension Targets

Blueprint delivers two no-op `.PHONY` Make targets that consumers override in `platform.mk` without merge-conflict risk on blueprint upgrade:

| Target | When it runs | Tier | Default |
|---|---|---|---|
| `quality-consumer-pre-push` | pre-push hook (always_run) | Tier 1/unit | `@true` (no-op) |
| `quality-consumer-ci` | final step of `quality-ci-blueprint` | Tier 2/component | `@true` (no-op) |

### When to override

Add to `make/platform.mk` (consumer-owned, never overwritten on upgrade):

```makefile
# make/platform.mk
quality-consumer-pre-push:
	@$(MAKE) backend-test-unit
	@$(MAKE) touchpoints-test-unit

quality-consumer-ci:
	@$(MAKE) touchpoints-test-component
```

### Tier placement guidance

- **Tier 1 (`quality-consumer-pre-push`):** Unit tests that complete in seconds. Runs at every push. Keep this target fast.
- **Tier 2 (`quality-consumer-ci`):** Slower component or integration tests acceptable to run only in CI. Wired into `quality-ci-blueprint` as its final step — runs whenever the blueprint CI lane runs.

Consumers who do not override the stubs see no behavior change (stubs are `@true` — immediate exit 0).
