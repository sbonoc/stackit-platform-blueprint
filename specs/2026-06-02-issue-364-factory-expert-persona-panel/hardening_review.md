# Hardening Review

> **Note:** Hardening review is populated at step07 (`make quality-hardening-review`).
> At intake (step01) only the Proposals Only section is pre-seeded with the
> deferred items captured during architectural debate.

## Repository-Wide Findings Fixed
- Finding 1: populated at step07

## Observability and Diagnostics Changes
- Metrics/logging/tracing updates: none directly in this PR; the additive C7 `outcome.details.expert_verdicts[]` field becomes queryable post-merge (e.g., "show everything Boundary Hawk blocked in the last 30 days"). Implementation of the emission lands under #361.
- Operational diagnostics updates: none in this PR.

## Architecture and Code Quality Compliance
- SOLID / Clean Architecture / Clean Code / DDD checks: this PR is specs + ADR + persona files + governance — no runtime code touched. Architectural separation between SDD-step / skill / expert layers is enforced by the new ADR-issue-364 and design-contracts § C3.
- Test-automation and pyramid checks: no runtime code; structural assertions only (grep / file-existence / ADR-text substrings). Documented in `pr_context.md` Validation Evidence at step07.
- Documentation/diagram/CI/skill consistency checks: covered by `make quality-sdd-check`, `make quality-hooks-fast`, `make quality-hooks-slow`, `make docs-build`, `make docs-smoke`, `make quality-hardening-review` at step07.

## Accessibility Gate (Normative — non-UI reviewers mark non-applicable items N/A)
- [N/A] SC 4.1.2 (Name, Role, Value): no user-facing UI — `has-user-facing-flow: false` in spec.md.
- [N/A] SC 2.1.1 (Keyboard): no UI.
- [N/A] SC 2.4.7 (Focus Visible): no UI.
- [N/A] SC 1.4.1 (Use of Color): no UI.
- [N/A] SC 3.3.1 (Error Identification): no UI.
- [N/A] axe-core WCAG 2.1 AA scan evidence: no UI.

## Proposals Only (Not Implemented)
- Proposal 1 — Expert-sprawl ceiling enforcement: ADR §3 (Future Work) pins an 8-expert ceiling and requires any 9th expert to demonstrate distinct push-back triggers that the existing 8 do not cover. No tooling enforces this today; relies on ADR review discipline. Consider a CI check that fails if `.agents/personas/` exceeds 8 directories without an ADR amendment — held; separate ticket if the temptation recurs.
- Proposal 2 — Convergence finding-text dedup quality: default `parallel-then-merge` aggregation ships with priority-order merge (`block > revise > pass`) but naive string-equality finding dedup. Embedding-based semantic dedup is held until naive dedup proves insufficient in #361 implementation.
- Proposal 3 — Per-expert prompt-cache discipline: per-expert LiteLLM routing means each expert hits its own context; cache contamination across experts is a theoretical risk. Held until #361 observability surfaces it.
- Proposal 4 — Expert-verdict-to-skill-output feedback loop: today the panel reviews skill output; no mechanism exists for an expert verdict to amend the skill output in-place. Held until parallel-then-merge proves insufficient.
- Proposal 5 — Optional `make expert-review` for solo-operator local SDD sessions: surfaces the panel review in the local CLI without going through GH-driven orchestration. Held until user demand emerges.
- Proposal 6 — 9th expert: compliance / data-protection-officer lens distinct from data-privacy (compliance frameworks and audit posture rather than data lifecycle). Held; requires distinct push-back triggers per ADR §3.
