# PR Context

## Summary
- Work item: 2026-05-28-managed-cache-state-file-label-consistency
- Objective: Align `managed-cache` module-wrapper stub templates with the hyphenated state-file-label convention used by other multi-word modules (`secrets-manager`, `public-endpoints`). Single-word modules (`langfuse`, `neo4j`, `kms`) continue to use underscores as their natural module name has none.
- Scope boundaries: Four files under `scripts/templates/infra/module_wrappers/managed-cache/`. No runtime logic, observability code, contract surface, docs, or tests touched. The change is a 4-character string rename per file (`managed_cache_<action>` → `managed-cache_<action>`).

## Requirement Coverage
- Requirement IDs covered: REQ-001
- Acceptance criteria covered: AC-001, AC-002
- Contract surfaces changed: none. The `optional_module_wrapper_stub_invocation` metric label changes from `module=managed-cache` (unchanged — already hyphenated) to the same value; only the state-file artifact name aligns. No downstream consumer of these stub templates has implemented the body yet (`status=not_implemented`), so no real telemetry is affected.

## Key Reviewer Files
- Primary files to review first:
  - `scripts/templates/infra/module_wrappers/managed-cache/managed_cache_apply.sh.tmpl`
  - `scripts/templates/infra/module_wrappers/managed-cache/managed_cache_destroy.sh.tmpl`
  - `scripts/templates/infra/module_wrappers/managed-cache/managed_cache_plan.sh.tmpl`
  - `scripts/templates/infra/module_wrappers/managed-cache/managed_cache_smoke.sh.tmpl`
- High-risk files: none.

## Validation Evidence
- Required commands executed: `make quality-sdd-check` (passes); `grep -n 'write_state_file "managed_cache_' scripts/templates/infra/module_wrappers/managed-cache/` (zero matches — AC-001); `grep -n 'write_state_file "managed-cache_' scripts/templates/infra/module_wrappers/managed-cache/` (four matches — AC-002).
- Result summary: bypass-track quality gate passes; both acceptance-criteria greps satisfied.
- Artifact references: none.

## Risk and Rollback
- Main risks: none. Templates are stubs (`status=not_implemented`) that consumers replace with module-specific logic; no consumer has shipped this module yet.
- Rollback strategy: `git revert` the commit; no migration step required.

## Deferred Proposals
- none
