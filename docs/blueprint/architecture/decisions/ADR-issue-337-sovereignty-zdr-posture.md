# ADR: EU Sovereignty + Zero-Data-Retention Posture

**Status:** approved
**Date:** 2026-05-29
**Issue:** #337
**Spec:** `specs/2026-05-28-issue-337-factory-phase-0-foundations/` (FR-004, NFR-SEC-001)
**Meta-ADR:** [`ADR-issue-337-factory-phase-0-foundations.md`](ADR-issue-337-factory-phase-0-foundations.md)
**Extensibility classification (#339 C8 FR-017):** `sealed` (listed explicitly in FR-017(b)).

## Context

The factory runs LLM inference against external Anthropic models. Two compliance constraints govern this surface: **EU sovereignty** (model traffic MUST land in EU-resident infrastructure) and **zero-data-retention (ZDR)** (prompt/completion content MUST NOT be retained by the model provider beyond the request lifetime). Both are enforced today by the LiteLLM gateway and the provider configuration that LiteLLM fronts — not by anything the factory runtime itself owns.

Without an explicit ADR pinning this enforcement boundary, a well-meaning Phase 1 implementation could introduce a "factory-side ZDR header" or a "factory-side EU-region pin" that duplicates the gateway's responsibility, drifts from the gateway's actual configuration, and creates a second compliance surface to audit. This ADR pins the enforcement point exactly once.

## Decision Drivers

- Single point of enforcement is easier to audit than two duplicated points (one of which can silently drift).
- The factory has no reason to retain prompt/completion content beyond the lifecycle event metadata declared by #339 Contract C7 — the event schema explicitly excludes prompt/completion bodies, so the factory's persistent surface already complies with ZDR.
- API-key custody at the factory layer would create a credential-exfiltration risk and an additional rotation surface; routing all model calls through the existing LiteLLM gateway eliminates both.
- Sovereignty/ZDR posture is a sealed identical rule under #339 C8 FR-017(b) — consumer instances inherit it without per-instance tuning.

## Decision

EU sovereignty and ZDR are enforced **upstream by the LiteLLM gateway** and the model providers it fronts. The factory runtime MUST NOT:

1. **Store Anthropic API keys.** Credentials for any model provider MUST live in the LiteLLM gateway's own secret store. The factory authenticates to LiteLLM (not to Anthropic directly) using a single LiteLLM-issued credential held in ESO + STACKIT Secrets Manager per #335.
2. **Bypass the LiteLLM gateway.** Every model invocation — from every persona, in every SDD step — MUST flow through LiteLLM. Direct calls to `api.anthropic.com` (or any provider endpoint) MUST be rejected at egress by the factory namespace NetworkPolicy (#334).
3. **Retain prompt or completion content beyond the lifecycle event metadata declared by #339 Contract C7.** The C7 schema carries identifiers, timestamps, model names, and outcome enums — explicitly no prompt or completion bodies. Log redaction in the factory runtime MUST preserve this boundary: if a debug log would contain a prompt or completion, it MUST be redacted before write.

## Options Considered

### Option A — Upstream-only enforcement at the LiteLLM gateway (chosen)

The decision above.

**Pros:** single audit surface; no credential custody at the factory; no duplicate ZDR header logic; matches the existing STACKIT-managed model-access posture; consumer instances inherit identically.

**Cons:** any LiteLLM-gateway misconfiguration becomes a factory-wide compliance gap. Mitigation: LiteLLM-gateway operations are a sealed external service (#339 C8 § External service); the factory's egress NetworkPolicy ensures no out-of-band path exists even if LiteLLM is misconfigured.

### Option B — Factory-side ZDR enforcement in addition to LiteLLM (rejected)

Have the factory inject an explicit ZDR header on every outbound request as defense-in-depth.

**Rejected:** the header value is meaningful only to the provider, not to LiteLLM — so the factory would be coupling to provider-specific protocol surface, which violates the "factory-talks-to-LiteLLM-only" boundary. Defense-in-depth claims here are theatre: the gateway is the only point that touches the provider.

### Option C — Direct factory-to-Anthropic calls with the factory holding the API key (rejected)

Skip LiteLLM; let the factory call providers directly.

**Rejected:** introduces a second credential custody surface; bypasses the sovereignty/ZDR enforcement that LiteLLM is configured to provide; consumer instances would each need their own provider credentials. Violates #339 NFR-SEC-001 and SDD-C-013 (managed-first).

### Option D — Factory-side prompt/completion logging for debugging, with retention policy (rejected)

Allow the factory to log prompt/completion bodies for support purposes with a documented retention.

**Rejected:** any non-zero retention creates a compliance footprint the factory does not currently carry. Debugging needs are met by the C7 event stream (identifiers, outcomes, model names, timestamps) plus the LiteLLM-side gateway logs that already comply with the configured retention policy.

## Consequences

- Phase 1 tickets #334 (factory runtime on SKE) and #335 (OpenHands + LiteLLM) inherit this posture: #334 implements the egress NetworkPolicy that blocks direct provider calls; #335 implements the LiteLLM-only credential model with ESO + Secrets Manager.
- The factory's audit posture (#339 Contract C7 event schema) carries no prompt/completion content by definition — the schema is the compliance contract.
- Any future "let's just have the factory call provider X directly" proposal MUST go through #339 sign-off as a Contract C8 amendment — it cannot land via a Phase 1 PR.
- Consumer instances inherit the sealed posture; they MUST NOT introduce a factory-side credential or a direct-provider egress path. The consumer overlay for LiteLLM access (#339 C8 FR-014) governs how each consumer points at its own LiteLLM gateway — credentials still live in the gateway, not in the factory.

## References

- Spec: `specs/2026-05-28-issue-337-factory-phase-0-foundations/spec.md` § FR-004, § NFR-SEC-001
- Meta-ADR: [`ADR-issue-337-factory-phase-0-foundations.md`](ADR-issue-337-factory-phase-0-foundations.md)
- Related: [`ADR-issue-337-llm-model-router-policy.md`](ADR-issue-337-llm-model-router-policy.md) (router policy that flows through the same LiteLLM gateway)
- Design contracts: `docs/blueprint/autonomous-factory/design-contracts.md` § Contract C7 (event schema — explicitly excludes prompt/completion content), § Contract C8 § External service (LiteLLM access configuration)
- Phase 1 implementers: #334 (factory runtime on SKE), #335 (OpenHands + LiteLLM)
