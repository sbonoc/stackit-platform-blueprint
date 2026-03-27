SHELL := /bin/bash
.DEFAULT_GOAL := help

.PHONY: help \
  blueprint-init-repo blueprint-init-repo-interactive blueprint-check-placeholders blueprint-template-smoke blueprint-release-notes blueprint-migrate blueprint-bootstrap blueprint-render-makefile blueprint-clean-generated blueprint-render-module-wrapper-skeletons \
  quality-hooks-run quality-docs-lint quality-docs-sync-core-targets quality-docs-check-core-targets-sync quality-docs-sync-contract-metadata quality-docs-check-contract-metadata-sync quality-test-pyramid \
  infra-prereqs infra-help-reference infra-bootstrap infra-destroy-disabled-modules infra-validate infra-smoke infra-provision infra-deploy infra-provision-deploy \
  infra-stackit-bootstrap-preflight infra-stackit-bootstrap-plan infra-stackit-bootstrap-apply infra-stackit-bootstrap-destroy \
  infra-stackit-foundation-preflight infra-stackit-foundation-plan infra-stackit-foundation-apply infra-stackit-foundation-destroy \
  infra-stackit-foundation-fetch-kubeconfig infra-stackit-foundation-refresh-kubeconfig infra-stackit-foundation-seed-runtime-secret \
  infra-stackit-ci-github-setup infra-stackit-destroy-all \
  infra-stackit-runtime-prerequisites infra-stackit-runtime-inventory infra-stackit-runtime-deploy \
  infra-stackit-smoke-foundation infra-stackit-smoke-runtime infra-stackit-provision-deploy \
  infra-argocd-topology-render infra-argocd-topology-validate \
  infra-doctor infra-context infra-status infra-status-json \
  infra-audit-version infra-audit-version-cached \
  docs-install docs-run docs-build docs-smoke

help: ## Show targets
	@awk 'BEGIN {FS = ":.*## "} /^[a-zA-Z0-9_.-]+:.*## / {printf "%-50s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

blueprint-init-repo: ## Initialize repository identity after GitHub template creation
	@scripts/bin/blueprint/init_repo.sh

blueprint-init-repo-interactive: ## Interactive repository identity wizard for GitHub template consumers
	@scripts/bin/blueprint/init_repo_interactive.sh

blueprint-check-placeholders: ## Verify generated repository identity placeholders are resolved
	@scripts/bin/blueprint/check_placeholders.sh

blueprint-template-smoke: ## Run generated-repo conformance smoke in a temp copy
	@scripts/bin/blueprint/template_smoke.sh

blueprint-release-notes: ## Generate template release notes
	@scripts/bin/blueprint/release_notes.sh

blueprint-migrate: ## Apply blueprint repository migrations for current template version
	@scripts/bin/blueprint/migrate.sh

blueprint-bootstrap: ## Bootstrap blueprint-scoped templates, docs, and Makefile rendering
	@scripts/bin/blueprint/bootstrap.sh

blueprint-render-makefile: ## Render blueprint-generated make targets from template and enabled module flags
	@scripts/bin/blueprint/render_makefile.sh

blueprint-clean-generated: ## Remove generated runtime/build/cache artifacts
	@scripts/bin/blueprint/clean_generated.sh

blueprint-render-module-wrapper-skeletons: ## Render optional-module wrapper skeleton templates from module contracts
	@scripts/bin/blueprint/render_module_wrapper_skeletons.sh

quality-hooks-run: ## Run pre-commit hooks and quality gates
	@scripts/bin/quality/hooks_run.sh

quality-docs-lint: ## Lint markdown docs, governance links, and make target references
	@python3 scripts/bin/quality/lint_docs.py

quality-docs-sync-core-targets: ## Regenerate tracked core Make targets reference doc
	@python3 scripts/bin/quality/render_core_targets_doc.py

quality-docs-check-core-targets-sync: ## Fail when tracked core Make targets doc is out of date
	@python3 scripts/bin/quality/render_core_targets_doc.py --check

quality-docs-sync-contract-metadata: ## Regenerate tracked contract metadata reference doc
	@python3 scripts/lib/docs/generate_contract_docs.py \
		--contract blueprint/contract.yaml \
		--modules-dir blueprint/modules \
		--output docs/reference/generated/contract_metadata.generated.md

quality-docs-check-contract-metadata-sync: ## Fail when tracked contract metadata doc is out of date
	@python3 scripts/lib/docs/generate_contract_docs.py \
		--contract blueprint/contract.yaml \
		--modules-dir blueprint/modules \
		--output docs/reference/generated/contract_metadata.generated.md \
		--check

quality-test-pyramid: ## Enforce repository test-pyramid ratios from canonical classification contract
	@python3 scripts/bin/quality/check_test_pyramid.py

infra-prereqs: ## Verify local prerequisites and optionally auto-install missing tools
	@scripts/bin/infra/prereqs.sh

infra-help-reference: ## Show full Make targets and variable defaults reference
	@scripts/bin/infra/help_reference.sh $(MAKEFILE_LIST)

infra-bootstrap: ## Bootstrap infra-only tooling/scaffolding
	@scripts/bin/infra/bootstrap.sh

infra-destroy-disabled-modules: ## Destroy resources for currently disabled optional modules
	@scripts/bin/infra/destroy_disabled_modules.sh

infra-validate: ## Validate infra contracts and manifests
	@scripts/bin/infra/validate.sh

infra-smoke: ## Infra smoke checks
	@scripts/bin/infra/smoke.sh

infra-provision: ## Provision infra only
	@scripts/bin/infra/provision.sh

infra-deploy: ## Deploy runtime/apps only
	@scripts/bin/infra/deploy.sh

infra-provision-deploy: ## Provision + deploy end-to-end
	@scripts/bin/infra/provision_deploy.sh

infra-stackit-bootstrap-preflight: ## Validate STACKIT bootstrap terraform inputs and path contract
	@scripts/bin/infra/stackit_bootstrap_preflight.sh

infra-stackit-bootstrap-plan: ## Plan STACKIT bootstrap terraform layer
	@scripts/bin/infra/stackit_bootstrap_plan.sh

infra-stackit-bootstrap-apply: ## Apply STACKIT bootstrap terraform layer
	@scripts/bin/infra/stackit_bootstrap_apply.sh

infra-stackit-bootstrap-destroy: ## Destroy STACKIT bootstrap terraform layer
	@scripts/bin/infra/stackit_bootstrap_destroy.sh

infra-stackit-foundation-preflight: ## Validate STACKIT foundation terraform inputs and path contract
	@scripts/bin/infra/stackit_foundation_preflight.sh

infra-stackit-foundation-plan: ## Plan STACKIT foundation terraform layer
	@scripts/bin/infra/stackit_foundation_plan.sh

infra-stackit-foundation-apply: ## Apply STACKIT foundation terraform layer
	@scripts/bin/infra/stackit_foundation_apply.sh

infra-stackit-foundation-destroy: ## Destroy STACKIT foundation terraform layer
	@scripts/bin/infra/stackit_foundation_destroy.sh

infra-stackit-foundation-fetch-kubeconfig: ## Fetch STACKIT foundation kubeconfig into local path
	@scripts/bin/infra/stackit_foundation_fetch_kubeconfig.sh

infra-stackit-foundation-refresh-kubeconfig: ## Refresh STACKIT foundation kubeconfig credentials and write local kubeconfig
	@scripts/bin/infra/stackit_foundation_refresh_kubeconfig.sh

infra-stackit-foundation-seed-runtime-secret: ## Seed runtime Kubernetes secret from STACKIT foundation outputs
	@scripts/bin/infra/stackit_foundation_seed_runtime_secret.sh

infra-stackit-ci-github-setup: ## Create GitHub environments/secrets required for STACKIT CI delivery
	@scripts/bin/infra/stackit_github_ci_setup.sh

infra-stackit-destroy-all: ## Destroy STACKIT foundation and bootstrap layers in canonical order
	@scripts/bin/infra/stackit_destroy_all.sh

infra-stackit-runtime-prerequisites: ## Validate STACKIT runtime prerequisites and kubeconfig availability
	@scripts/bin/infra/stackit_runtime_prerequisites.sh

infra-stackit-runtime-inventory: ## Print STACKIT runtime inventory from contract/state
	@scripts/bin/infra/stackit_runtime_inventory.sh

infra-stackit-runtime-deploy: ## Deploy STACKIT runtime control plane and apps path
	@scripts/bin/infra/stackit_runtime_deploy.sh

infra-stackit-smoke-foundation: ## Smoke-check STACKIT foundation readiness
	@scripts/bin/infra/stackit_smoke_foundation.sh

infra-stackit-smoke-runtime: ## Smoke-check STACKIT runtime convergence
	@scripts/bin/infra/stackit_smoke_runtime.sh

infra-stackit-provision-deploy: ## Run STACKIT provision+runtime deploy+smoke chain
	@scripts/bin/infra/stackit_provision_deploy.sh

infra-argocd-topology-render: ## Render ArgoCD base and environment topology manifests
	@scripts/bin/infra/argocd_topology_render.sh

infra-argocd-topology-validate: ## Validate ArgoCD base and environment topology manifests
	@scripts/bin/infra/argocd_topology_validate.sh

infra-doctor: ## Verify local tooling availability and contract preconditions
	@scripts/bin/infra/doctor.sh

infra-context: ## Print active Kubernetes context and profile routing metadata
	@scripts/bin/infra/context.sh

infra-status: ## Print compact runtime status from artifacts and current profile
	@scripts/bin/infra/status.sh

infra-status-json: ## Emit runtime status snapshot as JSON
	@scripts/bin/infra/status_json.sh



infra-audit-version: ## Audit infra dependencies/charts/images versions
	@scripts/bin/infra/audit_version.sh

infra-audit-version-cached: ## Audit infra dependencies/charts/images versions with local success cache
	@scripts/bin/infra/audit_version_cached.sh

docs-install: ## Install docs site dependencies
	@scripts/bin/docs/install.sh

docs-run: ## Run docs site locally
	@scripts/bin/docs/run.sh

docs-build: ## Build docs site
	@scripts/bin/docs/build.sh

docs-smoke: ## Smoke docs site output
	@scripts/bin/docs/smoke.sh
