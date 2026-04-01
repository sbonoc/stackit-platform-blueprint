# Async Message Contracts (Pact)

The blueprint supports an opt-in async message-contract lane for producer and consumer verification using Pact-compatible workflows.

## Goals
- Keep async contract file locations deterministic for generated consumers.
- Provide standard `make` targets for producer, consumer, and aggregate lanes.
- Keep broker publication and can-i-deploy gates optional and command-driven.
- Preserve backward compatibility when async lanes are disabled.

## Canonical Paths
- Producer contracts: `contracts/async/pact/messages/producer`
- Consumer contracts: `contracts/async/pact/messages/consumer`

Each directory includes a seeded `README.md` and `.gitkeep` in generated repositories.

## Enablement
Configure `blueprint/repo.init.env`:

```bash
ASYNC_PACT_MESSAGE_CONTRACTS_ENABLED=true
ASYNC_PACT_PRODUCER_VERIFY_CMD='pnpm --dir apps/touchpoints run test:pact:producer'
ASYNC_PACT_CONSUMER_VERIFY_CMD='pnpm --dir apps/touchpoints run test:pact:consumer'
```

When enabled, the following targets are available:
- `make test-contracts-async-producer`
- `make test-contracts-async-consumer`
- `make test-contracts-async-all`

The aggregate lane `make test-contracts-all` is augmented to depend on `test-contracts-async-all`.

## Optional Broker And Deployment Gates
All optional hooks are no-op when unset:

```bash
ASYNC_PACT_BROKER_PUBLISH_CMD='pact-broker publish "$ASYNC_PACT_ARTIFACT_DIR" --branch "$GIT_BRANCH"'
ASYNC_PACT_CAN_I_DEPLOY_CMD='pact-broker can-i-deploy --pacticipant touchpoints --version "$APP_VERSION"'
```

Execution contract for verify/hook commands:
- Commands run with `bash -lc`.
- `ASYNC_PACT_PROVIDER=pact` is exported.
- `ASYNC_PACT_MESSAGE_ROLE` is `producer` or `consumer` during lane execution.
- `ASYNC_PACT_CONTRACTS_DIR` and `ASYNC_PACT_ARTIFACT_DIR` are exported to commands.

## CI Pattern (Generic)
A minimal CI sequence:

```bash
make quality-hooks-fast
make test-contracts-all
make quality-hooks-strict
```

For async-enabled repositories, add broker commands through CI environment variables.

## Upgrade Path For Existing Generated Repositories
1. Plan and apply blueprint-managed upgrades:

```bash
BLUEPRINT_UPGRADE_REF=<tag|branch|commit> make blueprint-upgrade-consumer
BLUEPRINT_UPGRADE_REF=<tag|branch|commit> BLUEPRINT_UPGRADE_APPLY=true make blueprint-upgrade-consumer
make blueprint-upgrade-consumer-validate
```

2. Keep `ASYNC_PACT_MESSAGE_CONTRACTS_ENABLED=false` until producer/consumer verify commands are configured.
3. After commands are configured, enable the toggle and run:

```bash
make test-contracts-async-all
make test-contracts-all
```

## Failure Triage
- `verify_entrypoint_missing`: async lanes are enabled but no verify command (or `verify.sh`) is configured.
- `verify_command_failed` / `verify_script_failed`: producer or consumer verification command returned non-zero.
- `producer_publish_failed`: optional broker publish hook failed.
- `can_i_deploy` hook failures: deployment gate command returned non-zero.
