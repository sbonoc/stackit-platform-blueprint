# Async Pact Consumer Contracts

Place consumer-side async message contract assets in this directory.

Recommended conventions:
- Store consumer verification fixtures and pact expectations under this directory.
- Provide `verify.sh` here or set `ASYNC_PACT_CONSUMER_VERIFY_CMD` in `blueprint/repo.init.env`.
- Consumer verification runs via `make test-contracts-async-consumer` when `ASYNC_PACT_MESSAGE_CONTRACTS_ENABLED=true`.

Runtime environment variables available to verify commands:
- `ASYNC_PACT_PROVIDER` (`pact`)
- `ASYNC_PACT_MESSAGE_ROLE` (`consumer`)
- `ASYNC_PACT_CONTRACTS_DIR`
- `ASYNC_PACT_ARTIFACT_DIR`
