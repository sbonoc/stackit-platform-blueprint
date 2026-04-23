# Platform-owned Make targets.
# Safe to edit in generated repositories.
# ownership: platform-owned (generated-consumer maintainers are the implementation owners).

.PHONY: \
  auth-reconcile-eso-runtime-secrets auth-reconcile-argocd-repo-credentials auth-reconcile-runtime-identity auth-runtime-identity-doctor \
  infra-post-deploy-consumer \
  apps-bootstrap apps-ci-bootstrap apps-ci-bootstrap-consumer apps-smoke apps-audit-versions apps-audit-versions-cached apps-publish-ghcr \
  backend-test-unit backend-test-integration backend-test-contracts backend-test-e2e \
  touchpoints-test-unit touchpoints-test-integration touchpoints-test-contracts touchpoints-test-e2e \
  test-unit-all test-integration-all test-contracts-all test-e2e-all-local test-e2e-all-local-full test-e2e-all-local-execute \
  test-smoke-all-local

auth-reconcile-eso-runtime-secrets: ## Reconcile generic ESO runtime source-to-target credentials contract
	@scripts/bin/platform/auth/reconcile_eso_runtime_secrets.sh

auth-reconcile-argocd-repo-credentials: ## Reconcile ArgoCD Git repository credentials and validate URL/auth contract
	@scripts/bin/platform/auth/reconcile_argocd_repo_credentials.sh

auth-reconcile-runtime-identity: ## Reconcile runtime identity contracts (ESO, Argo repo access, Keycloak/module coverage)
	@scripts/bin/platform/auth/reconcile_runtime_identity.sh

auth-runtime-identity-doctor: ## Diagnose runtime identity readiness with consolidated Argo/ESO/contract diagnostics
	@scripts/bin/platform/auth/runtime_identity_doctor.sh

infra-post-deploy-consumer: ## Consumer-owned local infra post-deploy hook contract target (optional)
	@# blueprint-consumer-contract: infra-post-deploy-consumer must be replaced by generated-consumer maintainers.
	@if grep -qE '^[[:space:]]*repo_mode:[[:space:]]*generated-consumer$$' blueprint/contract.yaml; then \
		echo "[blueprint] infra-post-deploy-consumer placeholder active; implement deterministic local post-deploy reconciliation commands in make/platform.mk and set LOCAL_POST_DEPLOY_HOOK_ENABLED=true when ready" >&2; \
		exit 1; \
	fi
	@echo "[blueprint] infra-post-deploy-consumer placeholder skipped in template-source repo mode"

apps-bootstrap: ## Bootstrap app build/deploy prerequisites
	@scripts/bin/platform/apps/bootstrap.sh

apps-ci-bootstrap: ## Bootstrap CI runner dependencies for app/test lanes (consumer-owned override point)
	@$(MAKE) apps-bootstrap
	@$(MAKE) apps-ci-bootstrap-consumer

apps-ci-bootstrap-consumer: ## Consumer-owned dependency install hook for app/test lanes (required in generated-consumer repos)
	@# blueprint-consumer-contract: apps-ci-bootstrap-consumer must be replaced by generated-consumer maintainers.
	@if grep -qE '^[[:space:]]*repo_mode:[[:space:]]*generated-consumer$$' blueprint/contract.yaml; then \
		echo "[blueprint] apps-ci-bootstrap-consumer placeholder active; implement deterministic dependency bootstrap commands for your repository layout in make/platform.mk" >&2; \
		exit 1; \
	fi
	@echo "[blueprint] apps-ci-bootstrap-consumer placeholder skipped in template-source repo mode"

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

test-e2e-all-local: ## Fast local E2E chain (dry-run infra + backend e2e lane)
	@scripts/bin/platform/test/e2e_all_local.sh --scope fast

test-e2e-all-local-full: ## Full local E2E chain in dry-run mode (backend + touchpoints e2e lanes)
	@scripts/bin/platform/test/e2e_all_local.sh --scope full

test-e2e-all-local-execute: ## Full local E2E chain in execute mode (DRY_RUN=false, backend + touchpoints e2e lanes)
	@scripts/bin/platform/test/e2e_all_local.sh --scope full --execute

test-smoke-all-local: ## Full local smoke lane: provision, infra-smoke, and endpoint assertions against a local cluster
	@scripts/bin/platform/test/smoke_all_local.sh
