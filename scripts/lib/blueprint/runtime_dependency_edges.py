#!/usr/bin/env python3
"""Canonical runtime dependency edges used by upgrade and validation flows."""

from __future__ import annotations

RUNTIME_DEPENDENCY_EDGES: tuple[tuple[str, str], ...] = (
    ("scripts/bin/infra/smoke.sh", "scripts/bin/platform/auth/reconcile_runtime_identity.sh"),
    (
        "scripts/bin/platform/auth/reconcile_runtime_identity.sh",
        "scripts/bin/platform/auth/reconcile_eso_runtime_secrets.sh",
    ),
    (
        "scripts/bin/platform/auth/reconcile_runtime_identity.sh",
        "scripts/bin/platform/auth/reconcile_argocd_repo_credentials.sh",
    ),
    (
        "scripts/bin/platform/auth/reconcile_argocd_repo_credentials.sh",
        "scripts/bin/platform/auth/reconcile_eso_runtime_secrets.sh",
    ),
)
