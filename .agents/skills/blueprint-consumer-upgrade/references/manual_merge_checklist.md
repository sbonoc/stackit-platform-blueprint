# Manual Merge Checklist

Use this checklist when `required_manual_actions` is non-empty after preflight/apply.

## 1) Confirm Blocking Items

- Inspect `artifacts/blueprint/upgrade_preflight.json`.
- Extract `required_manual_actions` and affected paths.
- Treat runtime dependency edge breaks (missing referenced artifacts/scripts) as blocking.

## 2) Preserve Ownership Boundaries

- Keep consumer-owned files consumer-owned.
- Merge blueprint-managed updates without deleting consumer custom logic.
- Never use destructive commands to silence merge conflicts.

## 3) Resolve One Path at a Time

- For each path, compare:
  - current consumer file
  - blueprint target change
  - surrounding contract/doc references
- Prefer additive merges and explicit comments only when non-obvious behavior is introduced.

## 4) Re-run Required Commands

After merges, run in order:

```bash
make blueprint-upgrade-consumer
BLUEPRINT_UPGRADE_APPLY=true make blueprint-upgrade-consumer
make blueprint-upgrade-consumer-validate
make infra-validate
make quality-hooks-run
```

## 5) Close the Loop in Report

Always report:

- manual paths merged
- rationale per path
- remaining manual actions (if any)
- final validation outcomes
