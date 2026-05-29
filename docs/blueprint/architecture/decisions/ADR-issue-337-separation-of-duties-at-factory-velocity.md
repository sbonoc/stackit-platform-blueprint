# ADR: Separation of Duties at Factory Velocity

**Status:** approved
**Date:** 2026-05-29
**Issue:** #337
**Spec:** `specs/2026-05-28-issue-337-factory-phase-0-foundations/` (FR-005, NFR-SEC-002)
**Meta-ADR:** [`ADR-issue-337-factory-phase-0-foundations.md`](ADR-issue-337-factory-phase-0-foundations.md)
**Extensibility classification (#339 C8 FR-017):** `sealed`. The rule text is identical for every consumer (the multi-author SoD identical rule is listed explicitly in FR-017(b)). The two satisfaction paths defined below are both blueprint-authored — consumers select a mode via `blueprint/contract.yaml`, they do not vary the rule text. Mode-selection from a fixed blueprint-defined set is not parameterization in the FR-017 sense.

## Context

`AGENTS.md § Sign-off Policy` already requires that the four canonical sign-off phrases (`SPEC_PRODUCT_READY: approved`, `ARCHITECTURE_SIGNOFF: approved`, `SECURITY_SIGNOFF: approved`, `OPERATIONS_SIGNOFF: approved`) be posted verbatim in PR comments by humans, with code assistants forbidden from self-approving. At human velocity, the natural friction of four different humans posting four different phrases makes the multi-author property emergent — nobody has to enforce it because nobody can plausibly impersonate three colleagues at once.

At factory velocity that property is no longer emergent. The factory bot operates a real GitHub identity (#339 Contract C5) that posts PR comments, applies labels, and authors specs. Without an explicit rule, the bot could plausibly produce a spec PR where all four sign-off phrases trace back to a single human reviewer who rubber-stamped four checkboxes in one minute — restoring the bus-factor risk SDD was designed to eliminate. Worse, a substring/regex match on the bot's display name could be spoofed by a tampered fork; only exact-string equality on the GitHub login (which is unforgeable) closes that gap.

## Decision Drivers

- The multi-author guarantee is the load-bearing compliance argument behind every factory-produced spec; if it can be reduced to a single human, the entire SoD posture collapses.
- Identity matching MUST be unforgeable — display names and substrings are spoofable, GitHub logins are not.
- The rule MUST be checkable by the GitHub Actions enforcement layer (#336) in a single pass over the PR comment thread; no out-of-band state required.
- Consumer instances inherit identically; this is one of the rules explicitly enumerated in #339 C8 FR-017(b).

## Decision

**Multi-author SoD rule.** Every factory-produced spec MUST carry **at least two distinct git identities across the four canonical sign-off phrases** (Product, Architecture, Security, Operations). "Distinct" means distinct GitHub login strings (exact-string equality; case-sensitive per GitHub's canonicalization).

**Factory bot suppression.** The factory bot identity declared per #339 Contract C5 is suppressed from the SoD count. Concretely: if the bot's GitHub login appears as the comment author on any of the four sign-off comments, that comment MUST NOT count toward the two-distinct-identity requirement — the spec needs ≥ 2 distinct *non-bot* identities. (In practice the bot posts no sign-off comments; this clause exists to make the suppression rule mechanical rather than relying on bot behaviour.)

**Identity matching rule.** Bot-identity detection MUST use **exact-string equality** on the GitHub login (the `user.login` field on the comment payload). Substring matches, regular-expression matches, display-name matches (`user.name`), and email-domain heuristics are FORBIDDEN. This MUST reference #339 NFR-SEC-001 verbatim (per this spec's NFR-SEC-002): *"factory bot identity detection MUST use exact-string equality on GitHub login; substring/regex/display-name heuristics FORBIDDEN."*

**Enforcement layer.** #336 (GitHub Actions webhooks) reads the four most recent sign-off comments, extracts `user.login` for each, applies the bot-suppression filter, and counts distinct non-bot logins. The pass threshold depends on the satisfaction path selected per `blueprint/contract.yaml` (see § Satisfaction paths below). Cited by #334 (which inherits the same exact-string match for any factory-side bot-identity check it adds).

### Satisfaction paths

> **For #336 implementers.** The SoD rule is classified `sealed` per #339 C8 FR-017(b), but `#336` MUST implement TWO enforcement code paths gated by `blueprint/contract.yaml § spec.spec_driven_development_contract.readiness_gate.sod_policy.solo_operator` (boolean; default `false`). Do not assume a single code path. Path 1 (multi-author, default) gates at ≥ 2 distinct non-bot logins. Path 2 (solo-operator, opt-in per-repo) gates at ≥ 1 non-bot login AND a canonical attestation comment matching every constraint below. Both paths apply the same factory-bot suppression (NFR-SEC-002 / #339 NFR-SEC-001 exact-string equality on `user.login` — substring/regex/display-name heuristics FORBIDDEN). The mode-selection is not parameterization in the FR-017 sense; consumers select from a fixed blueprint-defined path-set, they do not vary the rule text.

The multi-author rule above is the blueprint default. Real consumer installations include solo-operator topologies (single-maintainer repositories, two-repo personal projects, early-stage initiatives) where a strict two-distinct-identity floor is unsatisfiable. To prevent solo operators from being forced to either fake reviewers or disable the factory entirely, the blueprint defines EXACTLY TWO satisfaction paths. Consumers select which path applies via `blueprint/contract.yaml § spec.spec_driven_development_contract.readiness_gate.sod_policy.solo_operator` (boolean; default `false`).

**Path 1 — Multi-author (default; `solo_operator: false`).** As specified above: ≥ 2 distinct non-bot GitHub logins across the four canonical sign-off comments, with factory bot suppression by exact-`user.login` equality.

**Path 2 — Solo-operator (`solo_operator: true`).** Exactly one distinct non-bot GitHub login may post all four sign-off phrases, IF AND ONLY IF the same login also posts a single canonical attestation comment on the PR that satisfies all of the following:

- The comment body MUST contain the literal marker string `SOLO_OPERATOR_ATTESTATION: confirmed` on its own line.
- The comment body MUST contain all five checklist items below as Markdown task-list lines, each checked (`- [x]`); any unchecked item (`- [ ]`) MUST cause the gate to reject the spec.
- The comment author MUST be a non-bot login (factory bot suppression unchanged).
- The comment author MUST be a member of at least one gate-1 CODEOWNERS team for the paths the PR touches (per FR-011 routing).
- The comment MUST be posted after the last code commit in the PR (timestamp comparison against `head.committer.date`); attestations posted before subsequent commits are invalidated and MUST be re-posted.

The canonical attestation checklist (normative — `#336` MUST match each line exactly, modulo leading whitespace):

```markdown
SOLO_OPERATOR_ATTESTATION: confirmed

- [x] I read the diff with fresh eyes, not the same flow-state that authored it
- [x] I verified each FR/AC in the spec is satisfied by the actual implementation (not the implementation summary)
- [x] I ran the full validation bundle locally and reviewed the output (not just exit codes)
- [x] I checked for secrets, drift in unrelated files, and accidentally-staged WIP
- [x] I reviewed this as if a teammate authored it — including pushing back on shortcuts I would let myself take
```

**Immutable invariants across both paths.** The following hold regardless of `solo_operator` value and MUST NOT be relaxed by any consumer overlay:

- Factory bot identity detection by exact `user.login` equality (per #339 NFR-SEC-001 quoted above).
- Factory bot MUST NOT self-approve under any path; bot-authored sign-off comments are suppressed from the count.
- The four canonical sign-off phrases remain mandatory and verbatim; solo-operator mode reduces the human-count floor, not the phrase-discipline floor.
- All other factory controls (trigger-authorization-model FR-003, reject-rerun-cap FR-006, per-ticket-wall-clock-cost-ceiling FR-007, reviewer-model-heterogeneity FR-008) apply unchanged in both modes.

**Why no cool-head delay.** A mandatory time-buffer between last commit and merge was considered and rejected: enforcement requires either reliable GitHub-side timestamp arithmetic at gate evaluation (fragile when commits are amended) or operator self-discipline (no compensating control beyond the attestation itself). The attestation checklist is the entire compensating control; operators who skip the checklist's intent will also skip a delay, so the delay buys no real safety.

**Why per-repo (not per-PR).** `solo_operator` is set once in `blueprint/contract.yaml` and applied uniformly to every PR in the repo. Per-PR opt-in was rejected because deadline pressure is the exact failure mode that would convert "occasional emergency solo merge" into "always-solo": the per-repo decision must be deliberate and audit-visible.

## Options Considered

### Option A — Multi-author SoD with bot suppression via exact-login match (chosen)

The decision above.

**Pros:** preserves the multi-author guarantee at factory velocity; bot identity is unforgeable; mechanical enforcement at #336 needs only the PR comment thread; consumer instances inherit identically.

**Cons:** small teams may have to manually rotate which reviewer signs which phrase to satisfy the ≥ 2 floor. Mitigation: the gate-1 CODEOWNERS routing per FR-011 ensures four different teams are notified for the four phrases, making distinct reviewers the default outcome.

### Option B — Require all four phrases to come from four distinct identities (rejected)

Stricter rule: four phrases ⇒ four distinct logins.

**Rejected:** in small consumer instances the four canonical roles may be carried by fewer than four humans; the ≥ 2 floor is the minimum that defeats single-reviewer bus-factor risk without forcing artificial team expansion. Four-distinct-identity is left available to consumers as a tighter overlay; the blueprint floor is two.

### Option C — Match the bot identity by display name or email domain (rejected)

Use `user.name` ("Factory Bot") or email-domain match (`@factory.example`) instead of exact login.

**Rejected:** display names are user-mutable on GitHub (the bot can change its display name to a human's name in one API call); email-domain matches collapse if the bot's email is spoofed or its address rotates. Only `user.login` is unforgeable inside a single GitHub installation. Violates #339 NFR-SEC-001 directly.

### Option D — Trust the gate-1 CODEOWNERS routing alone (rejected)

Rely on CODEOWNERS to fan sign-offs to multiple teams; do not separately verify distinct identities at the comment layer.

**Rejected:** CODEOWNERS controls *notification* and *blocking-review* surface, not who can post a free-text comment. A single human can be a member of multiple gate-1 teams and post all four sign-off phrases; CODEOWNERS would not flag that. The comment-layer identity check is the only thing that catches it.

### Option E — Single floor, no solo-operator path (rejected)

Keep the multi-author floor as the only satisfaction path; solo operators either pair with an external reviewer or disable the factory.

**Rejected:** solo-operator topologies are a real and stable population (single-maintainer repos, two-repo personal projects, indie research initiatives, early-stage teams). Forcing them off the factory creates a worse failure mode than the SoD rule prevents: operators fabricate sign-offs from shell accounts, share credentials with collaborators, or abandon SDD entirely. A bounded alternative path with an enforceable attestation gate preserves the rule's *intent* (deliberate independent review) under a topology where the *implementation* (two distinct humans) is structurally impossible. Path 2 is bounded in five ways simultaneously — fixed-text marker, fixed-text checklist with all-checked requirement, gate-1 CODEOWNERS membership, post-last-commit timestamp, factory-bot suppression — making it harder to satisfy carelessly than the multi-author path.

## Consequences

- Phase 1 ticket #336 carries the enforcement logic for BOTH paths: read four sign-off comments, apply bot-suppression filter via exact `user.login` equality, count distinct non-bot logins; if `solo_operator: false` gate at ≥ 2; if `solo_operator: true` gate at ≥ 1 AND require a matching canonical attestation comment per § Satisfaction paths.
- Phase 1 ticket #334 inherits the exact-string-equality rule for any bot-identity check on its factory-runtime side (e.g., identifying which commits were authored by the factory bot for audit-log attribution).
- The four canonical sign-off phrases remain human-only — this ADR does not relax `AGENTS.md § Sign-off Policy`; it tightens the implementation of that policy at factory velocity. In solo-operator mode, the same human posts all four phrases plus the attestation comment.
- Consumer instances inherit the rule identically (sealed per #339 C8 FR-017(b)); the `solo_operator` toggle in `blueprint/contract.yaml` selects between two blueprint-defined satisfaction paths, not a consumer-authored variant. The bot login string itself is parameterized per consumer overlay (#339 C8 FR-014) because each consumer runs its own factory bot account.
- The C7 lifecycle event stream (#339 Contract C7) carries the bot's GitHub login in the `actor` field where applicable, so post-hoc audit of "did a bot ever count toward SoD" is one query away. The C7 stream also carries the `solo_operator` mode flag per spec event, so auditors can filter on which path each merge was approved under.
- Solo-operator mode is audit-visible: `solo_operator: true` lives in `blueprint/contract.yaml` (under version control, diff-reviewable on every contract change) and every solo-merged PR carries the canonical attestation comment as a permanent thread record.

## References

- Spec: `specs/2026-05-28-issue-337-factory-phase-0-foundations/spec.md` § FR-005, § NFR-SEC-002
- Meta-ADR: [`ADR-issue-337-factory-phase-0-foundations.md`](ADR-issue-337-factory-phase-0-foundations.md)
- Related: [`ADR-issue-337-trigger-authorization-model.md`](ADR-issue-337-trigger-authorization-model.md) (the factory-operations team allowlist composes with this rule), [`ADR-issue-337-persona-skill-contract.md`](ADR-issue-337-persona-skill-contract.md) (no AI persona maps to a sign-off role)
- `AGENTS.md § Sign-off Policy`, § Sign-off Phrases (Deterministic)
- Design contracts: `docs/blueprint/autonomous-factory/design-contracts.md` § Contract C5 (Factory Bot Identity + SoD Detection), § Contract C7 (lifecycle event `actor` field), § NFR-SEC-001 (exact-string-equality)
- Contract toggle: `blueprint/contract.yaml § spec.spec_driven_development_contract.readiness_gate.sod_policy` (`solo_operator` boolean; default `false`)
- Phase 1 implementers: #334 (factory runtime), #336 (GitHub Actions webhooks — enforces both satisfaction paths)

## Amendments

- 2026-05-29 (PR #345, Step 06 follow-up): added § Satisfaction paths with Path 2 (solo-operator) as a blueprint-defined alternative satisfaction path; added Option E (rejected); extended Consequences to cover Path 2; preserved `sealed` extensibility classification under the rationale that consumer mode-selection from a fixed blueprint-defined path-set is not parameterization in the FR-017 sense. No change to NFR-SEC-002, no change to factory-bot suppression rule.
