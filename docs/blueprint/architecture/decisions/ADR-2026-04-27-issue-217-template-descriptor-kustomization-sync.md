# ADR: Issue #217 — Descriptor-Kustomization Cross-Check in Template Smoke Assertions

- **Status**: approved
- **Date**: 2026-04-27
- **Issues**: #217
- **Work item**: `specs/2026-04-27-issue-217-template-descriptor-kustomization-sync/`

## Context

`make blueprint-template-smoke` generates a synthetic consumer repo, runs
`infra-validate` against it, and then runs Python assertions in
`scripts/lib/blueprint/template_smoke_assertions.py`. The `infra-validate`
step calls `validate_app_descriptor` → `verify_kustomization_membership`,
which checks that every manifest filename declared in `apps/descriptor.yaml`
is listed in `infra/gitops/platform/base/apps/kustomization.yaml`.

However, `template_smoke_assertions.py:main()` does not perform this
cross-check itself. It verifies that the kustomization has resources and that
those resource files exist on disk, but it does not compare the kustomization
resource set against the descriptor's declared manifest filenames.

When the two seed templates diverge — the consumer init descriptor template
(`scripts/templates/consumer/init/apps/descriptor.yaml.tmpl`) references
filenames that the infra bootstrap kustomization template
(`scripts/templates/infra/bootstrap/infra/gitops/platform/base/apps/kustomization.yaml`)
does not list — the `infra-validate` step fails with 4 membership errors:

```
error: apps/descriptor.yaml: app[backend-api].component[backend-api]: deployment manifest filename not listed in infra/gitops/platform/base/apps/kustomization.yaml: backend-api-deployment.yaml
```

This failure cascades to `blueprint-upgrade-consumer-validate` and
`blueprint-upgrade-fresh-env-gate`, blocking every consumer upgrade regardless
of their local repo state.

The Python assertions step is the right place to add an explicit cross-check
because it runs after the full `init-repo → infra-bootstrap → infra-validate`
sequence and can produce a human-readable error that identifies the missing
filename and both file paths, making the root cause immediately actionable.

## Decision

**Add a descriptor-kustomization cross-check assertion to
`template_smoke_assertions.py:main()` that runs when `APP_RUNTIME_GITOPS_ENABLED=true`.**

After the existing kustomization resource non-empty check (which already
computes `app_manifest_names` from the generated kustomization), the assertion:

1. Reads the seeded `apps/descriptor.yaml` from the generated temp repo using `yaml.safe_load`.
2. For each app's components, extracts the manifest filename via `Path(manifests.get("deployment") or f"{component_id}-deployment.yaml").name` and `Path(manifests.get("service") or f"{component_id}-service.yaml").name`.
3. Checks each extracted filename against the already-computed `app_manifest_names` set.
4. Raises AssertionError per missing filename with a message naming the missing filename, the descriptor path, and the kustomization path.

This reuses the already-loaded kustomization resource set (`app_manifest_names`)
and adds a single read of the seeded descriptor. The convention-default path
derivation (`{component_id}-{kind}.yaml`) is copied from `_resolve_manifest_path`
in `app_descriptor.py` to avoid false-positive errors for components that
omit the explicit `manifests:` block.

## Alternatives Considered

**Alternative A — extract a standalone `assert_descriptor_kustomization_agreement()` helper in `app_descriptor.py`**: Rejected. The check is smoke-specific — it compares two seeded files in the generated temp repo scope. Exporting it to `app_descriptor.py` would couple a generated-repo-scope check with the live-repo validation library used in `infra-validate`.

**Alternative B — rely solely on `infra-validate` stderr for the error signal**: Rejected. `infra-validate` exits non-zero and the error appears in its stderr output, but the Python assertions step produces no named error. Operators must inspect infra-validate logs to find the root cause. The explicit Python assertion provides a self-explanatory message in CI without requiring log inspection.

## Consequences

- `scripts/lib/blueprint/template_smoke_assertions.py`: extended `main()` with a descriptor-kustomization cross-check assertion block after the existing `app_manifest_names` computation.
- `tests/blueprint/test_template_smoke_assertions.py`: extended with a new test class covering (a) consistent descriptor+kustomization passes, (b) missing filename raises AssertionError with message naming file and paths, (c) convention-default path handling, (d) template file content agreement (descriptor.yaml.tmpl and kustomization.yaml infra bootstrap template reference the same filenames).
- No changes to `validate_contract.py`, `app_descriptor.py`, consumer contract, or make targets.
- Future template edits that introduce descriptor-kustomization drift are caught at `make blueprint-template-smoke` time with a human-readable error, before reaching consumer upgrade validation.
