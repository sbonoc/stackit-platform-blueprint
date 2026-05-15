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
- ADR path: docs/blueprint/architecture/decisions/ADR-issue-293-294-agents-north-star-cross-reference.md
- ADR status: proposed
- SPEC_READY_EXCEPTION: none
- authorized-by: none

## Applicable Guardrail Controls (Normative)
- Applicable control IDs: SDD-C-001, SDD-C-002, SDD-C-003, SDD-C-004, SDD-C-005, SDD-C-006, SDD-C-007, SDD-C-008, SDD-C-011, SDD-C-012, SDD-C-016, SDD-C-017, SDD-C-019, SDD-C-020, SDD-C-021
- Control exception rationale: SDD-C-009 not applicable — no authn/authz or secret-handling paths. SDD-C-010 not applicable — script output is exit code + stdout violations; no metrics/traces owned by this tooling. SDD-C-013 not applicable — tooling-only; no STACKIT managed service. SDD-C-014 not applicable — no runtime changes. SDD-C-015 not applicable — no app delivery workflow impact. SDD-C-018 not applicable — no blueprint-managed defect workaround. SDD-C-022 not applicable — no HTTP routes. SDD-C-023 not applicable — no filter/transform logic. SDD-C-024 not applicable — tooling-only; no pre-PR smoke failures.

## Implementation Stack Profile (Normative)
- Backend stack profile: none
- Frontend stack profile: none
- Test automation profile: pytest
- Agent execution model: single-agent
- Managed service preference: explicit-consumer-exception
- Managed service exception rationale: quality tooling only; no STACKIT managed service involved
- Runtime profile: local-first-docker-desktop-kubernetes
- Local Kubernetes context policy: docker-desktop-preferred
- Local provisioning stack: crossplane-plus-helm
- Runtime identity baseline: custom-approved-exception
- Local-first exception rationale: no runtime changes; quality tooling only

## Objective
- Business outcome: Eliminate the recurring pattern of AGENTS.md ↔ north_star.md content duplication in consumer repos. The dhe-marketplace consumer demonstrates the failure mode: cross-cutting architecture invariants (e.g. OpenMetadata section) were inlined in AGENTS.md across multiple spec sessions because AGENTS.md is auto-loaded by agents, creating silent drift with north_star.md. This work item: (1) updates the consumer init template so every new consumer starts with an explicit "Architecture Invariants — Pointers" section that makes the single-source-of-truth contract visible from day one; and (2) adds a programmatic quality hook that catches heading duplication before it reaches review.
- Success metric: (1) New consumer repos initialized from the updated template contain an "Architecture Invariants — Pointers" section with anti-duplication instruction. (2) `quality-docs-cross-reference-check` exits 1 and reports the duplicate heading when AGENTS.md contains a heading identical to a north_star.md heading outside the Pointers table. (3) Clean consumer repos (no duplication) and repos with allowlisted exceptions pass the check with exit 0.

## Normative Requirements

### Functional Requirements (Normative)
- FR-001 `scripts/templates/consumer/init/AGENTS.md.tmpl` MUST include a new "Architecture Invariants — Pointers" section containing: (a) an explicit anti-duplication statement that AGENTS.md does NOT duplicate architecture content; (b) a placeholder pointers table mapping domain names to their canonical source in `north_star.md` (by section reference) and the associated ADR; (c) an instruction that new cross-cutting concerns MUST be recorded in `north_star.md` and the appropriate ADR, never inlined in AGENTS.md.
- FR-002 `scripts/templates/consumer/init/AGENTS.md.tmpl` Mandatory Workflow MUST include a new rule that before any SDD work item touching a domain covered in `docs/platform/architecture/north_star.md`, the agent MUST read the relevant `north_star.md` section and the canonical ADR(s) cited in the Pointers table. AGENTS.md MUST NOT duplicate architecture content present in `north_star.md`.
- FR-003 A new script `scripts/bin/quality/check_docs_cross_reference.py` MUST be created. It MUST parse `docs/platform/architecture/north_star.md` (consumer path) or `docs/blueprint/architecture/north_star.md` (blueprint path, used as fallback) section headings at `##` and `###` levels, and parse `AGENTS.md` section headings. It MUST report a named violation for each AGENTS.md heading that exactly matches (case-insensitive, whitespace-normalized) a north_star.md heading, UNLESS that heading appears verbatim in the "Architecture Invariants — Pointers" table in AGENTS.md.
- FR-004 `check_docs_cross_reference.py` MUST support a per-consumer allowlist file `.quality-docs-cross-reference-allowlist.yml`. Each allowlist entry MUST include a `justification` field with non-empty text. Headings listed in the allowlist MUST NOT generate violations.
- FR-005 A make target `quality-docs-cross-reference-check` MUST be added to `make/blueprint.generated.mk`. The target MUST invoke `check_docs_cross_reference.py` and be wired into `scripts/bin/quality/hooks_fast.sh` in the `quality-docs-check-changed` group alongside the existing `quality-docs-check-changed` invocation.
- FR-006 `check_docs_cross_reference.py` MUST exit 0 when no violations are found and exit 1 when at least one violation is detected. Violation output format MUST use a `[quality-docs-cross-reference-check]` prefix consistent with existing `check_*.py` scripts.

### Non-Functional Requirements (Normative)
- NFR-PERF-001 `check_docs_cross_reference.py` MUST complete in under 2 seconds on a consumer repository. The script MUST NOT invoke external processes or make network calls; markdown parsing MUST use only Python stdlib.
- NFR-MAINT-001 The "Architecture Invariants — Pointers" table in `AGENTS.md.tmpl` MUST include at least one placeholder domain row with a reference to a `north_star.md` section and an ADR column. A comment MUST instruct consumers to extend the table one row per cross-cutting concern.
- NFR-COMPAT-001 `check_docs_cross_reference.py` MUST exit 0 (no violation, no error) when `AGENTS.md` or the resolved `north_star.md` path is absent. The check MUST be a no-op for consumers that have not yet structured these files.
- NFR-A11Y-001 N/A — no UI or frontend changes.

## Normative Option Decision
- Option A: Exact normalized heading match — extract `##`/`###` headings from both files, normalize (lowercase + collapse whitespace), check for set intersection excluding Pointers-table entries. Simple, deterministic, no false positives from body content.
- Option B: Section-heading + body heuristic — additionally scan body lines of matched sections for shared MUST/MUST-NOT clauses or identical bullet text. Catches paraphrased duplication; higher implementation complexity and false-positive risk.
- Selected option: OPTION_A
- Rationale: Issue #294 explicitly recommends starting simple. Option A catches the primary failure mode (same heading = same topic inlined twice) with deterministic output. Option B is parked as a future iteration once Option A is stable and consumer feedback is gathered.

## Contract Changes (Normative)
- Config/Env contract: none
- API contract: none
- OpenAPI / Pact contract path: none
- Event contract: none
- Make/CLI contract: adds `quality-docs-cross-reference-check` make target to `make/blueprint.generated.mk`; wires into `quality-hooks-fast` via `hooks_fast.sh`
- Docs contract: `scripts/templates/consumer/init/AGENTS.md.tmpl` gains "Architecture Invariants — Pointers" section and a new Mandatory Workflow rule

## Blueprint Upstream Defect Escalation (Normative)
- Upstream issue URL: none
- Temporary workaround path: none
- Replacement trigger: none
- Workaround review date: none

## Normative Acceptance Criteria
- AC-001 `AGENTS.md.tmpl` contains an "Architecture Invariants — Pointers" section with: (a) explicit anti-duplication statement, (b) a pointers table with at least one example domain row (domain name → `north_star.md` section reference → ADR reference), and (c) instruction that new cross-cutting concerns MUST go to `north_star.md` and the appropriate ADR.
- AC-002 `AGENTS.md.tmpl` Mandatory Workflow contains a new rule (numbered, after the existing rules) requiring the agent to read the relevant `north_star.md` section and canonical ADR(s) before any SDD work item touching a domain covered in `north_star.md`, and explicitly prohibiting architecture content duplication in AGENTS.md.
- AC-003 `check_docs_cross_reference.py` exits 1 and emits a violation message when `AGENTS.md` contains a `##` or `###` heading that exactly matches (case-insensitive, whitespace-normalized) a `north_star.md` heading and the heading is not in the Pointers table and not in an allowlist file.
- AC-004 `check_docs_cross_reference.py` exits 0 when the matching heading appears in the "Architecture Invariants — Pointers" table in `AGENTS.md` (recognized as a sanctioned navigation pointer, not duplication).
- AC-005 `check_docs_cross_reference.py` exits 0 when the matching heading is listed in `.quality-docs-cross-reference-allowlist.yml` with a non-empty `justification` value.
- AC-006 `quality-docs-cross-reference-check` make target exists; `make quality-hooks-fast` triggers the check.
- AC-007 Unit test suite covers: clean files → exit 0; heading match without allowlist → exit 1 with violation message; heading in Pointers table → exit 0; heading in allowlist file → exit 0; missing allowlist file → exit 0; absent `AGENTS.md` → exit 0 (graceful skip); absent `north_star.md` → exit 0 (graceful skip).

## Informative Notes (Non-Normative)
- Context: dhe-marketplace consumer commit `9586424` is the reference implementation. Its restructured AGENTS.md (process-and-governance only, with a Pointers table) and `north_star.md` (all domain invariants) define the target state this work item encodes as a template and enforces with the hook.
- Tradeoffs: The Pointers table allowlist (FR-003) is a precision instrument — it only suppresses violations for headings that appear verbatim as Pointers-table entries, not arbitrary substring matches. This means the Pointers table heading text and the north_star.md heading text MUST match exactly for the exemption to apply. Consumers that paraphrase their pointer rows will still get flagged; this is intentional — the exact heading text from north_star.md is the required pointer key.
- Existing consumers: AGENTS.md is consumer-owned post-init and is NOT auto-updated on blueprint upgrade. Existing consumers see the new hook on upgrade; clean consumers pass; consumers with duplication see violations and fix manually.
- Option B deferred: body-heuristic detection is parked as a backlog proposal (on-scope: quality) for a future iteration.

## Explicit Exclusions
- Existing consumer AGENTS.md files are NOT auto-updated; the template change applies to new consumers only.
- Content-body heuristic detection (Option B) is explicitly out of scope for this work item.
- The hook does NOT check `docs/blueprint/architecture/north_star.md` against the blueprint's own AGENTS.md headings (only the consumer path `docs/platform/architecture/north_star.md` is the primary target; blueprint fallback is for development convenience when running the hook inside the blueprint repo itself).
