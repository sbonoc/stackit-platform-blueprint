# ADR: Separation of Duties at Factory Velocity

**Status:** approved
**Date:** 2026-05-29
**Issue:** #337
**Spec:** `specs/2026-05-28-issue-337-factory-phase-0-foundations/` (FR-005, NFR-SEC-002)
**Meta-ADR:** [`ADR-issue-337-factory-phase-0-foundations.md`](ADR-issue-337-factory-phase-0-foundations.md)
**Extensibility classification (#339 C8 FR-017):** `sealed` (the multi-author SoD identical rule is listed explicitly in FR-017(b)).

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

**Enforcement layer.** #336 (GitHub Actions webhooks) reads the four most recent sign-off comments, extracts `user.login` for each, applies the bot-suppression filter, and rejects the spec gate if fewer than two distinct logins remain. Cited by #334 (which inherits the same exact-string match for any factory-side bot-identity check it adds).

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

## Consequences

- Phase 1 ticket #336 carries the enforcement logic: read four sign-off comments, apply bot-suppression filter via exact `user.login` equality, count distinct logins, gate at ≥ 2.
- Phase 1 ticket #334 inherits the exact-string-equality rule for any bot-identity check on its factory-runtime side (e.g., identifying which commits were authored by the factory bot for audit-log attribution).
- The four canonical sign-off phrases remain human-only — this ADR does not relax `AGENTS.md § Sign-off Policy`; it tightens the implementation of that policy at factory velocity.
- Consumer instances inherit the rule identically (sealed per #339 C8 FR-017(b)); the bot login string itself is parameterized per consumer overlay (#339 C8 FR-014) because each consumer runs its own factory bot account.
- The C7 lifecycle event stream (#339 Contract C7) carries the bot's GitHub login in the `actor` field where applicable, so post-hoc audit of "did a bot ever count toward SoD" is one query away.

## References

- Spec: `specs/2026-05-28-issue-337-factory-phase-0-foundations/spec.md` § FR-005, § NFR-SEC-002
- Meta-ADR: [`ADR-issue-337-factory-phase-0-foundations.md`](ADR-issue-337-factory-phase-0-foundations.md)
- Related: [`ADR-issue-337-trigger-authorization-model.md`](ADR-issue-337-trigger-authorization-model.md) (the factory-operations team allowlist composes with this rule), [`ADR-issue-337-persona-skill-contract.md`](ADR-issue-337-persona-skill-contract.md) (no AI persona maps to a sign-off role)
- `AGENTS.md § Sign-off Policy`, § Sign-off Phrases (Deterministic)
- Design contracts: `docs/blueprint/autonomous-factory/design-contracts.md` § Contract C5 (Factory Bot Identity + SoD Detection), § Contract C7 (lifecycle event `actor` field), § NFR-SEC-001 (exact-string-equality)
- Phase 1 implementers: #334 (factory runtime), #336 (GitHub Actions webhooks)
