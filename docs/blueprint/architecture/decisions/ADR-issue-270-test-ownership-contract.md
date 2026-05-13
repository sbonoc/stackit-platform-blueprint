# ADR — Test Ownership Contract: Relocate Blueprint-Author Tests from tests/infra/ to tests/blueprint/

## Status

proposed

## Context

`tests/infra/test_*.py` files in `required_seed_files` are delivered to generated-consumer repos via the upgrade engine. Some of these files contain test classes that assert against blueprint-internal artefacts (`blueprint/modules/`, `scripts/lib/blueprint/`, etc.). When the blueprint ships a new version of such a test, the upgrade resolver 3-way-merges it into the consumer's copy, overwriting consumer state. The consumer's copy then fails because it asserts against blueprint-authoring artefacts that either do not exist in the consumer repo or have different content.

Evidence from a real consumer upgrade (sbonoc/dhe-marketplace, v1.7.0 → v1.10.0, PR #62): 19 false-positive test failures after the resolver overwrote `test_tooling_contracts.py`, `test_runtime_credentials_eso.py`, and `test_optional_modules.py`. Resolution required manual revert of three test files.

`tests/blueprint/` is already classified `source_only` in `ownership_path_classes` — files under it are never delivered to consumer repos.

## Decision

Relocate all blueprint-author test classes from `tests/infra/` to `tests/blueprint/`, following these rules:

1. **Entirely blueprint-author files**: moved wholesale to `tests/blueprint/test_<name>.py` and removed from `required_seed_files`.
2. **Mixed files**: split — blueprint-author classes extracted to `tests/blueprint/`, consumer-runtime classes kept in `tests/infra/`.
3. **Entirely consumer-runtime files**: unchanged; remain in `tests/infra/` and `required_seed_files`.

A contract assertion is added to verify that no file remaining in `required_seed_files` contains a direct reference to `blueprint/modules/`.

**Classification rule (normative for future maintainers):** A test belongs in `tests/blueprint/` if it asserts against `blueprint/`, `scripts/lib/blueprint/`, or `scripts/bin/blueprint/`. It belongs in `tests/infra/` if it asserts against the consumer's runtime infrastructure surface only.

## Alternatives Considered

**Option B — Per-file `source_only` override in `contract.yaml`**: Mark specific `tests/infra/` paths as `source_only` without moving the files. Rejected: leaves blueprint-author test classes in a directory whose name implies consumer-runtime scope; creates persistent taxonomy confusion for maintainers; requires a new contract mechanism when the existing `source_only` classification on `tests/blueprint/` already provides the right model.

**Option C — Active consumer cleanup (delete-on-upgrade)**: Actively delete stale copies of relocated files from consumer repos on next upgrade. Rejected for this work item: adds engine complexity; stale copies do not cause active failures in consumer CI (they are unreferenced after the resolver stops writing them); cleanup can happen via re-init.

## Consequences

- **Positive**: The upgrade engine can no longer overwrite consumer test files with blueprint-internal assertions. False-positive failures of the type seen in PR #62 are eliminated.
- **Positive**: `tests/blueprint/` and `tests/infra/` have clear, enforced taxonomies. The contract assertion (FR-005) prevents regression.
- **Positive**: `required_seed_files` shrinks, reducing the scope of 3-way merge candidates on every upgrade.
- **Neutral**: Stale copies of relocated files remain in existing consumer repos until re-init or manual deletion. These copies do not cause CI failures because the upgrade engine no longer overwrites them with failing blueprint-internal content.
- **Neutral**: One-time effort to audit and split mixed test files.

## Files Changed (Expected)

- `tests/blueprint/` — new and updated test files (relocated blueprint-author classes)
- `tests/infra/` — split files with blueprint-author classes removed
- `blueprint/contract.yaml` — `required_seed_files` updated (reduced)
- `tests/blueprint/test_quality_contracts.py` — new contract assertion (FR-005)
- `docs/blueprint/governance/` — taxonomy rule documented
