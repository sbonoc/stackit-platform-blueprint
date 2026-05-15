# Architecture

## Context
- Work item: 2026-05-15-issue-293-294-agents-north-star-cross-reference
- Owner: sbonoc
- Date: 2026-05-15

## Stack and Execution Model
- Backend stack profile: none (pure Python tooling, no app stack)
- Frontend stack profile: none
- Test automation profile: pytest (unit tests only)
- Agent execution model: single-agent

## Problem Statement
- What needs to change and why: Consumer repos drift silently because AGENTS.md is auto-loaded by agents and becomes a magnet for architecture content that should live in north_star.md. The template provides no structural contract and no automated enforcement. The dhe-marketplace consumer had to correct this manually after multiple sessions of accumulation.
- Scope boundaries: (1) Consumer init template `AGENTS.md.tmpl` — structural section + Mandatory Workflow rule. (2) New quality script `check_docs_cross_reference.py` — heading-overlap detection. (3) Make target + hooks_fast.sh wiring. No changes to existing consumer repos, no changes to contract.yaml.
- Out of scope: Auto-update of existing consumer AGENTS.md files. Body-heuristic content detection (Option B). Blueprint's own AGENTS.md structural changes.

## Bounded Contexts and Responsibilities

- **Template governance context** (`scripts/templates/consumer/init/AGENTS.md.tmpl`): Defines the structural contract for new consumers. Adds the Pointers section (navigation aid + anti-duplication rule), the north_star.md MUST-read Mandatory Workflow rule (FR-002), and the AGENTS.decisions.md scan Mandatory Workflow rule (FR-008). This is a one-time init artifact; existing consumers are not affected.

- **Blueprint governance context** (`AGENTS.md` — blueprint root): Closes the auto-loading gap in the blueprint repo itself. Adds the same north_star.md MUST-read Mandatory Workflow rule (FR-007) and the AGENTS.decisions.md scan Mandatory Workflow rule (FR-009). Textual change only — no programmatic enforcement is added because the heading-overlap hook targets consumer repos.

- **Quality enforcement context** (`scripts/bin/quality/check_docs_cross_reference.py`): Stateless check — reads two markdown files, extracts headings, computes set intersection minus exemptions, emits violations. Runs in consumer repo context (hooks_fast.sh) and in blueprint repo context (development). No persistent state, no external I/O.

## High-Level Component Design

- Domain layer: Heading normalization function (`_normalize_heading`) — lowercase + collapse whitespace. Heading extraction function (`_extract_headings`) — parse `##`/`###` lines from markdown. Pointers-table extraction function (`_extract_pointer_headings`) — parse AGENTS.md "Architecture Invariants — Pointers" table to get exempted headings. Allowlist loader (`_load_allowlist`) — parse `.quality-docs-cross-reference-allowlist.yml`, validate `justification` fields.
- Application layer: `main()` — resolve file paths, invoke domain functions, compute violation set, emit output, return exit code.
- Infrastructure adapters: Python stdlib only (`pathlib`, `re`, `sys`, `yaml` via stdlib or PyYAML for allowlist parsing — actually to avoid a new dependency, use the existing PyYAML already present in pyproject.toml).
- Presentation/API/workflow boundaries: stdout violation messages with `[quality-docs-cross-reference-check]` prefix; exit code 0/1.

## Integration and Dependency Edges

- Upstream dependencies: `AGENTS.md` (consumer-owned root file), `docs/platform/architecture/north_star.md` (consumer-owned, blueprint seed), `.quality-docs-cross-reference-allowlist.yml` (optional, consumer-owned).
- Downstream consumers: `hooks_fast.sh` invokes the make target; `quality-docs-check-changed` group in hooks_fast.sh. The script is also propagated to consumer repos via the blueprint bootstrap template path (`scripts/templates/blueprint/bootstrap/scripts/bin/quality/`).
- Blueprint template propagation: `scripts/bin/quality/check_docs_cross_reference.py` is blueprint-managed and propagated to consumers on upgrade via the existing drift-check mechanism.

## Mermaid Diagrams

### Detection Flow

```mermaid
flowchart TD
    A[hooks_fast.sh: quality-docs-check-changed group] --> B[make quality-docs-cross-reference-check]
    B --> C[check_docs_cross_reference.py]
    C --> D{AGENTS.md exists?}
    D -- no --> Z[exit 0: no-op]
    D -- yes --> E{north_star.md exists?}
    E -- no --> Z
    E -- yes --> F[extract ##/### headings from north_star.md]
    F --> G[extract ##/### headings from AGENTS.md]
    G --> H[extract Pointers-table heading entries from AGENTS.md]
    H --> I{load allowlist file?}
    I -- file absent --> J[allowlist = empty]
    I -- file present --> K[parse YAML, validate justification fields]
    K --> J
    J --> L[compute: AGENTS headings ∩ north_star headings]
    L --> M[subtract: Pointers-table entries + allowlist entries]
    M --> N{violations?}
    N -- none --> Z
    N -- yes --> O[emit: [quality-docs-cross-reference-check] violation per heading]
    O --> P[exit 1]
```

One diagram sufficient — the detection flow covers the full control path.

## ADR Reference

`docs/blueprint/architecture/decisions/ADR-issue-293-294-agents-north-star-cross-reference.md`
Status: proposed

## Risks and Mitigations

- **Risk 1**: Consumers with existing heading overlap see hook failures on blueprint upgrade. Mitigation: the allowlist mechanism provides a structured escape hatch with required justification; upgrade docs should note the new hook.
- **Risk 2**: The Pointers-table exemption requires exact heading text match between the table row and the north_star.md heading. Consumers who paraphrase their table rows will be incorrectly flagged. Mitigation: template instructions and ADR clearly state that Pointers-table domain names MUST match the north_star.md heading text exactly.
- **Risk 3**: PyYAML is used for allowlist parsing. PyYAML is already a declared dependency in `pyproject.toml`; no new dependency introduced.
- **Risk 4**: Blueprint's own `AGENTS.md` accumulates Mandatory Workflow rules over time. Adding FR-007 and FR-009 increases the rule count; if the list grows too long it becomes difficult for agents to process. Mitigation: rules are brief, distinct, and additive; no existing rule is modified. Future refactoring of AGENTS.md structure is a separate concern.
- **Risk 5**: AGENTS.decisions.md scan rule (FR-008, FR-009) instructs agents to scan for scope-intersecting decisions but does not define a programmatic enforcement path. An agent that ignores the rule produces no hook failure. Mitigation: the instruction is clear and normative; programmatic enforcement of AGENTS.decisions.md scan compliance is deferred as a future iteration (would require LLM-in-the-loop enforcement, out of scope).
