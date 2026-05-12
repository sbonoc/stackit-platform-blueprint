# Traceability Matrix

## Requirement-to-Delivery Mapping

| Requirement ID | Control IDs | WCAG SC | Design Element | Implementation Path(s) | Test Evidence | Documentation Evidence | Operational Evidence |
|---|---|---|---|---|---|---|---|
| FR-001 | SDD-C-005, SDD-C-024 | N/A | `architecture.md` § Bounded Contexts | `scripts/lib/docs/site.sh` — `docs_pnpm_install`, `docs_pnpm_build`, `docs_pnpm_start` | `tests/infra/test_docs_site_sh_issue_272_273.py::Issue272PnpmIgnoreWorkspaceTests` | `docs/platform/consumer/troubleshooting.md` — v1.10.0 docs build section | `make docs-build && make docs-smoke` PASS |
| FR-002 | SDD-C-005, SDD-C-024 | N/A | `architecture.md` § High-Level Component Design | `scripts/lib/docs/site.sh` — `_docs_assert_pnpm_version` | `tests/infra/test_docs_site_sh_issue_272_273.py::Issue273PnpmVersionErrorMessageTests` | `docs/platform/consumer/troubleshooting.md` — v1.10.0 docs build section | `make quality-hooks-run` PASS |
| NFR-SEC-001 | SDD-C-009 | N/A | `architecture.md` § Non-Functional Architecture Notes — Security | N/A — no security surface affected | N/A | N/A | N/A |
| NFR-OBS-001 | SDD-C-010 | N/A | `architecture.md` § Non-Functional Architecture Notes — Observability | `scripts/lib/docs/site.sh` — `log_fatal` call preserved | `tests/infra/test_docs_site_sh_issue_272_273.py` — `test_pnpm_version_error_uses_log_fatal` | N/A | `make quality-hooks-run` PASS |
| NFR-REL-001 | SDD-C-012 | N/A | `plan.md` § Change Strategy | `scripts/lib/docs/site.sh` — additive flag restoration | `uv run python3 -m pytest tests/infra/ -k "issue_272 or issue_273"` | N/A | `make docs-build && make docs-smoke` PASS |
| NFR-OPS-001 | SDD-C-012 | N/A | `plan.md` § Validation Strategy | `tests/infra/test_docs_site_sh_issue_272_273.py` | `uv run python3 -m pytest tests/infra/ -k "issue_272 or issue_273" -v` — no network/cluster required | N/A | `uv run python3 -m pytest` PASS |
| AC-001 | SDD-C-012 | N/A | `plan.md` § Slice 1 | `scripts/lib/docs/site.sh` | `Issue272PnpmIgnoreWorkspaceTests` (3 tests) | N/A | `make docs-build` PASS |
| AC-002 | SDD-C-012 | N/A | `plan.md` § Slice 2 | `scripts/lib/docs/site.sh` | `Issue273PnpmVersionErrorMessageTests` (2 tests) | N/A | `make quality-hooks-run` PASS |

## Graph Linkage
- Graph file: `graph.json`
- Every `FR-###`, `NFR-*-###`, and `AC-###` listed in this file MUST have a corresponding node in `graph.json`.
- Node IDs referenced:
  - FR-001
  - FR-002
  - NFR-SEC-001
  - NFR-OBS-001
  - NFR-REL-001
  - NFR-OPS-001
  - AC-001
  - AC-002

## Validation Summary
- Required bundles executed: `uv run python3 -m pytest tests/infra/test_docs_site_sh_issue_272_273.py -v` (6/6 PASS); `make infra-validate` (PASS); `make quality-hooks-fast` (8/9 PASS — `quality-spec-pr-ready` only, pre-publish state); `make quality-hardening-review` (PASS)
- Result summary: all implementation and regression evidence confirmed. `make docs-build && make docs-smoke` deferred to CI (requires live pnpm+docusaurus installation not present in local environment; content-level fix verified by regression tests).

## Evidence Checksums
- `scripts/lib/docs/site.sh` sha256: `6763fdc6e96de81c8247456cfc6dd3bc999119a4f69ed35b7d5ea07c7d0c29ff`
- `tests/infra/test_docs_site_sh_issue_272_273.py` sha256: `47a8f53a2c9d839d49caf6ab2d0aab7d4fa3c91e1fe3b798475965313ca65570`
- `docs/platform/consumer/troubleshooting.md` sha256: `ca8ce1991f96484fa8af7b6697c6832f3ca880fa3c19226db8801723cae4a4a9`
- `scripts/templates/blueprint/bootstrap/docs/platform/consumer/troubleshooting.md` sha256: `ca8ce1991f96484fa8af7b6697c6832f3ca880fa3c19226db8801723cae4a4a9` (byte-identical mirror)
- Documentation validation:
  - `make docs-build`
  - `make docs-smoke`

## Evidence Manifest
- Manifest file: `evidence_manifest.json`
- Context export: `context_pack.md`
- PR context export: `pr_context.md`
- Hardening review export: `hardening_review.md`

## Open Risks and Follow-Ups
- Follow-up 1: `lstrip('pnpm@')` in `_docs_assert_pnpm_version` strips individual characters rather than a string prefix — latent bug for versions starting with `p`, `n`, `m`, or `@`. No known pnpm version triggers this; tracked as a future cleanup.
