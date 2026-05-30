# Hardening Review

## Repository-Wide Findings Fixed
- Finding 1: (pending — Step 5 implementation phase will surface any incidental drift)

## Observability and Diagnostics Changes
- Metrics/logging/tracing updates: Grafana dashboard gains `execution_mode` panel facet (NFR-OBS-001). Opt-out rate panel surfaces `c7-emission-opted-out` event count over rolling 30-day window with alert threshold > 5%.
- Operational diagnostics updates: Helper failure logs to stderr (NFR-REL-001); SDD step pass/fail decoupled from C7 emission success. FR-008 audit predicate gains `unknown`-model exemption (NFR-OBS-002).

## Architecture and Code Quality Compliance
- SOLID / Clean Architecture / Clean Code / DDD checks: Helper follows hexagonal layering — `LifecycleEvent` (domain), `EmitC7EventUseCase` + `OptOutAuditUseCase` (application), `JsonlSinkAdapter` + `JsonlReaderAdapter` + `EnvVarModelResolver` (infrastructure), CLI entrypoint (presentation). Pydantic v2 model is the single source of envelope truth.
- Test-automation and pyramid checks: Unit (envelope, env-var resolver, event_id derivation) + contract (JSON Schema validation, round-trip parity) + integration (#336 PR-event ingest with dedupe-on-replay) — pyramid intact, no integration-heavy substitution for unit coverage.
- Documentation/diagram/CI/skill consistency checks: Uniform "## C7 Emission" addendum across all seven step skills validated by extension to `check_sdd_assets.py` (T-031); bootstrap mirror docs re-synced via `sync_blueprint_template_docs.py` (T-002 + T-053).

## Accessibility Gate (Normative — non-UI reviewers mark non-applicable items N/A)
- [x] SC 4.1.2 (Name, Role, Value): N/A — no UI surface
- [x] SC 2.1.1 (Keyboard): N/A — no UI surface
- [x] SC 2.4.7 (Focus Visible): N/A — no UI surface
- [x] SC 1.4.1 (Use of Color): N/A — no UI surface
- [x] SC 3.3.1 (Error Identification): N/A — no UI surface
- [x] axe-core WCAG 2.1 AA scan evidence: N/A — no UI surface (NFR-A11Y-001 declared in spec.md)

## Proposals Only (Not Implemented)
- Proposal 1: Consumer-repo C7 emission — defer to a follow-up work item once `artifacts/c7/*.jsonl` stabilizes on the blueprint side.
- Proposal 2: JSONL line signing / HMAC — pending Q-2 resolution; default no.
- Proposal 3: IDE-extension direct emission — helper remains CLI-only for this iteration.
