# ADR: Trigger Authorization Model (`agent-ready` / `agent-stop`)

**Status:** approved
**Date:** 2026-05-29
**Issue:** #337
**Spec:** `specs/2026-05-28-issue-337-factory-phase-0-foundations/` (FR-003)
**Meta-ADR:** [`ADR-issue-337-factory-phase-0-foundations.md`](ADR-issue-337-factory-phase-0-foundations.md)
**Extensibility classification (#339 C8 FR-017):** `sealed` for the trigger names and cascade semantics; `parameterized` for the team allowlist slug (consumer overlay schema lives in #339 Contract C8).

## Context

The factory starts work on a GitHub issue when `agent-ready` is applied and stops in-flight runs when `agent-stop` is applied. Without an explicit authorization model, any repository member with write access could trigger an autonomous run — bypassing the SoD posture #339 NFR-SEC-001 establishes for sign-off comments. Similarly, without a defined `agent-stop` cascade, stopping a decomposed parent would leave child runs alive.

## Decision Drivers

- The cost of an unauthorized factory run is bounded but real (FR-007 cost ceiling caps per-ticket spend; reputational/operational cost of an unwanted run on production-adjacent repos is higher).
- `agent-stop` MUST be effective fast enough to halt runaway work before it consumes the cost ceiling.
- The cascade is critical for decomposed parents — partial halts leave children running with no parent to merge into.
- The trigger names themselves should be identical across consumer instances so cross-repo runbooks and incident response are consistent; the team allowlist necessarily varies per instance.

## Decision

**`agent-ready` authorization.** The label `agent-ready` MUST NOT be applied by any GitHub user whose membership in a designated GitHub team allowlist does not resolve to true at the moment of label application. The team slug name is parameterized per factory instance and MUST be declared via the #339 C8 consumer overlay schema. For the blueprint instance, the team is `@sbonoc/factory-operations` (the team that operates the factory itself); see [`ADR-issue-337-separation-of-duties-at-factory-velocity.md`](ADR-issue-337-separation-of-duties-at-factory-velocity.md) for how this composes with the SoD rule.

**`agent-stop` semantics.** Application of `agent-stop` MUST abort in-flight factory runs within **60 seconds** of label application. Enforcement is the responsibility of the GitHub Actions webhook layer (#336) — checks the label state at each persona-transition boundary, and SIGTERMs the in-progress persona on detection.

**`agent-stop` cascade.** Application of `agent-stop` to a parent issue MUST propagate to every open child issue created by `blueprint-ticket-decompose-light` (FR-010). Cascade target identification: children carry the parent's issue number in their body per the #339 Contract C2 child-spec convention and per FR-010's parent-tracking contract.

**Implementer.** #336 (GitHub Actions webhooks) carries the enforcement logic for both the team-allowlist check on `agent-ready` and the 60-second stop semantics + cascade.

## Options Considered

### Option A — Team-allowlist gating + 60s stop + cascade (chosen)

The decision above.

**Pros:** clear, minimal-config authorization; 60s is short enough to bound runaway cost (< $1 worst-case at typical model spend); cascade preserves decomposition contract integrity.

**Cons:** the team must be provisioned and maintained on GitHub. Mitigation: this is a one-time operational setup tracked under FR-011 (CODEOWNERS) team provisioning.

### Option B — Single fixed allowlist of GitHub logins (rejected)

Hardcode a set of logins in the factory config.

**Rejected:** turns membership rotation into a code change; consumer instances cannot inherit the convention without rewriting their own config; fails the "parameterized" classification under #339 C8.

### Option C — No `agent-stop` cascade (rejected)

Halt only the directly labelled issue; require operators to label each child individually.

**Rejected:** races against ongoing child runs; in a 5-child decomposition (FR-010 fan-out cap) the operator would need to apply five labels at the same second to be effective.

### Option D — Synchronous stop (block until persona exits) (rejected)

Block the label-applier's action until the run is fully halted.

**Rejected:** GitHub label-apply is a UI/API action with no streaming response model; the user would see an indefinite spinner. The 60s upper bound from Option A is observed via PR comments / event stream and is operationally adequate.

## Consequences

- Phase 1 ticket #336 implements the team-allowlist check and the 60s stop + cascade.
- The blueprint instance allowlist (`@sbonoc/factory-operations`) ensures factory-start authority sits with the same team carrying Operations sign-off (per [`ADR-issue-337-separation-of-duties-at-factory-velocity.md`](ADR-issue-337-separation-of-duties-at-factory-velocity.md)), which is intentional — Operations is the on-call team for factory runtime per FR-012's owner assignment.
- Consumer instances populate their own allowlist team slug via `spec.factory_contract.triggers.agent_ready_allowlist_team` in their `contract.yaml` (overlay schema; see #339 C8 consumer overlay pattern).
- The `agent-stop` cascade preserves FR-010 light-decomposition policy integrity — parent halt deterministically halts all children.
- Telemetry: every `agent-stop`-caused abort emits a C7 lifecycle event with `outcome: human-handoff` (per #339 C7 outcome enum), so the bus carries the audit trail.

## References

- Spec: `specs/2026-05-28-issue-337-factory-phase-0-foundations/spec.md` § FR-003
- Meta-ADR: [`ADR-issue-337-factory-phase-0-foundations.md`](ADR-issue-337-factory-phase-0-foundations.md)
- Related: [`ADR-issue-337-separation-of-duties-at-factory-velocity.md`](ADR-issue-337-separation-of-duties-at-factory-velocity.md), [`ADR-issue-337-light-decomposition-policy.md`](ADR-issue-337-light-decomposition-policy.md), [`ADR-issue-337-reject-rerun-cap.md`](ADR-issue-337-reject-rerun-cap.md)
- Design contracts: `docs/blueprint/autonomous-factory/design-contracts.md` § Contract C7 (lifecycle event schema), § Contract C8 (consumer overlay)
- Phase 1 implementer: #336 (GitHub Actions webhooks)
