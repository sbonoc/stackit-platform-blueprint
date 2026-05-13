# Plan

## Delivery Strategy

Two slices. Slice 1 (RED) adds contract assertions that fail before the relocation. Slice 2 (GREEN) executes the relocation: move blueprint-author test classes, update `required_seed_files`, fix import paths.

A prerequisite audit task (T-000) must be completed first and its output recorded in `architecture.md` before Slice 1 tests are written — the test targets depend on the final classification table.

---

## Slice 0 — Audit (prerequisite, no commit)

Run the classification audit on all 16 consumer-delivered `tests/infra/` files:

```bash
for f in $(python3 -c "
import yaml, pathlib
c = yaml.safe_load(pathlib.Path('blueprint/contract.yaml').read_text())
for p in c['spec']['repository']['required_seed_files']:
    if p.startswith('tests/infra/test_'):
        print(p)
"); do
  echo "=== $f ==="
  grep -c "blueprint/modules\|scripts/lib/blueprint\|scripts/bin/blueprint" "$f" || echo 0
  grep "^class" "$f"
done
```

Record final classification (blueprint-author / consumer-runtime / mixed) for each file and each class in `architecture.md`. This drives the Slice 1 test targets.

---

## Slice 1 — RED: Contract assertions

**Commit message:** `test(issue-270-test-ownership-contract): slice 1 — failing contract assertion for test taxonomy`

Add to `tests/blueprint/test_quality_contracts.py`:

- `test_required_seed_files_contain_no_blueprint_module_refs` — reads all files listed in `required_seed_files` that match `tests/infra/test_*.py`; asserts none contain the string `blueprint/modules/`. Expected: FAIL before relocation.

Run: `uv run python3 -m pytest tests/blueprint/test_quality_contracts.py -v -k "blueprint_module_refs"` — must be RED.

---

## Slice 2 — GREEN: Relocation

**Commit message:** `feat(issue-270-test-ownership-contract): slice 2 — relocate blueprint-author tests, update required_seed_files`

For each file classified as **blueprint-author** in the audit:
1. Move the file to `tests/blueprint/test_<name>.py`.
2. Update imports if any reference `tests/infra/`-specific conftest or fixtures.
3. Remove the path from `required_seed_files` in `blueprint/contract.yaml`.

For each file classified as **mixed**:
1. Extract blueprint-author test classes to `tests/blueprint/test_<name>_blueprint.py` (or append to an existing file if scope matches).
2. Remove those classes from the original `tests/infra/` file.
3. Update `required_seed_files` to keep the `tests/infra/` path (now consumer-runtime only).

Run:
```bash
uv run python3 -m pytest tests/blueprint/ -v         # all green including new assertion
uv run python3 -m pytest tests/infra/ -v             # consumer-runtime tests still green
make infra-validate                                   # contract.yaml valid
make quality-hooks-fast                               # all quality gates pass
```

---

## Slice 3 — Docs + taxonomy rule

**Commit message:** `docs(issue-270-test-ownership-contract): document tests/blueprint vs tests/infra taxonomy rule`

- Update `docs/blueprint/governance/` (ownership_matrix.md or a new page) with the normative rule: blueprint-author tests go in `tests/blueprint/`, consumer-runtime tests in `tests/infra/`.
- Sync to bootstrap template mirrors: `python3 scripts/lib/docs/sync_blueprint_template_docs.py`.
- `make quality-docs-check-changed` — must pass.

---

## App Onboarding Contract (Normative)
- Required minimum make targets:
  - `apps-bootstrap`
  - `apps-smoke`
  - `backend-test-unit`
  - `backend-test-integration`
  - `backend-test-contracts`
  - `backend-test-e2e`
  - `touchpoints-test-unit`
  - `touchpoints-test-integration`
  - `touchpoints-test-contracts`
  - `touchpoints-test-e2e`
  - `test-unit-all`
  - `test-integration-all`
  - `test-contracts-all`
  - `test-e2e-all-local`
  - `infra-port-forward-start`
  - `infra-port-forward-stop`
  - `infra-port-forward-cleanup`
- App onboarding impact: no-impact
- Notes: No Make-target contract changes affecting app delivery; all listed targets are pre-existing and unaffected by this work item.
