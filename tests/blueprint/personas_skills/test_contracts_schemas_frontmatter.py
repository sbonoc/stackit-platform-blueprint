"""T-102 — front-matter + ## Required Output Schema parsing for new skills.

AC-003: Every new SKILL.md contains EXACTLY ONE ## Required Output Schema
        heading followed by EXACTLY ONE fenced ```yaml jsonschema``` block
        whose body parses as valid JSON Schema (draft-07 or later).
AC-004: Each of the 20 paths (10 personas + 10 new skills) appears as a row
        in `docs/blueprint/autonomous-factory/design-contracts.md` § Contract
        C8 § Category (c) with stability tier `stable`, extensibility tier
        `extensible`, and owning ticket `#333`.
AC-005: Every persona + every new SKILL.md carries blueprint-version
        front-matter matching the semver pattern.
"""

from __future__ import annotations

import re

import pytest
import yaml
from jsonschema import Draft7Validator

from tests.blueprint.personas_skills._roster import (
    NEW_SKILL_NAMES,
    PERSONA_NAMES,
    REPO_ROOT,
    new_skill_path,
    persona_path,
)

DESIGN_CONTRACTS = (
    REPO_ROOT / "docs" / "blueprint" / "autonomous-factory" / "design-contracts.md"
)
CATEGORY_C_HEADING_RE = re.compile(
    r"^###\s+Category\s+\(c\)[^\n]*$", re.MULTILINE
)
NEXT_SECTION_RE = re.compile(r"^###\s+", re.MULTILINE)

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


# -------- AC-004 — Contract C8 § Category (c) enumeration --------------------

def _category_c_block() -> str:
    text = DESIGN_CONTRACTS.read_text(encoding="utf-8")
    heading = CATEGORY_C_HEADING_RE.search(text)
    assert heading is not None, (
        "design-contracts.md MUST contain a '### Category (c)' heading"
    )
    start = heading.end()
    next_section = NEXT_SECTION_RE.search(text, pos=start)
    end = next_section.start() if next_section else len(text)
    return text[start:end]


_C8_PATHS: list[str] = (
    [f".agents/personas/{name}.md" for name in PERSONA_NAMES]
    + [f".agents/skills/{name}/" for name in NEW_SKILL_NAMES]
)


@pytest.mark.parametrize("surface_path", _C8_PATHS)
def test_category_c_row_present_with_stable_extensible_owned_by_333(
    surface_path: str,
) -> None:
    block = _category_c_block()
    matching_rows = [
        line for line in block.splitlines()
        if line.startswith("|") and f"`{surface_path}`" in line
    ]
    assert matching_rows, (
        f"design-contracts.md § Contract C8 § Category (c) MUST contain a row "
        f"for surface item `{surface_path}`"
    )
    row = matching_rows[0]
    assert "`stable`" in row, (
        f"row for `{surface_path}` MUST carry stability tier `stable`: {row!r}"
    )
    assert "`extensible`" in row, (
        f"row for `{surface_path}` MUST carry extensibility tier `extensible`: {row!r}"
    )
    assert "#333" in row, (
        f"row for `{surface_path}` MUST carry owning ticket `#333`: {row!r}"
    )
