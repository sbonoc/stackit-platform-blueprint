from __future__ import annotations

from tests.blueprint.contract_refactor_groups import (
    QUALITY_TOOLING_CASES,
    build_split_case,
)


ContractQualityToolingTests = build_split_case(
    "ContractQualityToolingTests",
    QUALITY_TOOLING_CASES,
    __name__,
)
