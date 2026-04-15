# Architecture Decisions (ADR)

This directory stores finalized architecture decisions for blueprint-maintainer work.

## Purpose

- `specs/*/architecture.md` captures exploration and option analysis.
- ADRs capture the finalized decision after clarification/sign-off.
- Accepted ADRs become long-lived architectural guidance and should stay aligned with `blueprint/contract.yaml` and governance docs.

## Recommended Naming

- `ADR-<YYYYMMDD>-<slug>.md`

## Minimum ADR Content

- Business/requirement summary (functional + non-functional drivers)
- Decision options (recommended + rejected) with rationale
- Affected capabilities and architecture components
- Architecture diagram (Mermaid)
- High-level work packages and timeline (Mermaid Gantt)
- External dependencies and risk notes

## Source Template

- `.spec-kit/templates/blueprint/adr.md`
