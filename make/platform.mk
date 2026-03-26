# Platform-owned Make targets.
# Safe to edit in generated repositories.

.PHONY: \
  apps-bootstrap apps-smoke apps-audit-versions apps-audit-versions-cached apps-publish-ghcr \
  backend-test-unit backend-test-integration backend-test-contracts backend-test-e2e \
  touchpoints-test-unit touchpoints-test-integration touchpoints-test-contracts touchpoints-test-e2e \
  test-unit-all test-integration-all test-contracts-all test-e2e-all-local

apps-bootstrap: ## Bootstrap app build/deploy prerequisites
	@scripts/bin/platform/apps/bootstrap.sh

apps-smoke: ## App-level smoke checks
	@scripts/bin/platform/apps/smoke.sh

apps-audit-versions: ## Audit app/base-image dependency versions
	@scripts/bin/platform/apps/audit_versions.sh

apps-audit-versions-cached: ## Audit app/base-image dependency versions with local success cache
	@scripts/bin/platform/apps/audit_versions_cached.sh

apps-publish-ghcr: ## Build and publish backend/touchpoints images to GHCR (dry-run by default)
	@scripts/bin/platform/apps/publish_ghcr.sh

backend-test-unit: ## Backend unit tests
	@scripts/bin/platform/backend/test_unit.sh

backend-test-integration: ## Backend integration tests
	@scripts/bin/platform/backend/test_integration.sh

backend-test-contracts: ## Backend contract tests
	@scripts/bin/platform/backend/test_contracts.sh

backend-test-e2e: ## Backend E2E tests
	@scripts/bin/platform/backend/test_e2e.sh

touchpoints-test-unit: ## Touchpoints unit tests
	@scripts/bin/platform/touchpoints/test_unit.sh

touchpoints-test-integration: ## Touchpoints integration tests
	@scripts/bin/platform/touchpoints/test_integration.sh

touchpoints-test-contracts: ## Touchpoints contract tests
	@scripts/bin/platform/touchpoints/test_contracts.sh

touchpoints-test-e2e: ## Touchpoints E2E tests
	@scripts/bin/platform/touchpoints/test_e2e.sh

test-unit-all: ## Run all unit-test lanes
	@scripts/bin/platform/test/unit_all.sh

test-integration-all: ## Run all integration-test lanes
	@scripts/bin/platform/test/integration_all.sh

test-contracts-all: ## Run all contract-test lanes
	@scripts/bin/platform/test/contracts_all.sh

test-e2e-all-local: ## Full local E2E chain
	@scripts/bin/platform/test/e2e_all_local.sh
