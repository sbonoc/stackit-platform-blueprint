# ADR-20260423-issue-160-bootstrap-consumer-seeded-paths-guard: Honour consumer_seeded paths in infra bootstrap

## Metadata
- Status: approved
- Date: 2026-04-23
- Owners: bonos
- Related spec path: specs/2026-04-23-issue-160-bootstrap-consumer-seeded-paths-guard/spec.md

## Business Objective and Requirement Summary
- Business objective: Allow generated-consumer repos to delete blueprint placeholder manifests from git without `make infra-bootstrap` recreating them on every fresh checkout.
- Functional requirements summary: Add a `blueprint_path_is_consumer_seeded` guard to `ensure_infra_template_file` and `ensure_infra_rendered_file` in `scripts/bin/infra/bootstrap.sh`, mirroring the existing `blueprint_path_is_init_managed` guard. Consumer-seeded paths are silently skipped; a log_info diagnostic and `infra_consumer_seeded_skip_count` metric are emitted.
- Non-functional requirements summary: purely additive shell guard using an existing helper; no new env vars, no subprocess, no shell injection.
- Desired timeline: 2026-04-23.

## Decision Drivers
- Driver 1: `ensure_infra_template_file` already honours `init_managed_paths` but ignores `consumer_seeded_paths`, which are a first-class path class in the blueprint contract.
- Driver 2: The only current workaround is to keep unwanted placeholder files committed at template content — functionally inert but polluting and confusing.

## Options Considered
- Option A: Add `blueprint_path_is_consumer_seeded` guard to both functions (mirrors the init_managed pattern).
- Option B: Leave as-is and document the workaround.

## Decision
- Selected option: Option A
- Rationale: Option A is consistent with how `init_managed_paths` is handled, uses an existing helper, and is purely additive — repos without `consumer_seeded` declarations are unaffected. Option B leaves a confusing workaround as the only path forward for consumers.

## Consequences
- Positive: Consumers can delete placeholder manifests from git and rely on bootstrap not recreating them, as long as the paths are declared in `blueprint/contract.yaml` under `consumer_seeded`.
- Negative: Consumers who miscategorize an actually-managed path as `consumer_seeded` will silently not get the file recreated; this is intentional (consumer owns the decision) but requires care.
- Neutral: No new env vars, no make target changes, no docs changes required.

## Diagram

```
ensure_infra_template_file(relative_path)
  ├─ is_init_managed?  → yes → check file exists (fatal if missing) → return 0
  ├─ is_consumer_seeded? → yes → log_info + increment counter → return 0
  └─ otherwise → ensure_file_from_template (creates from template)
```
