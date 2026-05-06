#!/usr/bin/env bash
set -euo pipefail

# Canonical pinned versions for infra and platform dependencies.
TERRAFORM_VERSION="1.13.3"
HELM_VERSION="4.1.3"
KUBECTL_VERSION="1.34.1"
KIND_VERSION="0.30.0"
EXTERNAL_SECRETS_CHART_VERSION="2.2.0"
CERT_MANAGER_CHART_VERSION="v1.20.1"
ARGOCD_CHART_VERSION="9.4.16"
CROSSPLANE_CHART_VERSION="2.2.0"
OTEL_COLLECTOR_CHART_VERSION="0.147.1"
GRAFANA_CHART_VERSION="9.5.4"
LOKI_CHART_VERSION="6.41.0"
TEMPO_CHART_VERSION="1.23.2"

# Optional-module local chart pins live here too so version drift stays
# contract-driven and `infra-audit-version` has one canonical source.
POSTGRES_HELM_CHART_VERSION_PIN="15.5.38"
OBJECT_STORAGE_HELM_CHART_VERSION_PIN="17.0.21"
RABBITMQ_HELM_CHART_VERSION_PIN="15.5.3"
OPENSEARCH_HELM_CHART_VERSION_PIN="2.28.3"
NEO4J_HELM_CHART_VERSION_PIN="2026.1.4"
PUBLIC_ENDPOINTS_HELM_CHART_VERSION_PIN="1.7.1"
IAP_HELM_CHART_VERSION_PIN="10.4.0"
KEYCLOAK_HELM_CHART_VERSION_PIN="7.1.9"
KEYCLOAK_IMAGE_TAG_PIN="26.5.5"

# Local fallback images are pinned explicitly because upstream chart defaults
# may drift to retired registry tags. Where STACKIT exposes a managed service
# version contract, the local image line follows that same version family.
# Bitnami publishes some current multi-arch tags under the `bitnamilegacy/*`
# namespace; treat that as a vendor naming quirk, not as approval to use
# unsupported runtime versions.
POSTGRES_LOCAL_IMAGE_REGISTRY="docker.io"
POSTGRES_LOCAL_IMAGE_REPOSITORY="bitnamilegacy/postgresql"
POSTGRES_LOCAL_IMAGE_TAG="16.4.0-debian-12-r14"
OBJECT_STORAGE_LOCAL_IMAGE_REGISTRY="docker.io"
OBJECT_STORAGE_LOCAL_IMAGE_REPOSITORY="bitnamilegacy/minio"
OBJECT_STORAGE_LOCAL_IMAGE_TAG="2025.7.23-debian-12-r3"
OBJECT_STORAGE_LOCAL_CLIENT_IMAGE_REGISTRY="docker.io"
OBJECT_STORAGE_LOCAL_CLIENT_IMAGE_REPOSITORY="bitnamilegacy/minio-client"
OBJECT_STORAGE_LOCAL_CLIENT_IMAGE_TAG="2025.7.21-debian-12-r2"
RABBITMQ_LOCAL_IMAGE_REGISTRY="docker.io"
RABBITMQ_LOCAL_IMAGE_REPOSITORY="bitnamilegacy/rabbitmq"
RABBITMQ_LOCAL_IMAGE_TAG="4.0.9-debian-12-r1"
OPENSEARCH_LOCAL_IMAGE_REGISTRY="docker.io"
OPENSEARCH_LOCAL_IMAGE_REPOSITORY="bitnamilegacy/opensearch"
OPENSEARCH_LOCAL_IMAGE_TAG="2.17.1-debian-12-r0"
IAP_LOCAL_IMAGE_REGISTRY="quay.io"
IAP_LOCAL_IMAGE_REPOSITORY="oauth2-proxy/oauth2-proxy"
IAP_LOCAL_IMAGE_TAG="v7.15.0"
