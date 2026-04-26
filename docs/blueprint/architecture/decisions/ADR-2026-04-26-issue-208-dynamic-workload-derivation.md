# ADR: Issue #208 — Dynamic Workload Derivation in bootstrap.sh and template_smoke_assertions.py

- **Status**: approved
- **Date**: 2026-04-26
- **Issues**: #208
- **Work item**: `specs/2026-04-26-issue-208-dynamic-workload-derivation/`

## Context

`scripts/bin/infra/bootstrap.sh` · `bootstrap_infra_static_templates()` and
`scripts/lib/blueprint/template_smoke_assertions.py` · `validate_app_runtime_conformance()`
both maintain hardcoded lists of app workload manifest filenames:

```bash
# bootstrap.sh — hardcoded
ensure_infra_template_file "infra/gitops/platform/base/apps/backend-api-deployment.yaml"
ensure_infra_template_file "infra/gitops/platform/base/apps/backend-api-service.yaml"
ensure_infra_template_file "infra/gitops/platform/base/apps/touchpoints-web-deployment.yaml"
ensure_infra_template_file "infra/gitops/platform/base/apps/touchpoints-web-service.yaml"
```

```python
# template_smoke_assertions.py — hardcoded
app_manifest_paths = [
    "infra/gitops/platform/base/apps/backend-api-deployment.yaml",
    "infra/gitops/platform/base/apps/backend-api-service.yaml",
    "infra/gitops/platform/base/apps/touchpoints-web-deployment.yaml",
    "infra/gitops/platform/base/apps/touchpoints-web-service.yaml",
]
```

These lists are redundant copies of the resources declared in the template
kustomization (`scripts/templates/infra/bootstrap/infra/gitops/platform/base/apps/kustomization.yaml`).
When a consumer renames their workloads, they update only the kustomization
(the obvious place). The hardcoded lists diverge silently; the mismatch
surfaces only in the `generated-consumer-smoke` CI job with no local
pre-commit signal.

Failure sequence:
1. Consumer renames workloads; updates template kustomization.
2. `make blueprint-bootstrap` runs `bootstrap_infra_static_templates()` → tries old hardcoded names.
3. Templates not found → FATAL logged + empty placeholder files created.
4. Smoke test checks hardcoded list → placeholders contain no `kind:` → `AssertionError`.
5. CI fails. No local hook catches this.

## Decision

**Replace hardcoded lists with dynamic derivation from the template kustomization.**

For `bootstrap.sh`: read resource filenames from the infra template kustomization
at `$(bootstrap_templates_root "infra")/infra/gitops/platform/base/apps/kustomization.yaml`
using `sed` to parse the `resources:` section. For each filename read, call
`ensure_infra_template_file`.

For `template_smoke_assertions.py`: add a stdlib-only helper
`_extract_kustomization_resources(text: str) -> list[str]` that parses the
`resources:` section of a kustomization YAML using `re`. In
`validate_app_runtime_conformance()`, read the consumer repo's
`infra/gitops/platform/base/apps/kustomization.yaml` and derive
`app_manifest_paths` from it at runtime.

The template kustomization is already the canonical source of truth for
which app manifests exist. Both call sites MUST read from it rather than
embedding redundant copies.

## Alternatives Considered

**Alternative A — sync the hardcoded lists via a generator script**: Rejected.
This preserves the redundancy and requires a separate generator update step
on every kustomization change. It does not remove the root cause.

**Alternative B — remove the smoke assertion entirely and rely on kustomize build**:
Rejected. The `workload_kinds_required_when_enabled` check in
`validate_app_runtime_conformance()` already calls kustomize build. Removing the
individual-file checks would reduce signal quality when files are missing
(kustomize errors are less precise than "file does not exist" assertions).

## Consequences

- `scripts/bin/infra/bootstrap.sh` · `bootstrap_infra_static_templates()`: four hardcoded `ensure_infra_template_file` calls replaced by a `sed`-based `while` loop reading the template kustomization.
- `scripts/lib/blueprint/template_smoke_assertions.py`: `_extract_kustomization_resources()` helper added; `validate_app_runtime_conformance()` derives `app_manifest_paths` dynamically.
- Test: `tests/blueprint/test_template_smoke_assertions.py` (new file) — unit tests for `_extract_kustomization_resources()` and for the dynamic derivation path in `validate_app_runtime_conformance()`.
- Test: `tests/blueprint/test_quality_contracts.py` — extended to assert no hardcoded app manifest filenames (`backend-api-deployment.yaml`, `backend-api-service.yaml`, `touchpoints-web-deployment.yaml`, `touchpoints-web-service.yaml`) appear in `bootstrap_infra_static_templates()`.
- No contract changes. No consumer-repo migration required. No CLI/Make target changes.
- Any consumer who renames workloads MUST update only `infra/gitops/platform/base/apps/kustomization.yaml`; `bootstrap.sh` and `template_smoke_assertions.py` stay correct automatically.
