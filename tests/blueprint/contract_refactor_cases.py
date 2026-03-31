from __future__ import annotations

from tests.blueprint.contract_refactor_docs_cases import DocsRefactorCases
from tests.blueprint.contract_refactor_governance_cases import GovernanceRefactorCases
from tests.blueprint.contract_refactor_make_cases import MakeRefactorCases
from tests.blueprint.contract_refactor_runtime_identity_cases import RuntimeIdentityRefactorCases
from tests.blueprint.contract_refactor_scripts_cases import ScriptsRefactorCases
from tests.blueprint.contract_refactor_shared import RefactorContractBase


class RefactorContractsTests(
    GovernanceRefactorCases,
    DocsRefactorCases,
    MakeRefactorCases,
    ScriptsRefactorCases,
    RuntimeIdentityRefactorCases,
    RefactorContractBase,
):
    """Backwards-compatible aggregate over focused contract test suites."""
