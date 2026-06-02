---
name: blueprint-agent-stop-cleanup
description: Terminate a persona run, reclaim its workspace, and emit the agent-stop label so the runtime can clean up under the issue #336 contract.
blueprint-version: 1.0.0
extensibility-tier: extensible
emits-phase: agent-pr-review
---

# Blueprint Agent Stop Cleanup

## When to Use

Invoked at the end of every persona run, regardless of outcome
(`success | rejected | retried | human-handoff`). The skill produces a
cleanup report the orchestrator uses to release the workspace pod and emit
the `agent-stop` label per the #336 webhook handler contract.

## Actor

Invoked by every persona at the end of its run. The persona files declare
this skill in `## Collaboration & Handoffs` so the termination handoff is
visible without reading any skill runbook.

## Inputs

- The current persona's run identifier and the work-item ticket id.
- The structured outcome of the persona run drawn from the enum
  `success | rejected | retried | human-handoff`.
- The list of skill invocations the persona made during the run.

## Steps

1. Compile the run-summary metadata (start time, end time, skill
   invocation count).
2. Identify any workspace artifacts that MUST persist beyond the run
   (the JSONL C7 sink, the work-item branch commits).
3. Identify any ephemeral state the runtime MUST reclaim (the workspace
   pod, the OpenHands session handle, the persona's working directory).
4. Return the structured payload described in `## Required Output Schema`
   below. The orchestrator acts on the payload to release the workspace
   and emit the `agent-stop` label per the #336 contract.

## Composition

This skill MUST NOT directive-invoke any other skill. The orchestrator
performs the actual pod-release action; this skill produces the structured
request only.

## Required Output Schema

The orchestrator emits the persona's last C7 lifecycle event on skill
completion (the phase value matches the persona's terminating phase, e.g.,
`agent-pr-review` for reviewer personas); the structured payload below is
the `outcome.details` carried on that event.

```yaml jsonschema
$schema: "http://json-schema.org/draft-07/schema#"
title: BlueprintAgentStopCleanupOutput
description: Cleanup request payload emitted at the end of every persona run.
type: object
additionalProperties: false
required:
  - ticket_id
  - persona
  - run_outcome
  - persistent_artifacts
  - ephemeral_resources
properties:
  ticket_id:
    type: string
  persona:
    type: string
    description: Persona name (basename without `.md`) under `.agents/personas/`.
  run_outcome:
    type: string
    enum:
      - success
      - rejected
      - retried
      - human-handoff
  persistent_artifacts:
    type: array
    description: Paths or identifiers that MUST persist beyond the run.
    items:
      type: string
  ephemeral_resources:
    type: array
    description: Identifiers the runtime MUST reclaim (pods, session handles, working directories).
    items:
      type: object
      additionalProperties: false
      required:
        - kind
        - identifier
      properties:
        kind:
          type: string
          enum:
            - workspace-pod
            - openhands-session
            - working-directory
            - other
        identifier:
          type: string
  agent_stop_label_requested:
    type: boolean
    description: True when the orchestrator MUST emit the `agent-stop` label per the #336 contract.
```
