#!/usr/bin/env python3
"""Generate semantic annotations for merge-required upgrade plan entries.

Analyses the diff between baseline content and upgrade source content using
static heuristics (no file execution). Returns a SemanticAnnotation describing
what changed and what the consumer should verify after merging.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any


# Closed-set kind values
KIND_FUNCTION_ADDED = "function-added"
KIND_FUNCTION_REMOVED = "function-removed"
KIND_VARIABLE_CHANGED = "variable-changed"
KIND_SOURCE_DIRECTIVE_ADDED = "source-directive-added"
KIND_STRUCTURAL_CHANGE = "structural-change"

_FUNC_DEF_RE = re.compile(
    r"^\s*(?:function\s+(\w+)|(\w+)\s*\(\s*\))",
    re.MULTILINE,
)
_VAR_ASSIGN_RE = re.compile(
    r"^\s*([A-Za-z_][A-Za-z0-9_]*)=(.*)",
    re.MULTILINE,
)
_SOURCE_RE = re.compile(
    r"^\s*(?:source|\.)\s+(\S+)",
    re.MULTILINE,
)


@dataclass(frozen=True)
class SemanticAnnotation:
    kind: str
    description: str
    verification_hints: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "description": self.description,
            "verification_hints": list(self.verification_hints),
        }


def _extract_functions(content: str) -> dict[str, str]:
    """Return {name: definition_line} for all shell function definitions in content."""
    result: dict[str, str] = {}
    for m in _FUNC_DEF_RE.finditer(content):
        name = m.group(1) or m.group(2)
        if name:
            result[name] = m.group(0).strip()
    return result


def _extract_vars(content: str) -> dict[str, str]:
    """Return {name: value} for all variable assignments in content."""
    result: dict[str, str] = {}
    for m in _VAR_ASSIGN_RE.finditer(content):
        result[m.group(1)] = m.group(2).strip()
    return result


def _extract_sources(content: str) -> set[str]:
    """Return set of source directive targets in content."""
    return {m.group(1) for m in _SOURCE_RE.finditer(content)}


def annotate(baseline_content: str, source_content: str) -> SemanticAnnotation:
    """Analyse the diff between baseline and source and return a SemanticAnnotation.

    Detection order (first match wins):
      1. function-added
      2. function-removed
      3. variable-changed
      4. source-directive-added
      5. structural-change (fallback)

    When baseline_content is empty (additive file with no ancestor), returns
    structural-change with an "additive file" description immediately.
    """
    if not baseline_content:
        return SemanticAnnotation(
            kind=KIND_STRUCTURAL_CHANGE,
            description="Additive file: no baseline ancestor exists for diff analysis.",
            verification_hints=(
                "Review the complete file and verify the merged result contains all expected content.",
            ),
        )

    baseline_funcs = _extract_functions(baseline_content)
    source_funcs = _extract_functions(source_content)

    # 1. function-added
    added = sorted(set(source_funcs) - set(baseline_funcs))
    if added:
        name = added[0]
        return SemanticAnnotation(
            kind=KIND_FUNCTION_ADDED,
            description=f"New shell function `{name}` added in upgrade source.",
            verification_hints=(
                f"Verify the function definition `{name}` is present in the merged result.",
                f"Verify `{name}` is callable from its call sites in the merged result.",
            ),
        )

    # 2. function-removed
    removed = sorted(set(baseline_funcs) - set(source_funcs))
    if removed:
        name = removed[0]
        return SemanticAnnotation(
            kind=KIND_FUNCTION_REMOVED,
            description=f"Shell function `{name}` removed in upgrade source.",
            verification_hints=(
                f"Verify no remaining call sites reference `{name}` in the merged result.",
            ),
        )

    # 3. variable-changed
    baseline_vars = _extract_vars(baseline_content)
    source_vars = _extract_vars(source_content)
    for var_name in sorted(source_vars):
        if var_name in baseline_vars and baseline_vars[var_name] != source_vars[var_name]:
            new_val = source_vars[var_name]
            return SemanticAnnotation(
                kind=KIND_VARIABLE_CHANGED,
                description=f"Variable `{var_name}` changed to `{new_val}` in upgrade source.",
                verification_hints=(
                    f"Verify `{var_name}` is set to `{new_val}` in the merged result.",
                ),
            )

    # 4. source-directive-added
    baseline_sources = _extract_sources(baseline_content)
    source_sources = _extract_sources(source_content)
    added_sources = sorted(source_sources - baseline_sources)
    if added_sources:
        target = added_sources[0]
        return SemanticAnnotation(
            kind=KIND_SOURCE_DIRECTIVE_ADDED,
            description=f"New `source` directive for `{target}` added in upgrade source.",
            verification_hints=(
                f"Verify the sourced file `{target}` exists and is reachable from the merged result.",
                f"Verify symbols from `{target}` referenced in the merged file are defined.",
            ),
        )

    # 5. structural-change fallback
    return SemanticAnnotation(
        kind=KIND_STRUCTURAL_CHANGE,
        description="Structural diff detected — no specific change pattern matched by annotator.",
        verification_hints=(
            "Manually review the diff between the baseline ref and the upgrade source.",
            "Verify the merged result is complete and correct before committing.",
        ),
    )
