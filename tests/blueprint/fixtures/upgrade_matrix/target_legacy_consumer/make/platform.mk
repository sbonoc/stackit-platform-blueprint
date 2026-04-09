# Platform-owned Make targets.

.PHONY: apps-ci-bootstrap apps-ci-bootstrap-consumer infra-post-deploy-consumer

apps-ci-bootstrap:
	@$(MAKE) apps-ci-bootstrap-consumer

apps-ci-bootstrap-consumer:
	@echo consumer-ci-bootstrap-implemented

infra-post-deploy-consumer:
	@echo consumer-local-post-deploy-implemented
