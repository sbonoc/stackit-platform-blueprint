"""T-102 — front-matter + ## Required Output Schema parsing for new skills.

AC-003: Every new SKILL.md contains EXACTLY ONE ## Required Output Schema
        heading followed by EXACTLY ONE fenced ```yaml jsonschema``` block
        whose body parses as valid JSON Schema (draft-07 or later).
AC-005: Every persona + every new SKILL.md carries blueprint-version
        front-matter matching the semver pattern.

AC-004 (Contract C8 enumeration) is added in slice 4.
"""

from __future__ import annotations

import re

import pytest
import yaml
from jsonschema import Draft7Validator

from tests.blueprint.personas_skills._roster import (
    NEW_SKILL_NAMES,
    PERSONA_NAMES,
    new_skill_path,
    persona_path,
)

SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+(-[\w.]+)?$")

FRONT_MATTER_RE = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)
REQUIRED_OUTPUT_SCHEMA_RE = re.compile(
    r"^## Required Output Schema\s*$", re.MULTILINE
)
YAML_JSONSCHEMA_FENCE_RE = re.compile(
    r"```yaml jsonschema\n(.*?)\n```", re.DOTALL
)


def _front_matter(text: str) -> dict:
    match = FRONT_MATTER_RE.match(text)
    assert match is not None, "file is missing YAML front-matter"
    loaded = yaml.safe_load(match.group(1))
    assert isinstance(loaded, dict), "front-matter MUST be a YAML mapping"
    return loaded


# -------- AC-005 — blueprint-version semver front-matter on all 20 new files --

@pytest.mark.parametrize("name", PERSONA_NAMES)
def test_persona_front_matter_has_blueprint_version_semver(name: str) -> None:
    fm = _front_matter(persona_path(name).read_text(encoding="utf-8"))
    assert "blueprint-version" in fm, (
        f"{name}: persona front-matter missing blueprint-version key"
    )
    value = fm["blueprint-version"]
    assert isinstance(value, str) and SEMVER_RE.match(value), (
        f"{name}: blueprint-version {value!r} does not match semver pattern"
    )


@pytest.mark.parametrize("name", NEW_SKILL_NAMES)
def test_new_skill_front_matter_has_blueprint_version_semver(name: str) -> None:
    fm = _front_matter(new_skill_path(name).read_text(encoding="utf-8"))
    assert "blueprint-version" in fm, (
        f"{name}: skill front-matter missing blueprint-version key"
    )
    value = fm["blueprint-version"]
    assert isinstance(value, str) and SEMVER_RE.match(value), (
        f"{name}: blueprint-version {value!r} does not match semver pattern"
    )


# -------- AC-003 — Required Output Schema on every new SKILL.md ---------------

@pytest.mark.parametrize("name", NEW_SKILL_NAMES)
def test_new_skill_has_exactly_one_required_output_schema_heading(name: str) -> None:
    text = new_skill_path(name).read_text(encoding="utf-8")
    matches = REQUIRED_OUTPUT_SCHEMA_RE.findall(text)
    assert len(matches) == 1, (
        f"{name}: expected EXACTLY ONE '## Required Output Schema' heading, "
        f"got {len(matches)}"
    )


@pytest.mark.parametrize("name", NEW_SKILL_NAMES)
def test_new_skill_has_exactly_one_yaml_jsonschema_fence(name: str) -> None:
    text = new_skill_path(name).read_text(encoding="utf-8")
    blocks = YAML_JSONSCHEMA_FENCE_RE.findall(text)
    assert len(blocks) == 1, (
        f"{name}: expected EXACTLY ONE ```yaml jsonschema``` fenced block, "
        f"got {len(blocks)}"
    )


@pytest.mark.parametrize("name", NEW_SKILL_NAMES)
def test_new_skill_yaml_jsonschema_body_parses_as_valid_json_schema(name: str) -> None:
    text = new_skill_path(name).read_text(encoding="utf-8")
    blocks = YAML_JSONSCHEMA_FENCE_RE.findall(text)
    assert blocks, f"{name}: ```yaml jsonschema``` fenced block missing"
    schema = yaml.safe_load(blocks[0])
    assert isinstance(schema, dict), (
        f"{name}: ```yaml jsonschema``` body MUST be a YAML mapping"
    )
    # Validate the schema itself against the Draft 7 meta-schema.
    Draft7Validator.check_schema(schema)
