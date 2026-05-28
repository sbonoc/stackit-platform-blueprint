# Hardening Review

## Repository-Wide Findings Fixed
- Finding: no repository-wide hardening regressions introduced. Both changes are local developer tooling only; no production runtime path is modified. Confirmed at implementation time: `make quality-hooks-fast` passes 10/11 checks (quality-spec-pr-ready resolves when Slice 3 publish tasks are marked [x]); `python3 -m pytest tests/blueprint/test_tooling_contracts.py::LocalDxImprovementsTests -v` → 8 passed (2026-05-27).

## Security Review

### `.env.local` credential protection (NFR-SEC-001, NFR-SEC-002)
- `load_env_file_defaults` preserves pre-existing exports before sourcing `.env.local`, then restores them after. Shell environment always wins. A CI system or developer shell that exports credentials before running `make` is not at risk of having those values overridden by `.env.local`.
- `.env.local` MUST appear in both `.gitignore` (root) and `scripts/templates/blueprint/bootstrap/.gitignore` (consumer template). This is enforced by test assertions T-102 and T-103 (Slice 1).
- `.env.local` is not encrypted. Engineers MUST NOT store plaintext production credentials in `.env.local`. The gitignore entry prevents accidental commits; cloud storage sync (e.g., Dropbox, iCloud) is the developer's responsibility. This is the same risk posture as any `.env*` local file pattern.

### ArgoCD patch (no credential surface)
- `patch_argocd_local_target_revision()` writes only `spec.source.targetRevision` — a branch name, not a secret. The patch uses `run_kubectl_with_active_access`, which respects the active kubeconfig (Docker Desktop local context). No credentials are written or read.
- The patch is guarded to local profile only (FR-011), preventing accidental execution against STACKIT clusters.

## Observability and Diagnostics Changes
- `deploy.sh` logs the effective `targetRevision` when the patch is applied (FR-012). No other instrumentation changes.

## Architecture and Code Quality Compliance
- Both changes use existing helpers (`load_env_file_defaults`, `run_kubectl_with_active_access`). No new abstractions introduced.
- `deploy.sh` patch logic is inline in the local profile branch — clean, no side effects on other paths.

## Accessibility Gate (Normative — non-UI reviewers mark non-applicable items N/A)
- N/A — no UI surfaces introduced or modified (NFR-A11Y-001).

## Proposals Only (Not Implemented)
- Proposal A: Encrypt `.env.local` at rest (e.g., via `age` or `sops`). Out of scope — adds tooling dependency for a local-dev convenience file; documented as a developer responsibility note in the README.
- Proposal B: Extend `ARGOCD_LOCAL_TARGET_REVISION` to patch multiple Applications. Out of scope — only `platform-local-core` is relevant for this pattern; multi-app patching would require a list-based contract.
