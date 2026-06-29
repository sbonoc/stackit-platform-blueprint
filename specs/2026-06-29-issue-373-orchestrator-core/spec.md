# Specification

## Spec Readiness Gate (Blocking)
<!-- SPEC_PRODUCT_READY=true: intake gate — Product sign-off only; unlocks agent ADR drafting.
     SPEC_READY=true: implementation gate — all sign-offs required; unlocks coding. -->
- SPEC_READY: false
- SPEC_PRODUCT_READY: false
- Open questions count: 0
- Unresolved alternatives count: 0
- Unresolved TODO markers count: 0
- Pending assumptions count: 0
- Open clarification markers count: 0
- Product sign-off: pending
- Architecture sign-off: pending
- Security sign-off: pending
- Operations sign-off: pending
- Missing input blocker token: none
- ADR path: docs/blueprint/architecture/decisions/ADR-issue-373-orchestrator-core.md
- ADR status: proposed
- SPEC_READY_EXCEPTION: none
- authorized-by: none

## Applicable Guardrail Controls (Normative)
- Applicable control IDs: SDD-C-001, SDD-C-002, SDD-C-003, SDD-C-004, SDD-C-005, SDD-C-006, SDD-C-007, SDD-C-008, SDD-C-009, SDD-C-010, SDD-C-011, SDD-C-012, SDD-C-013, SDD-C-016, SDD-C-017, SDD-C-019, SDD-C-020, SDD-C-021, SDD-C-024
- Control exception rationale: SDD-C-014 (local-first runtime) does not apply — this child ships a pure-Python importable module with zero runtime I/O; there is no containerised service to provision locally. SDD-C-015 (app onboarding Make-target contract) does not apply — the orchestrator core is platform/factory infrastructure, not an app-delivery workload. SDD-C-018 (upstream defect escalation) does not apply — no blueprint defect workaround. SDD-C-022 (HTTP smoke gate) does not apply — the module exposes no HTTP routes; its only surface is a Python API consumed by sibling children (#361.2 for emission, #361.3 for the work loop). SDD-C-023 (filter/payload positive-path assertion) does not apply — no HTTP filter/payload-transform logic. SDD-C-024 (finding-to-test translation) is applicable; any pre-PR finding on the core module MUST be translated into a failing automated test before the fix is authored.

## Implementation Stack Profile (Normative)
- Backend stack profile: python_plus_fastapi_pydantic_v2
- Frontend stack profile: none
- Test automation profile: pytest_vitest_playwright_pact
- Agent execution model: specialized-subagents-isolated-worktrees
- Managed service preference: stackit-managed-first
- Managed service exception rationale: none
- Runtime profile: local-first-docker-desktop-kubernetes
- Local Kubernetes context policy: docker-desktop-preferred
- Local provisioning stack: crossplane-plus-helm
- Runtime identity baseline: eso-plus-argocd-plus-keycloak
- Local-first exception rationale: This child ships a pure-Python importable module (`scripts/lib/factory/orchestrator/core/`) with zero runtime I/O. There is no local-cluster lane to configure at this layer; the module is exercised exclusively via pytest in-process. Container packaging and local-cluster smoke are scoped to #361.4 (Helm chart) and a follow-up once #335 + #336 ship.
- Has user-facing flow: false <!-- inferred from intake: no UI/flow keywords, labels, or frontend-framework references in issue #373 or its parent scope — confirm before SPEC_READY -->
- E2E gate classification: N/A

## Objective
- Business outcome: Ship the **pure-Python core of the orchestrator** — the four importable domain/application-layer components (dispatch matrix loader, convergence engine, schema validator, predicate-registry mechanism) that every other orchestrator child (#361.2, #361.3, #361.4) depends on. These components have zero I/O and are the critical-path deliverable that unblocks the entire `#361` decomposition.
- Success metric: `uv run python3 -m pytest tests/factory/orchestrator/core/` passes with 0 failures covering T-101 (dispatch matrix loader), T-102 (convergence engine all three modes), T-103 (schema validator), and T-104 (predicate registry); `make quality-sdd-check` passes on the implementation branch.

## Normative Requirements

### Functional Requirements (Normative)

- FR-001 The dispatch matrix loader MUST read `docs/blueprint/autonomous-factory/design-contracts.md` § Contract C3 at call time and parse it into a typed in-memory mapping `step → MatrixRow` where `MatrixRow` conforms to the `DispatchTableRow` JSON Schema defined in `docs/blueprint/architecture/decisions/ADR-issue-364-expert-persona-model.md` § 4.1. The loader MUST validate at parse time that: (a) every `skill` value in the matrix resolves to a directory under `.agents/skills/`; (b) every `expert_slug` value in `expert_panel[]` satisfies EXACTLY ONE OF — presence in the sealed `expert_slug_blueprint` enum from design-contracts § C7 F-12, OR presence in the consumer-overlay `expert_slug_extension` allowlist supplied by the caller as a `frozenset[str]` parameter (empty frozenset is the default; callers that have no consumer overlay MUST pass the empty frozenset, not omit the parameter); (c) every `predicate` value that is not the literal string `"none"` resolves to a registered name in the `PredicateRegistry` supplied by the caller. The loader MUST raise `DispatchMatrixError` and MUST NOT return a partial result if any validation check fails. The returned mapping MUST cover the 8 SDD steps `step01..step08`; the step-set MUST be derived by parsing the matrix rows, NOT asserted as a literal integer constant.
- FR-002 The convergence engine MUST implement the three convergence modes defined in `docs/blueprint/architecture/decisions/ADR-issue-364-expert-persona-model.md` § 5: (a) `parallel-then-merge` — accept a list of `ExpertVerdict` objects, apply precedence `block > revise > pass` to derive aggregate verdict, apply naive string-equality deduplication across all `finding_text` values, and return a `MergeResult(aggregate_verdict, findings_before_dedup, findings_after_dedup, severity_escalation_events)`; (b) `sequential-lens` — accept an ordered list of expert invocation callables and a shared mutable `LensDelta` context, invoke each callable in the declared order passing the prior callable's delta as an additional input, and return the final `LensDelta`; (c) `structured-disagreement` — accept a list of `ExpertVerdict` objects, detect cross-lens contradictions where two or more verdicts conflict on the same `finding_category`, and return a `StructuredDisagreementResult(verdicts, severity_escalation_events)` where `severity_escalation_events` counts the number of detected cross-verdict category conflicts. The convergence engine MUST perform zero I/O.
- FR-003 The schema validator MUST accept a raw skill-output payload (dict) and a skill basename string, locate the skill's `SKILL.md` at `.agents/skills/<skill-basename>/SKILL.md`, extract the YAML content from the `## Required Output Schema` fenced block (`` ```yaml jsonschema ``), compile it as a JSON Schema draft-07 document, and validate the payload against it using `jsonschema`. On validation failure the validator MUST raise `SchemaValidationError` with the normalized field path and raw validator error message in its structured fields, and MUST return a typed `ValidationFailure(skill=<skill-basename>, evidence_ref=<opaque pointer string>, error_message=<raw validator error>)`. On validation success the validator MUST return `ValidationSuccess(skill=<skill-basename>)`. The validator MUST perform zero I/O beyond the single `SKILL.md` read at validation time; it MUST NOT write to any stream, emit any event, or call any external service.
- FR-004 The predicate registry MUST provide a typed `PredicateRegistry` with `register(name: str, fn: Callable[[WorkItemContext], bool]) -> None` and `evaluate(name: str, ctx: WorkItemContext) -> bool` methods. `WorkItemContext` MUST carry at minimum `changed_paths: list[str]` and `has_user_facing_flow: bool`. The registry MUST ship two built-in fixture predicates registered at construction time: `"always_true"` (returns `True` for all contexts) and `"always_false"` (returns `False` for all contexts). `evaluate` MUST raise `PredicateRegistryError` when `name` is not registered. `MatrixRow.predicate` MUST be typed as `str | None` in Pydantic v2; the literal string `"none"` MUST be coerced to Python `None` by a Pydantic field validator at parse time; any non-`"none"` string MUST be treated as a registry name and MUST be validated against the supplied `PredicateRegistry` at matrix-load time (FR-001 clause (c)) — validation MUST NOT be deferred to dispatch time.

### Non-Functional Requirements (Normative)

- NFR-SEC-001 The module MUST NOT access credentials, environment variables with secret semantics, or any external network service. File reads are restricted to EXACTLY TWO categories: (1) `docs/blueprint/autonomous-factory/design-contracts.md` for the dispatch matrix, (2) `.agents/skills/*/SKILL.md` files for schema extraction. No other file path categories are permitted from within the module. Any caller wishing to override paths MUST supply them as constructor parameters — the module MUST NOT read from process environment to determine file paths.
- NFR-OBS-001 The module MUST expose structured exception types (`DispatchMatrixError`, `SchemaValidationError`, `PredicateRegistryError`, `ConvergenceError`) each carrying at minimum a `detail: str` field and a `context: dict` field sufficient for the caller (#361.2) to emit a structured log line per parent NFR-OBS-001. The module MUST NOT write to stdout, stderr, or any log sink — all observable signals are surfaced exclusively via exceptions and return types. This constraint makes the module trivially unit-testable without output capture and ensures the caller owns all observability decisions.
- NFR-REL-001 The dispatch matrix loader MUST validate the complete matrix before returning any result — partial matrix loads are forbidden and MUST be rejected with `DispatchMatrixError`. The schema validator MUST be idempotent: invoking it twice on the same `(payload, skill)` pair MUST return the same result. The predicate registry MUST be immutable after the first `evaluate` call is made; calling `register` after `evaluate` MUST raise `PredicateRegistryError` with a frozen-registry message.
- NFR-OPS-001 `DispatchMatrixError` MUST include the failing row's `step` identifier and the failing value (skill basename or expert slug) so the caller can produce a diagnostic that routes to operator runbook action. `SchemaValidationError` MUST include the failing `field_path` (JSON pointer string) and `raw_error` (validator error message string). `PredicateRegistryError` MUST include the unresolved `predicate_name` and the list of currently registered names.
- NFR-A11Y-001 N/A — this module is a headless pure-Python library with no UI surface. Operator-facing observability is delegated to the caller (#361.2 and #361.3) and downstream Grafana dashboards authored by #350.

## Normative Option Decision
- Option A: Dict-based in-process `PredicateRegistry` — predicates registered by name string as callables against a typed `WorkItemContext`; registry validated at matrix-load time via FR-001 clause (c).
- Option B: `importlib.metadata` entry-point registry — consumer predicates registered as Python package entry points; lookup at matrix-load time queries the installed package's entry-point group.
- Selected option: OPTION_A
- Rationale: The predicate registry in this child ships only fixture predicates (`always_true`, `always_false`); the first real predicate (`ui-fidelity-or-a11y`) ships in #361.5 and can be registered programmatically using the same `register` API. Entry-point registration adds dependency on package distribution machinery that is premature at v1 scale and introduces a test-isolation problem (installed entry points are global state). Option A is extensible without API change: #361.5 calls `registry.register("ui-fidelity-or-a11y", fn)` before passing the registry to the loader.

## Contract Changes (Normative)
- Config/Env contract: None — the module reads only two file-path categories (design-contracts.md and SKILL.md files); it consumes no environment variables or Kubernetes secrets.
- API contract: Python module API exported from `scripts/lib/factory/orchestrator/core/__init__.py`: `DispatchMatrixLoader`, `ConvergenceEngine`, `SchemaValidator`, `PredicateRegistry`, `WorkItemContext`, `MatrixRow`, `ExpertVerdict`, `MergeResult`, `ValidationFailure`, `ValidationSuccess`, `DispatchMatrixError`, `SchemaValidationError`, `PredicateRegistryError`, `ConvergenceError`.
- OpenAPI / Pact contract path: none
- Event contract: None — this child emits no C7 events. The C7 emission path for schema-validation failures (rejected events) is #361.2 scope.
- Make/CLI contract: No new Make targets. The module is exercised via `uv run python3 -m pytest tests/factory/orchestrator/core/`.
- Docs contract: `docs/blueprint/autonomous-factory/design-contracts.md` § C3 is consumed read-only; no changes are authored in this child. The orchestrator runtime documentation at `docs/blueprint/autonomous-factory/orchestrator.md` (new file) is scoped to #361.3 per the parent spec.

## Blueprint Upstream Defect Escalation (Normative)
- Upstream issue URL: none
- Temporary workaround path: none
- Replacement trigger: none
- Workaround review date: none

## Normative Acceptance Criteria

- AC-001 [Dispatch matrix loader reads § C3 and rejects unknown skills and experts at load time, accepting consumer-overlay extension slugs] — verified by T-101, which MUST assert: (a) `DispatchMatrixLoader.load(design_contracts_path, skills_dir, extension_allowlist=frozenset(), registry=registry)` raises `DispatchMatrixError` when invoked against a fixture `design-contracts.md` containing a row with a fabricated skill basename absent from the fixture `.agents/skills/` directory; (b) the loader raises `DispatchMatrixError` when invoked against a fixture containing a fabricated `expert_slug_blueprint` value absent from the sealed baseline enum AND also absent from the `extension_allowlist` (fixture: empty frozenset); (c) the loader accepts an expert slug that appears in the `extension_allowlist` even when it is absent from `expert_slug_blueprint`, returning a valid dispatch table without raising; (d) the loader returns a typed mapping whose key-set equals EXACTLY `{"step01","step02","step03","step04","step05","step06","step07","step08"}` when invoked against the canonical `docs/blueprint/autonomous-factory/design-contracts.md` § C3, with the step-set derived by parsing the matrix rows (the assertion MUST NOT use `len(result) == 8` — it MUST assert `result.keys() == expected_steps` where `expected_steps` is constructed from the parsed row keys).
- AC-002 [Three convergence modes produce the documented merger outputs] — verified by T-102, which MUST assert: (a) `ConvergenceEngine.parallel_then_merge([pass_verdict, revise_verdict, block_verdict, pass_verdict])` returns a `MergeResult` with `aggregate_verdict == "block"`, `findings_before_dedup == 4`, and `findings_after_dedup` equal to the count of findings remaining after naive string-equality deduplication across all four verdict objects; (b) `ConvergenceEngine.sequential_lens(experts=[e1, e2, e3, e4, e5], initial_context=fixture_context)` invokes each callable in order and passes each callable's returned `LensDelta` as an additional input parameter to the next callable — asserted by a spy that records invocation order and input deltas; (c) `ConvergenceEngine.structured_disagreement([block_verdict_cat_A, block_verdict_cat_A_conflict])` where both verdicts carry `finding_category == "schema"` but conflicting `verdict` values returns a `StructuredDisagreementResult` with `severity_escalation_events >= 1`.
- AC-003 [Schema validator raises SchemaValidationError and returns ValidationFailure without performing any I/O] — verified by T-103, which MUST assert that a fixture skill output dict missing a required field declared in that skill's `## Required Output Schema` fenced block causes: (a) the validator to raise `SchemaValidationError` with a non-empty `detail` field containing the missing field name; (b) the validator to return a `ValidationFailure` object with a non-empty `error_message` and a non-empty `evidence_ref` string; (c) no write is made to stdout, stderr, or any file — asserted by patching `builtins.open` in write mode and `sys.stdout.write` and `sys.stderr.write` to assert they are never called during validation.
- AC-004 [Predicate registry evaluates fixture predicates correctly and MatrixRow.predicate "none" parses to Python None] — verified by T-104, which MUST assert: (a) a freshly constructed `PredicateRegistry` with `evaluate("always_true", WorkItemContext(changed_paths=[], has_user_facing_flow=False))` returns `True`; (b) `evaluate("always_false", WorkItemContext(...))` returns `False`; (c) `MatrixRow(predicate="none", ...)` has `predicate == None` after Pydantic v2 construction (the literal string `"none"` is coerced to Python `None` by the field validator); (d) `DispatchMatrixLoader.load(...)` invoked against a fixture matrix containing a row with `predicate="always_true"` and a registry that has `always_true` registered returns a valid dispatch table without raising; (e) `DispatchMatrixLoader.load(...)` invoked against a fixture matrix containing a row with `predicate="unregistered_sentinel"` and a registry that does NOT have `unregistered_sentinel` registered raises `DispatchMatrixError` at load time (asserted by checking the exception type is `DispatchMatrixError`, not `PredicateRegistryError` — the loader wraps registry misses as matrix errors to give the caller a single error type for startup validation).

## Informative Notes (Non-Normative)
- Context: This child (`#361.1`) is the pure-Python core of the orchestrator service (`#361`, Child B of `#333`). It is deliberately zero-I/O so that every component can be unit-tested without mocks or stubs of infrastructure. The C7 emission path for rejected skill outputs (FR-004 in parent spec) belongs to `#361.2` — this child's schema validator returns a typed `ValidationFailure`; the caller (#361.2) decides whether and how to emit a C7 rejected event. The dependency direction is `#361.5 → #361.1`, not the reverse: this child authors only fixture predicates; the first real predicate (`ui-fidelity-or-a11y`) is authored in `#361.5` which calls `registry.register(...)` before passing the registry to the loader.
- Tradeoffs: The zero-I/O constraint on this child maximises unit-test coverage speed and eliminates the need for any infrastructure stub at the domain/application layer. The cost is that the caller (#361.2) must wire observability. This mirrors Clean Architecture's dependency rule: inner layers know nothing about outer layers.
- Clarifications: All four open questions from the parent spec (Q-1 through Q-4) are resolved and do not generate open questions for this child. The predicate evaluation surface (Q-3, resolved as Option A OR-form) is implemented here only at the registry-mechanism level; the two consumer-extensible regex sets (`predicates.frontend.pathRegex`, `predicates.accessibility.pathRegex`) belong to the config-map in `#361.4` and the actual `ui-fidelity-or-a11y` callable in `#361.5`.

## Explicit Exclusions
- Excluded item 1: C7 event emission — entirely owned by `#361.2`. This child returns typed result objects; the caller handles emission.
- Excluded item 2: RabbitMQ subscriber and OpenHands API client — owned by `#361.3`.
- Excluded item 3: Helm chart, NetworkPolicy, ESO, ServiceAccount — owned by `#361.4`.
- Excluded item 4: `usability-pragmatist` PERSONA.md and the `ui-fidelity-or-a11y` predicate implementation — owned by `#361.5`.
- Excluded item 5: Embedding-based finding-text deduplication — explicitly deferred per ADR-issue-364 § 11; v1 uses naive string-equality dedup.
- Excluded item 6: Per-expert prompt-cache discipline — deferred per backlog `proposal(issue-368-factory-cost-telemetry-routing-fixture): per-expert prompt-cache efficiency`; needs token-usage baseline first.

## Potential Deferred Proposals
- Embedding-based convergence deduplication: ADR-issue-364 § 11 explicitly defers this; v1 ships naive string-equality. Surface when bigram-match false-positive rate on real step02 traffic is quantified by the `proposal(issue-368-factory-cost-telemetry-routing-fixture): embedding-based router implementation` backlog trigger.
- `importlib.metadata` entry-point predicate registry: deferred in favour of the dict-based registry (Option A above). Surface if consumer teams request a packaging-native registration path for predicates.
- Consumer-extensible path-regex in predicate evaluation: the two regex sets (`predicates.frontend.pathRegex`, `predicates.accessibility.pathRegex`) are scoped to the orchestrator config-map in `#361.4`; this child ships only the `WorkItemContext.changed_paths` field and the registry mechanism.
- `MatrixRow.predicate` compound object (named + parameters): v1 ships string-name-only predicate references. If predicates need parameters (e.g., `{ name: "path-regex", args: { pattern: "^src/.*" } }`), the schema can be widened in a follow-up without breaking the string-name form.
