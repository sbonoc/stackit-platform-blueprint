from __future__ import annotations

from tests.blueprint.contract_refactor_groups import (
    BOOTSTRAP_SURFACE_CASES,
    build_split_case,
)


ContractBootstrapSurfaceTests = build_split_case(
    "ContractBootstrapSurfaceTests",
    BOOTSTRAP_SURFACE_CASES,
    __name__,
)
