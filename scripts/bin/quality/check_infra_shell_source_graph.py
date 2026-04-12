#!/usr/bin/env python3
"""Generate and validate infra shell source-edge dependency graph."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
import sys


REPO_ROOT = Path(__file__).resolve().parents[3]
INFRA_LIB_DIR = REPO_ROOT / "scripts" / "lib" / "infra"
SOURCE_EDGE_RE = re.compile(r'^\s*source\s+"\$ROOT_DIR/scripts/lib/infra/([^"]+)"\s*$', re.MULTILINE)

# Contract-critical edges: helpers that are frequently sourced transitively
# must declare their direct dependencies explicitly to avoid caller-side
# implicit sourcing drift.
REQUIRED_SOURCE_EDGES: dict[str, set[str]] = {
    "fallback_runtime.sh": {"tooling.sh"},
    "public_endpoints.sh": {"fallback_runtime.sh", "tooling.sh"},
    "keycloak_identity_contract.sh": {"tooling.sh"},
    "identity_aware_proxy.sh": {"fallback_runtime.sh"},
    "postgres.sh": {"fallback_runtime.sh"},
    "object_storage.sh": {"fallback_runtime.sh"},
    "rabbitmq.sh": {"fallback_runtime.sh"},
}


@dataclass(frozen=True)
class Violation:
    file_name: str
    message: str


def _source_graph() -> dict[str, set[str]]:
    graph: dict[str, set[str]] = {}
    for path in sorted(INFRA_LIB_DIR.glob("*.sh")):
        graph[path.name] = set(SOURCE_EDGE_RE.findall(path.read_text(encoding="utf-8")))
    return graph


def _validate_required_edges(graph: dict[str, set[str]]) -> list[Violation]:
    violations: list[Violation] = []
    known_files = set(graph)
    for file_name, required_sources in sorted(REQUIRED_SOURCE_EDGES.items()):
        if file_name not in known_files:
            violations.append(Violation(file_name=file_name, message="required file not found in scripts/lib/infra"))
            continue
        for source_file in sorted(required_sources):
            if source_file not in known_files:
                violations.append(
                    Violation(
                        file_name=file_name,
                        message=f"required source target missing from infra library set: {source_file}",
                    )
                )
                continue
            if source_file not in graph[file_name]:
                violations.append(
                    Violation(
                        file_name=file_name,
                        message=f"missing explicit source edge to {source_file}",
                    )
                )
    return violations


def main() -> int:
    graph = _source_graph()
    edge_count = sum(len(edges) for edges in graph.values())
    violations = _validate_required_edges(graph)

    if violations:
        for violation in violations:
            print(
                f"[quality-infra-shell-source-graph-check] {violation.file_name}: {violation.message}",
                file=sys.stderr,
            )
        return 1

    print(
        "[quality-infra-shell-source-graph-check] "
        f"validated scripts/lib/infra source graph nodes={len(graph)} edges={edge_count}",
        file=sys.stdout,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
