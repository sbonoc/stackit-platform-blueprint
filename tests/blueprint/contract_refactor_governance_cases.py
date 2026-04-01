from __future__ import annotations

from tests.blueprint.contract_refactor_governance_init_cases import GovernanceInitRepoCases
from tests.blueprint.contract_refactor_governance_runtime_cases import GovernanceRuntimePolicyCases
from tests.blueprint.contract_refactor_governance_structure_cases import GovernanceStructureCases
from tests.blueprint.contract_refactor_governance_version_cases import GovernanceVersionPolicyCases
from tests.blueprint.contract_refactor_shared import RefactorContractBase


class GovernanceRefactorCases(
    GovernanceStructureCases,
    GovernanceRuntimePolicyCases,
    GovernanceVersionPolicyCases,
    GovernanceInitRepoCases,
    RefactorContractBase,
):
    """Backwards-compatible aggregate over split governance contract suites."""
