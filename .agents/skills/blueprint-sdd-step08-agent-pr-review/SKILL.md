---
name: blueprint-sdd-step08-agent-pr-review
description: Produce a structured findings list against the work-item PR diff at SDD step 08; one invocation per expert from the dispatched expert panel, returning a per-expert verdict array aligned with C7 outcome_details.expert_verdicts[].
blueprint-version: 1.0.0
extensibility-tier: extensible
emits-phase: agent-pr-review
---

# Blueprint SDD Step 08 — Agent PR Review

## Steps covered

- **Step 8** — Agent PR review pass that produces the structured findings
  list the human merge reviewer reads at the bounded-context human merge gate.

## When to Use

Invoked after the PR body has been authored by
`blueprint-sdd-step07-pr-packager` and before the human merge gate. The
orchestrator dispatches the full 8-expert panel for step08 per the SDD-step ×
expert matrix in `docs/blueprint/autonomous-factory/design-contracts.md` § C3
(convergence mode: **parallel-then-merge**; structured-disagreement fires as a
fallback only when ≥ 2 experts return `block` verdicts that share a finding
category and survive dedup — see ADR-issue-364 § 5.2). Each invocation reviews
the PR under exactly one expert lens and contributes one verdict to the panel array.

## Actor

Invoked once per expert in the panel dispatched for step08. The orchestrator
is the binding mechanism for which experts are consulted; the
expert-panel layer MUST NOT directive-invoke this skill. The
reviewer-model-heterogeneity ADR at
`docs/blueprint/architecture/decisions/ADR-issue-337-reviewer-model-heterogeneity.md`
(amended by `ADR-issue-364-expert-persona-model.md`) requires
**panel-disjointness**: within a single step's panel, the set of LiteLLM
routing keys actually used MUST contain at least 2 distinct **model families**
(not string-equality — see ADR-issue-364 § 4.3 for the `model_family(s)`
normalization; pairwise uniqueness across all 8 experts is NOT required, but
the panel MUST NOT collapse to a single model family) for the same
`(ticket_id, phase, rerun_round)` tuple. The pre-amendment implement-vs-review model-split
framing is superseded — the FR-008 audit invariant still pairs the
`phase: implement` C7 event with the `phase: agent-pr-review` event on the
same `ticket_id`, but the predicate is re-expressed at the **model-family**
layer against the per-panel routing-key set carried as the C7 extension
field `outcome_details.routing_keys` (per design-contracts § C7 — see the
`model_family(s)` normalization defined there). The audit asserts BOTH
(a) `model_family(implement.model)` is NOT the sole family represented in
`{model_family(k) : k ∈ agent-pr-review.outcome_details.routing_keys}`
(i.e., the panel carries ≥ 1 routing key from a different family than
implement), AND (b) the agent-pr-review `outcome_details.routing_keys` set
contains ≥ 2 distinct families. Comparing the two events' aggregate
`model` fields directly (the pre-amendment predicate) is unsatisfiable
under the panel model because the agent-pr-review event has one aggregate
`model` field (carrying the lead voice's routing key per § 4.4 / § 4.5)
but the panel has multiple per-expert routing keys, and the strings live
in different identifier spaces (minimum-schema family ID vs LiteLLM
prefixed key). The orchestrator (Child B, #361)
enforces the disjointness rule when assembling the panel for step08,
populates `outcome_details.routing_keys` on the emitted event, and
selects routing keys accordingly.

## Inputs

- The full work-item PR diff against the base branch.
- The single `expert_slug` this invocation is reviewing under (drawn from the
  step08 panel-input parameter the orchestrator supplies).
- The packaged PR body authored by the PR packager.
- The work-item `traceability.md` and `graph.json`.
- The expert's `## Worldview`, `## Default Heuristics`, `## Push-back Triggers`,
  `## What I Notice That Others Miss`, and `## Quality Bar` sections loaded
  from `.agents/personas/<expert_slug>/PERSONA.md`.

## Workflow

1. Read the PR diff and the expert's loaded persona sections.
2. Generate findings, one entry per concrete observation, conforming to
   the `ExpertVerdict.findings[]` shape pinned in
   `ADR-issue-364-expert-persona-model.md` § 6: required keys `category`
   and `summary`; optional keys `evidence_ref` (formatted as `path:line`
   to anchor the finding to a concrete diff location) and `severity`
   drawn from the enum `info | low | medium | high | critical`.
3. Compute a single per-expert verdict drawn from the enum `pass | revise |
   block`, following the verdict priority rule defined in
   `ADR-issue-364-expert-persona-model.md` § 6 (block > revise > pass).
4. Return the structured payload described in `## Required Output Schema`
   below; the orchestrator merges per-expert payloads into the
   structured-disagreement convergence output for step08 and validates
   each finding against the ADR § 6 `ExpertVerdict` schema. Payloads that
   diverge from that schema are rejected per ADR § 6.1 (treated as
   `missing-expert-verdict`).

## Guardrails

This skill MUST NOT directive-invoke any other skill (FR-016 composition
ban). Each expert invocation is independent; the orchestrator merges the
per-expert verdict arrays into the C7 `outcome_details.expert_verdicts[]`
field per `ADR-issue-337-c7-emission-mechanism.md` (amended by
`ADR-issue-364-expert-persona-model.md` § 9) and per design-contracts § C7.

## Required Report Format

Return:

1. The `expert_slug` this invocation was dispatched under.
2. The `findings` array conforming to the `ExpertVerdict.findings[]`
   shape in ADR-issue-364 § 6 (i.e., each finding is an object with
   required `category` and `summary`, optional `evidence_ref` and
   `severity`). The orchestrator computes the C7
   `outcome_details.expert_verdicts[].findings_count` integer (per
   ADR-issue-364 § 9 / design-contracts § C7) as the **length** of
   this array — the skill does NOT report a `findings_count`,
   `count`, or severity-grouped count field, since adding any such
   field would violate the `additionalProperties: false` constraint
   on `BlueprintAgentPrReviewOutput` below. A human-readable severity
   breakdown (e.g., `critical: 1, high: 0, medium: 3, low: 0, info: 0`)
   MAY appear in prose surrounding the structured payload but MUST
   NOT be added as a schema field on the structured output.
3. For each finding: `category` (short tag drawn from the expert's
   `## Push-back Triggers` set, suitable for grouping/dedup), `summary`
   (one-sentence statement), and optional `evidence_ref` (formatted as
   `path:line` to anchor the finding to a concrete diff location) and
   `severity` drawn from the enum `info | low | medium | high | critical`.
4. The single per-expert verdict (`pass | revise | block`) computed by the
   verdict priority rule.
5. Confirmation that every finding carries an `evidence_ref` anchoring it
   to a concrete diff location.

## Required Output Schema

The orchestrator merges the per-expert payloads from all dispatched
experts into an internal panel-merge structure used to author workspace
artifacts (referenced by the C7 event's `evidence_uri`), and then emits
a single `phase: agent-pr-review` C7 lifecycle event carrying the
**compact** per-expert summary array
(`outcome_details.expert_verdicts[]` as `ExpertVerdictSummary` per
ADR-issue-364 § 9 and design-contracts § C7). The per-expert payload
schema below is the input to that merge — it is NOT the C7 row shape.
The full `findings[]` array MUST NOT be inlined into the C7 event;
dashboards and ingest pipelines query counts via the
`findings_count` field on the compact row and load full payloads from
the referenced workspace artifact when needed.

```yaml jsonschema
$schema: "http://json-schema.org/draft-07/schema#"
title: BlueprintAgentPrReviewOutput
description: >-
  Structured per-expert verdict and findings list produced by one expert-panel
  invocation during the SDD step08 agent PR review phase. The orchestrator
  consumes this shape, merges across experts, writes the full findings to a
  workspace artifact, and emits the compact ExpertVerdictSummary row on the
  C7 agent-pr-review event per ADR-issue-364 § 9.
type: object
additionalProperties: false
required:
  - expert_slug
  - verdict
  - findings
properties:
  expert_slug:
    type: string
    description: >-
      Basename of the expert persona file under .agents/personas/. Drawn from
      EITHER the blueprint baseline roster locked by ADR-issue-364-expert-persona-model.md
      § 9 (the `expert_slug_blueprint` sealed enum, listed below — currently 8 slugs,
      widened to 9 by issue #361.5 when `usability-pragmatist` lands) OR the consumer
      overlay's allowlist for consumer-specific experts (the `expert_slug_extension`
      open string from design-contracts.md § C7 F-12 amendment 2026-06-19). This
      input-payload field stays single-key for orchestrator-internal handoff; the
      orchestrator routes the value into the correct sub-enum on the emitted C7 row
      based on whether it matches the blueprint baseline or the consumer overlay.
  verdict:
    type: string
    description: >-
      Single per-expert verdict computed by the priority rule defined in
      ADR-issue-364-expert-persona-model.md § 6 (block > revise > pass).
    enum:
      - pass
      - revise
      - block
  findings:
    type: array
    description: >-
      Per-finding list (may be empty when verdict is pass). Shape pinned by
      ADR-issue-364-expert-persona-model.md § 6 ExpertVerdict.findings[];
      the orchestrator (#361) validates each entry against that schema
      before merge per § 5.1 / § 6.1.
    items:
      type: object
      additionalProperties: false
      required:
        - category
        - summary
      properties:
        category:
          type: string
          description: >-
            Short tag for grouping/dedup (e.g., missing-observability,
            leaky-abstraction, retention-overshoot). Typically drawn from
            the expert's ## Push-back Triggers set. The merger dedups
            findings by (category, summary) tuple per § 5.1.
        summary:
          type: string
          description: >-
            One-sentence finding statement.
        evidence_ref:
          type: string
          description: >-
            Optional path:line (or other artifact reference) grounding
            the finding in the diff under review.
        severity:
          type: string
          enum:
            - info
            - low
            - medium
            - high
            - critical
          description: >-
            Severity ordering used by the merger's escalation rule
            (critical > high > medium > low > info) per ADR § 5.1 step 4.
```

The orchestrator MUST aggregate one such payload per dispatched expert into
an **internal** panel-merge structure (used to author the workspace
artifact referenced by the C7 event's `evidence_uri`):

```yaml
# orchestrator internal merge structure — NOT the C7 payload shape
panel_merge:
  expert_payloads:
    - { expert_slug: ..., verdict: ..., findings: [...] }
    - { expert_slug: ..., verdict: ..., findings: [...] }
```

The orchestrator then converts each row into the **compact**
`ExpertVerdictSummary` shape (ADR-issue-364 § 9) and emits exactly that
on the C7 event:

```yaml
# C7 event payload — compact summary only, MUST NOT carry the full findings array.
# Note: `outcome` itself remains a sealed STRING enum (`success | rejected | retried | human-handoff`)
# per the C7 minimum schema; the additive per-expert data lives on the sibling
# top-level object `outcome_details`, not nested inside `outcome`.
outcome: success
outcome_details:
  expert_verdicts:
    # Per ADR-issue-364 § 9 + design-contracts § C7 F-12 amendment 2026-06-19,
    # each row carries EXACTLY ONE of `expert_slug_blueprint` (sealed enum) OR
    # `expert_slug_extension` (consumer overlay string), never both.
    - { expert_slug_blueprint: product-pragmatist, verdict: pass,  findings_count: 0 }
    - { expert_slug_blueprint: boundary-hawk,      verdict: revise, findings_count: 3 }
  # Routing-key set actually used across the dispatched panel for this
  # (ticket_id, phase, rerun_round). Audit-of-record for FR-008 reviewer-
  # heterogeneity under ADR-issue-364 § 4.3 panel-disjointness.
  routing_keys:
    - anthropic/claude-opus-4-7
    - anthropic/claude-sonnet-4-6
    - anthropic/claude-haiku-4-5
evidence_uri: artifacts/c7/<work-item-slug>/agent-pr-review-round-0.json
```

per design-contracts § C7 and FR-007 of `ADR-issue-364-expert-persona-model.md`.

## C7 Emission (post-panel-merge — invoke exactly once per step08 round)

**⚠️ CRITICAL: This block MUST be executed exactly once per step08 round,
after all expert verdicts have been collected and merged. It is NOT invoked
once per expert. The orchestrator dispatches this skill once per expert
(up to 8 invocations), but C7 emission happens only once — after all 8
verdicts are merged into the panel-level summary.**

In the autonomous-factory bot path the orchestrator merges all per-expert
payloads first and then emits **one** `agent-pr-review` C7 event carrying
`outcome_details.expert_verdicts[]` (per ADR-issue-364 § 4 and
design-contracts § C7). The `local-cli` helper below is the human-assisted
equivalent: run it **once**, after completing all expert consultations for
this step08 round and consolidating the findings. Running it once per expert
invocation would produce 8 `agent-pr-review` events with duplicate
`(ticket_id, phase, rerun_round, emitter)` tuples, breaking the FR-008
implement↔review pairing and the event-id idempotency guarantee.

Resolve variable values from session context: `TICKET_ID` — the GitHub issue
number; `SKILL_BASENAME` — the `name:` value from this SKILL.md frontmatter;
`OWNER_TEAM` — the GitHub team slug owning this repository (e.g. `platform-team`);
`WORK_ITEM_SLUG` — the spec directory basename.

**Prerequisite — helper version:** the `--extension-json` flag was added to
`scripts/bin/sdd/c7_emit.py` in blueprint version `1.0.0` (issue #364). If
your consumer repo seeded an older copy of the helper, the flag will not be
recognised. Verify with
`uv run python3 scripts/bin/sdd/c7_emit.py emit --help | grep extension-json`.
If the flag is absent, update your seeded helper from the blueprint source
before running this block, or omit `--extension-json` and emit the compact
minimum-field event only (expert-verdict attribution will be absent from the
C7 event until the helper is upgraded, degrading FR-008 audit coverage).

First, author the extension-fields payload to a temporary JSON file. The
payload MUST carry the three C7 extension fields the FR-008 audit
(design-contracts § C7) depends on: `outcome_details.expert_verdicts[]`
(compact summary, one row per dispatched expert), `outcome_details.routing_keys`
(set of LiteLLM routing keys actually used across the panel), and
`evidence_uri` (workspace artifact carrying the full per-finding payload).
Reserved minimum-schema keys (e.g., `model`, `outcome`, `phase`) MUST NOT
be shadowed.

```sh
EXT_PAYLOAD="$(mktemp)"
cat > "$EXT_PAYLOAD" <<'JSON'
{
  "outcome_details": {
    "expert_verdicts": [
      {"expert_slug_blueprint": "product-pragmatist", "verdict": "pass", "findings_count": 0}
    ],
    "routing_keys": ["anthropic/claude-opus-4-7", "anthropic/claude-sonnet-4-6"]
  },
  "evidence_uri": "artifacts/c7/<work-item-slug>/agent-pr-review-round-0.json"
}
JSON

uv run python3 scripts/bin/sdd/c7_emit.py emit \
  --ticket "$TICKET_ID" \
  --phase "agent-pr-review" \
  --skill "$SKILL_BASENAME" \
  --owner-team "$OWNER_TEAM" \
  --slug "$WORK_ITEM_SLUG" \
  --extension-json "$EXT_PAYLOAD"

rm -f "$EXT_PAYLOAD"
```

If the panel-incomplete reroute fires (ADR § 6.1), the same invocation
shape applies with `--outcome rejected`, the `expert_verdicts[]` stub
row carrying `verdict: "block"` and `findings_count: 0`, and the
extension payload additionally carrying `rejection_reason:
"missing-expert-verdict"` plus the artifact URI under `evidence_uri`.

Stage and commit the emitted JSONL — this commit is part of the authorized
skill workflow and must land immediately so the audit record is durable:

```sh
git add "artifacts/c7/$WORK_ITEM_SLUG.jsonl"
git diff --cached --quiet || {
  git commit -m "chore($WORK_ITEM_SLUG): emit C7 lifecycle event"
  git push
}
```

Set `BLUEPRINT_SDD_C7_EMIT=0` to suppress; exactly one `c7-emission-opted-out` event is written per work-item slug (subsequent opted-out steps write nothing — the guard above skips the commit in that case).
**The LLM MUST NOT write events directly — invoke the helper only.**
