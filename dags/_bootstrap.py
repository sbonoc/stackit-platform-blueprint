"""Shared DAG bootstrap helpers for repository-root DAG entrypoints."""

from __future__ import annotations


def get_blueprint_context() -> dict[str, str]:
    """Return a minimal context contract consumed by DAG entrypoints."""
    return {
        "owner": "stackit-platform-blueprint",
        "bootstrap": "dags._bootstrap",
    }
