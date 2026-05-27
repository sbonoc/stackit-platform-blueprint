# Traceability Matrix

## Requirement-to-Delivery Mapping

| Requirement ID | Control IDs | Design Element | Implementation Path(s) | Test Evidence | Documentation Evidence | Operational Evidence |
|---|---|---|---|---|---|---|
| FR-001 | SDD-C-008, SDD-C-011 | `bootstrap.sh` auto-load call | `scripts/lib/shell/bootstrap.sh` | `test_bootstrap_calls_load_env_file_defaults` | ADR §302 Decision | log output (no-op path) |
| FR-002 | SDD-C-008 | `load_env_file_defaults` no-op when absent | `scripts/lib/shell/bootstrap.sh` (existing function) | `test_bootstrap_calls_load_env_file_defaults` (coverage via function contract) | ADR §302 Consequences | — |
| FR-003 | SDD-C-009 | Shell env wins via pre-existing export restore | `scripts/lib/shell/bootstrap.sh:load_env_file_defaults` | `test_env_local_does_not_override_existing_var` (AC-006) | spec.md NFR-SEC-001 | — |
| FR-004 | SDD-C-009 | `.env.local` in root `.gitignore` | `.gitignore` | `test_gitignore_contains_env_local` | spec.md NFR-SEC-002 | — |
| FR-005 | SDD-C-009, SDD-C-011 | `.env.local` in bootstrap template `.gitignore` | `scripts/templates/blueprint/bootstrap/.gitignore` | `test_bootstrap_template_gitignore_contains_env_local` | spec.md NFR-SEC-002 | — |
| FR-006 | SDD-C-008 | Post-apply `kubectl patch` in `deploy.sh` local path | `scripts/bin/infra/deploy.sh` | `test_deploy_references_argocd_local_target_revision` | ADR §284 Decision | `log_info` patch message |
| FR-007 | SDD-C-008 | Fallback to `git branch --show-current` | `scripts/bin/infra/deploy.sh:patch_argocd_local_target_revision` | `test_deploy_falls_back_to_git_branch` (AC-002) | spec.md FR-007 | log_info |
| FR-008 | SDD-C-008 | Skip guard: revision == main | `scripts/bin/infra/deploy.sh:patch_argocd_local_target_revision` | `test_deploy_skips_patch_on_main` | spec.md FR-008 | — |
| FR-009 | SDD-C-008 | Skip guard: empty revision (detached HEAD) | `scripts/bin/infra/deploy.sh:patch_argocd_local_target_revision` | `test_deploy_skips_patch_on_empty_branch` | spec.md FR-009 | — |
| FR-010 | SDD-C-008 | Skip guard: Application not found | `scripts/bin/infra/deploy.sh:patch_argocd_local_target_revision` | `test_deploy_skips_patch_when_app_missing` (AC-003 variant) | spec.md FR-010 | — |
| FR-011 | SDD-C-008 | STACKIT guard: patch only inside `is_local_profile` | `scripts/bin/infra/deploy.sh` | `test_deploy_patch_inside_local_profile_guard` | spec.md FR-011 | — |
| FR-012 | SDD-C-010 | `log_info` on patch execution | `scripts/bin/infra/deploy.sh:patch_argocd_local_target_revision` | `test_deploy_logs_effective_revision` | spec.md NFR-OBS-001 | log output |
| FR-013 | SDD-C-008 | Idempotent `kubectl patch --type=merge` | `scripts/bin/infra/deploy.sh:patch_argocd_local_target_revision` | `test_deploy_references_argocd_local_target_revision` (idempotency via merge patch) | spec.md NFR-REL-001 | — |
| NFR-OPS-001 | SDD-C-010 | `log_info` patch message in deploy.sh | `scripts/bin/infra/deploy.sh` | `test_deploy_logs_effective_revision` | spec.md NFR-OPS-001 | log output |
| NFR-SEC-001 | SDD-C-009 | `load_env_file_defaults` existing export preservation | `scripts/lib/shell/bootstrap.sh` | `test_env_local_does_not_override_existing_var` | spec.md NFR-SEC-001, ADR §Consequences | — |
| NFR-SEC-002 | SDD-C-009 | `.gitignore` entries | `.gitignore`, `scripts/templates/blueprint/bootstrap/.gitignore` | `test_gitignore_contains_env_local`, `test_bootstrap_template_gitignore_contains_env_local` | spec.md NFR-SEC-002 | — |
| AC-001 | SDD-C-012 | patch sets targetRevision from var | `deploy.sh` | T-201, T-203 | — | — |
| AC-002 | SDD-C-012 | patch falls back to git branch | `deploy.sh` | T-201, T-205 | — | — |
| AC-003 | SDD-C-012 | skip on main | `deploy.sh` | T-202 | — | — |
| AC-004 | SDD-C-012 | STACKIT guard | `deploy.sh` | T-203 | — | — |
| AC-005 | SDD-C-012 | .env.local loaded | `bootstrap.sh` | T-101 | — | — |
| AC-006 | SDD-C-012 | shell env wins | `bootstrap.sh` / `load_env_file_defaults` | T-101 (via function contract) | — | — |
| AC-007 | SDD-C-012 | gitignore entries | `.gitignore` × 2 | T-102, T-103 | — | — |
| AC-008 | SDD-C-008, SDD-C-012 | ≥ 8 automated assertions | `tests/` | T-101 through T-205 (≥ 8) | — | — |
