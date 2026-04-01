# Async Pact Producer Contracts

Place producer-side async message contract assets in this directory.

Recommended conventions:
- Store pact message artifacts and fixtures under this directory.
- Provide `verify.sh` here or set `ASYNC_PACT_PRODUCER_VERIFY_CMD` in `blueprint/repo.init.env`.
- Producer verification runs via `make test-contracts-async-producer` when `ASYNC_PACT_MESSAGE_CONTRACTS_ENABLED=true`.

Runtime environment variables available to verify commands:
- `ASYNC_PACT_PROVIDER` (`pact`)
- `ASYNC_PACT_MESSAGE_ROLE` (`producer`)
- `ASYNC_PACT_CONTRACTS_DIR`
- `ASYNC_PACT_ARTIFACT_DIR`
