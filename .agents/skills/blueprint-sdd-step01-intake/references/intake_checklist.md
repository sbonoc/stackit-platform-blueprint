# SDD Intake Checklist

- Confirm source requirements document(s) path and version.
- Extract atomic requirements as REQ-###, NFR-###, AC-###.
- Use only MUST / MUST NOT / SHALL / EXACTLY ONE OF in normative sections.
- Declare applicable SDD-C-### control IDs in spec.md.
- Populate Implementation Stack Profile (stack, test automation, managed-service, local-first fields).
- Draft architecture.md with bounded-context decisions and integration edges.
- Draft ADR at correct track path; set ADR path in spec.md.
- Choose Mermaid diagram type(s) with one-sentence captions.
- Write plan.md with sequenced delivery slices (red→green TDD order).
- Populate tasks.md with all task rows (all unchecked).
- Generate graph.json nodes and edges for every REQ/NFR/AC.
- Populate traceability.md for every requirement.
- Record all unresolved inputs as [NEEDS CLARIFICATION] structured blocks — not empty sections.
- Run make quality-sdd-check — fix all violations before committing.
- Commit all artifacts; push to dedicated branch.
- Open Draft PR with Open Questions table (if open questions exist).
- Confirm Draft PR URL is posted in the required report.
