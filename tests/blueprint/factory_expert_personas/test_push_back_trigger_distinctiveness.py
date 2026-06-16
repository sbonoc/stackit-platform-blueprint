"""Push-back trigger distinctiveness assertions (issue #364, FR-001).

FR-001 (authoring quality bar):
- each PERSONA.md MUST list at least 6 distinct trigger phrases in
  `## Push-back Triggers` (one phrase per markdown list item);
- the count of phrases that semantically overlap (case-insensitive
  substring match on the phrase head) with any other persona's
  Push-back Triggers section MUST NOT exceed 1.

The substring-overlap rule keeps the step02 dynamic-scope routing
algorithm (ADR-issue-364 § 4.2) substring-matchable without ambiguity.
"""

from __future__ import annotations

import re

import pytest

from tests.blueprint.factory_expert_personas._roster import (
    EXPERT_SLUGS,
    MAX_PAIRWISE_TRIGGER_OVERLAP,
    MIN_PUSH_BACK_TRIGGER_PHRASES,
    persona_path,
)

_PHRASE_HEAD_SPLIT = re.compile(r"[—:\.\;]| - ")


def _extract_trigger_phrases(slug: str) -> list[str]:
    body = persona_path(slug).read_text()
    in_section = False
    phrases: list[str] = []
    for raw in body.splitlines():
        line = raw.rstrip()
        if line.startswith("## Push-back Triggers"):
            in_section = True
            continue
        if in_section and line.startswith("## "):
            break
        if in_section and line.startswith("- "):
            item = line[2:].strip()
            head = _PHRASE_HEAD_SPLIT.split(item, maxsplit=1)[0].strip().lower()
            head = re.sub(r"\s+", " ", head)
            if head:
                phrases.append(head)
    return phrases


@pytest.mark.parametrize("slug", EXPERT_SLUGS)
def test_persona_has_minimum_distinct_trigger_phrases(slug: str) -> None:
    phrases = _extract_trigger_phrases(slug)
    distinct = set(phrases)
    assert len(distinct) >= MIN_PUSH_BACK_TRIGGER_PHRASES, (
        f"{slug}/PERSONA.md has only {len(distinct)} distinct push-back trigger "
        f"phrases; FR-001 requires at least {MIN_PUSH_BACK_TRIGGER_PHRASES} so the "
        f"step02 dynamic routing surface (ADR-issue-364 § 4.2) is not starved"
    )


def test_persona_trigger_phrases_have_bounded_pairwise_overlap() -> None:
    """For every pair of personas, the count of trigger phrases from persona A
    whose head appears as a case-insensitive substring of any trigger phrase
    head from persona B (or vice versa) MUST NOT exceed
    MAX_PAIRWISE_TRIGGER_OVERLAP. Stricter than per-persona collision counting:
    catches drift before it appears in only one of the pair.
    """
    by_slug: dict[str, list[str]] = {
        slug: _extract_trigger_phrases(slug) for slug in EXPERT_SLUGS
    }

    failures: list[str] = []
    slugs = sorted(by_slug)
    for i, a in enumerate(slugs):
        for b in slugs[i + 1 :]:
            phrases_a = by_slug[a]
            phrases_b = by_slug[b]
            overlap: list[tuple[str, str]] = []
            for pa in phrases_a:
                for pb in phrases_b:
                    if pa in pb or pb in pa:
                        overlap.append((pa, pb))
                        break
            if len(overlap) > MAX_PAIRWISE_TRIGGER_OVERLAP:
                failures.append(
                    f"{a} ↔ {b}: {len(overlap)} overlapping trigger phrases "
                    f"(max allowed = {MAX_PAIRWISE_TRIGGER_OVERLAP}); "
                    f"collisions: {overlap!r}"
                )

    assert not failures, (
        "FR-001 pairwise trigger-phrase overlap exceeded — step02 routing "
        "would become ambiguous between these expert pairs:\n  - "
        + "\n  - ".join(failures)
    )
