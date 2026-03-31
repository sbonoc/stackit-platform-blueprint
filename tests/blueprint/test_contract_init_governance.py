from __future__ import annotations

from tests.blueprint.contract_refactor_groups import (
    INIT_GOVERNANCE_CASES,
    build_split_case,
)


ContractInitGovernanceTests = build_split_case(
    "ContractInitGovernanceTests",
    INIT_GOVERNANCE_CASES,
    __name__,
)
