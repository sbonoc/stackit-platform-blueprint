from __future__ import annotations

from tests.blueprint.contract_refactor_groups import (
    STACKIT_RUNTIME_CASES,
    build_split_case,
)


ContractStackitRuntimeTests = build_split_case(
    "ContractStackitRuntimeTests",
    STACKIT_RUNTIME_CASES,
    __name__,
)
