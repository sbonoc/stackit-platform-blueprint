"""T-110 — existing 8 SDD skill `SKILL.md` files backfilled with
`## Required Output Schema` + `blueprint-version` front-matter (FR-020).

AC-017: Each of the 8 existing skill SKILL.md files contains EXACTLY ONE
        `## Required Output Schema` heading followed by EXACTLY ONE fenced
        ```yaml jsonschema``` block parsing as valid JSON Schema
        (draft-07 or later); AND each file's YAML front-matter contains a
        `blueprint-version` key matching the semver pattern.
"""

from __future__ import annotations

import re

import pytest
import yaml
from jsonschema import Draft7Validator

from tests.blueprint.personas_skills._roster import (
    EXISTING_SDD_SKILL_NAMES,
    existing_skill_path,
)
from tests.blueprint.personas_skills.test_contracts_schemas_frontmatter import (
    REQUIRED_OUTPUT_SCHEMA_RE,
    SEMVER_RE,
    YAML_JSONSCHEMA_FENCE_RE,
)

FRONT_MATTER_RE = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)


def _front_matter(text: str) -> dict:
    match = FRONT_MATTER_RE.match(text)
    assert match is not None, "file is missing YAML front-matter"
    loaded = yaml.safe_load(match.group(1))
    assert isinstance(loaded, dict), "front-matter MUST be a YAML mapping"
    return loaded


@pytest.mark.parametrize("name", EXISTING_SDD_SKILL_NAMES)
def test_existing_skill_has_exactly_one_required_output_schema_heading(name: str) -> None:
    text = existing_skill_path(name).read_text(encoding="utf-8")
    matches = REQUIRED_OUTPUT_SCHEMA_RE.findall(text)
    assert len(matches) == 1, (
        f"{name}: expected EXACTLY ONE '## Required Output Schema' heading, "
        f"got {len(matches)}"
    )


@pytest.mark.parametrize("name", EXISTING_SDD_SKILL_NAMES)
def test_existing_skill_has_exactly_one_yaml_jsonschema_fence(name: str) -> None:
    text = existing_skill_path(name).read_text(encoding="utf-8")
    blocks = YAML_JSONSCHEMA_FENCE_RE.findall(text)
    assert len(blocks) == 1, (
        f"{name}: expected EXACTLY ONE ```yaml jsonschema``` fenced block, "
        f"got {len(blocks)}"
    )


@pytest.mark.parametrize("name", EXISTING_SDD_SKILL_NAMES)
def test_existing_skill_yaml_jsonschema_parses_as_valid_json_schema(name: str) -> None:
    text = existing_skill_path(name).read_text(encoding="utf-8")
    blocks = YAML_JSONSCHEMA_FENCE_RE.findall(text)
    assert blocks, f"{name}: ```yaml jsonschema``` fenced block missing"
    schema = yaml.safe_load(blocks[0])
    assert isinstance(schema, dict), (
        f"{name}: ```yaml jsonschema``` body MUST be a YAML mapping"
    )
    Draft7Validator.check_schema(schema)


@pytest.mark.parametrize("name", EXISTING_SDD_SKILL_NAMES)
def test_existing_skill_front_matter_has_blueprint_version_semver(name: str) -> None:
    fm = _front_matter(existing_skill_path(name).read_text(encoding="utf-8"))
    assert "blueprint-version" in fm, (
        f"{name}: existing skill front-matter missing blueprint-version key"
    )
    value = fm["blueprint-version"]
    assert isinstance(value, str) and SEMVER_RE.match(value), (
        f"{name}: blueprint-version {value!r} does not match semver pattern"
    )
