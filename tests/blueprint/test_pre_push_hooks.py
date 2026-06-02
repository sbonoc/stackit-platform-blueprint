"""Blueprint pre-push hook assertions (issue #358).

Verify that all five pre-push hooks are present in the bootstrap template with
correct field values (T-101, T-102, T-103, T-104, T-108, T-109, AC-001–AC-007).
"""
from __future__ import annotations

import functools
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
TEMPLATE = REPO_ROOT / "scripts/templates/blueprint/bootstrap/.pre-commit-config.yaml"

_HOOK_IDS = frozenset(
    {
        "touchpoints-test-unit-pre-push",
        "touchpoints-test-contracts-pre-push",
        "backend-test-unit-pre-push",
        "backend-test-contracts-pre-push",
        "touchpoints-test-integration-pre-push",
    }
)


@functools.lru_cache(maxsize=None)
def _load_hooks() -> dict[str, dict]:
    """Return template hooks indexed by id, limited to the five we own."""
    config = yaml.safe_load(TEMPLATE.read_text(encoding="utf-8"))
    return {
        hook["id"]: hook
        for repo in config.get("repos", [])
        for hook in repo.get("hooks", [])
        if hook.get("id") in _HOOK_IDS
    }


class TestTouchpointsUnitPrePushHook:
    """T-101: touchpoints-test-unit-pre-push present with correct fields (AC-001)."""

    def test_hook_present(self) -> None:
        assert "touchpoints-test-unit-pre-push" in _load_hooks(), (
            "touchpoints-test-unit-pre-push hook not found in template"
        )

    def test_name(self) -> None:
        hook = _load_hooks().get("touchpoints-test-unit-pre-push", {})
        assert hook.get("name") == "touchpoints unit tests (pre-push)"

    def test_language(self) -> None:
        hook = _load_hooks().get("touchpoints-test-unit-pre-push", {})
        assert hook.get("language") == "system"

    def test_entry(self) -> None:
        hook = _load_hooks().get("touchpoints-test-unit-pre-push", {})
        assert hook.get("entry") == "make touchpoints-test-unit"

    def test_pass_filenames(self) -> None:
        hook = _load_hooks().get("touchpoints-test-unit-pre-push", {})
        assert hook.get("pass_filenames") is False

    def test_stages(self) -> None:
        hook = _load_hooks().get("touchpoints-test-unit-pre-push", {})
        assert hook.get("stages") == ["pre-push"]

    def test_files_pattern(self) -> None:
        hook = _load_hooks().get("touchpoints-test-unit-pre-push", {})
        assert hook.get("files") == r"^apps/touchpoints/.*\.(ts|vue|tsx)$"

    def test_always_run(self) -> None:
        hook = _load_hooks().get("touchpoints-test-unit-pre-push", {})
        assert hook.get("always_run") is False


class TestTouchpointsContractsPrePushHook:
    """T-102: touchpoints-test-contracts-pre-push present with correct fields (AC-002)."""

    def test_hook_present(self) -> None:
        assert "touchpoints-test-contracts-pre-push" in _load_hooks(), (
            "touchpoints-test-contracts-pre-push hook not found in template"
        )

    def test_name(self) -> None:
        hook = _load_hooks().get("touchpoints-test-contracts-pre-push", {})
        assert hook.get("name") == "touchpoints contract tests (pre-push)"

    def test_language(self) -> None:
        hook = _load_hooks().get("touchpoints-test-contracts-pre-push", {})
        assert hook.get("language") == "system"

    def test_entry(self) -> None:
        hook = _load_hooks().get("touchpoints-test-contracts-pre-push", {})
        assert hook.get("entry") == "make touchpoints-test-contracts"

    def test_pass_filenames(self) -> None:
        hook = _load_hooks().get("touchpoints-test-contracts-pre-push", {})
        assert hook.get("pass_filenames") is False

    def test_stages(self) -> None:
        hook = _load_hooks().get("touchpoints-test-contracts-pre-push", {})
        assert hook.get("stages") == ["pre-push"]

    def test_files_pattern(self) -> None:
        hook = _load_hooks().get("touchpoints-test-contracts-pre-push", {})
        assert hook.get("files") == r"^(apps/touchpoints/.*\.(ts|vue|tsx)|apps/packages/api-client/src/.*\.ts|tests/touchpoints/contracts/.*\.py)$"

    def test_files_pattern_covers_api_client(self) -> None:
        hook = _load_hooks().get("touchpoints-test-contracts-pre-push", {})
        assert "apps/packages/api-client/src/" in hook.get("files", ""), (
            "files pattern must cover api-client source changes (FR-002)"
        )

    def test_files_pattern_covers_pytest_contracts(self) -> None:
        hook = _load_hooks().get("touchpoints-test-contracts-pre-push", {})
        assert "tests/touchpoints/contracts/" in hook.get("files", ""), (
            "files pattern must cover tests/touchpoints/contracts/*.py — make touchpoints-test-contracts runs a pytest lane there (FR-002)"
        )

    def test_always_run(self) -> None:
        hook = _load_hooks().get("touchpoints-test-contracts-pre-push", {})
        assert hook.get("always_run") is False


class TestBackendUnitPrePushHook:
    """T-103: backend-test-unit-pre-push present with correct fields (AC-003)."""

    def test_hook_present(self) -> None:
        assert "backend-test-unit-pre-push" in _load_hooks(), (
            "backend-test-unit-pre-push hook not found in template"
        )

    def test_name(self) -> None:
        hook = _load_hooks().get("backend-test-unit-pre-push", {})
        assert hook.get("name") == "backend unit tests (pre-push)"

    def test_language(self) -> None:
        hook = _load_hooks().get("backend-test-unit-pre-push", {})
        assert hook.get("language") == "system"

    def test_entry(self) -> None:
        hook = _load_hooks().get("backend-test-unit-pre-push", {})
        assert hook.get("entry") == "make backend-test-unit"

    def test_pass_filenames(self) -> None:
        hook = _load_hooks().get("backend-test-unit-pre-push", {})
        assert hook.get("pass_filenames") is False

    def test_stages(self) -> None:
        hook = _load_hooks().get("backend-test-unit-pre-push", {})
        assert hook.get("stages") == ["pre-push"]

    def test_files_pattern(self) -> None:
        hook = _load_hooks().get("backend-test-unit-pre-push", {})
        assert hook.get("files") == r"^(apps/backend/|tests/backend/).*\.py$"

    def test_always_run(self) -> None:
        hook = _load_hooks().get("backend-test-unit-pre-push", {})
        assert hook.get("always_run") is False


class TestBackendContractsPrePushHook:
    """T-108: backend-test-contracts-pre-push present with correct fields (AC-006)."""

    def test_hook_present(self) -> None:
        assert "backend-test-contracts-pre-push" in _load_hooks(), (
            "backend-test-contracts-pre-push hook not found in template"
        )

    def test_name(self) -> None:
        hook = _load_hooks().get("backend-test-contracts-pre-push", {})
        assert hook.get("name") == "backend contract tests (pre-push)"

    def test_language(self) -> None:
        hook = _load_hooks().get("backend-test-contracts-pre-push", {})
        assert hook.get("language") == "system"

    def test_entry(self) -> None:
        hook = _load_hooks().get("backend-test-contracts-pre-push", {})
        assert hook.get("entry") == "make backend-test-contracts"

    def test_pass_filenames(self) -> None:
        hook = _load_hooks().get("backend-test-contracts-pre-push", {})
        assert hook.get("pass_filenames") is False

    def test_stages(self) -> None:
        hook = _load_hooks().get("backend-test-contracts-pre-push", {})
        assert hook.get("stages") == ["pre-push"]

    def test_files_pattern(self) -> None:
        hook = _load_hooks().get("backend-test-contracts-pre-push", {})
        assert hook.get("files") == r"^(apps/backend/|tests/backend/).*\.py$"

    def test_always_run(self) -> None:
        hook = _load_hooks().get("backend-test-contracts-pre-push", {})
        assert hook.get("always_run") is False


class TestTouchpointsIntegrationPrePushHook:
    """T-109: touchpoints-test-integration-pre-push present with correct fields (AC-007)."""

    def test_hook_present(self) -> None:
        assert "touchpoints-test-integration-pre-push" in _load_hooks(), (
            "touchpoints-test-integration-pre-push hook not found in template"
        )

    def test_name(self) -> None:
        hook = _load_hooks().get("touchpoints-test-integration-pre-push", {})
        assert hook.get("name") == "touchpoints integration tests (pre-push)"

    def test_language(self) -> None:
        hook = _load_hooks().get("touchpoints-test-integration-pre-push", {})
        assert hook.get("language") == "system"

    def test_entry(self) -> None:
        hook = _load_hooks().get("touchpoints-test-integration-pre-push", {})
        assert hook.get("entry") == "make touchpoints-test-integration"

    def test_pass_filenames(self) -> None:
        hook = _load_hooks().get("touchpoints-test-integration-pre-push", {})
        assert hook.get("pass_filenames") is False

    def test_stages(self) -> None:
        hook = _load_hooks().get("touchpoints-test-integration-pre-push", {})
        assert hook.get("stages") == ["pre-push"]

    def test_files_pattern(self) -> None:
        hook = _load_hooks().get("touchpoints-test-integration-pre-push", {})
        assert hook.get("files") == r"^(apps/touchpoints/.*\.(ts|vue|tsx)|apps/packages/api-client/src/.*\.ts)$"

    def test_files_pattern_covers_api_client(self) -> None:
        hook = _load_hooks().get("touchpoints-test-integration-pre-push", {})
        assert "apps/packages/api-client/src/" in hook.get("files", ""), (
            "files pattern must cover api-client source changes (FR-007)"
        )

    def test_always_run(self) -> None:
        hook = _load_hooks().get("touchpoints-test-integration-pre-push", {})
        assert hook.get("always_run") is False


class TestAllHooksNoBehaviourAtCommitStage:
    """T-104: no hook fires at commit stage — always_run: false + stages: [pre-push] only (AC-004)."""

    def test_touchpoints_unit_always_run_false(self) -> None:
        hooks = _load_hooks()
        assert hooks.get("touchpoints-test-unit-pre-push", {}).get("always_run") is False

    def test_touchpoints_unit_stages_pre_push_only(self) -> None:
        hooks = _load_hooks()
        assert hooks.get("touchpoints-test-unit-pre-push", {}).get("stages") == ["pre-push"]

    def test_touchpoints_contracts_always_run_false(self) -> None:
        hooks = _load_hooks()
        assert hooks.get("touchpoints-test-contracts-pre-push", {}).get("always_run") is False

    def test_touchpoints_contracts_stages_pre_push_only(self) -> None:
        hooks = _load_hooks()
        assert hooks.get("touchpoints-test-contracts-pre-push", {}).get("stages") == ["pre-push"]

    def test_backend_unit_always_run_false(self) -> None:
        hooks = _load_hooks()
        assert hooks.get("backend-test-unit-pre-push", {}).get("always_run") is False

    def test_backend_unit_stages_pre_push_only(self) -> None:
        hooks = _load_hooks()
        assert hooks.get("backend-test-unit-pre-push", {}).get("stages") == ["pre-push"]

    def test_backend_contracts_always_run_false(self) -> None:
        hooks = _load_hooks()
        assert hooks.get("backend-test-contracts-pre-push", {}).get("always_run") is False

    def test_backend_contracts_stages_pre_push_only(self) -> None:
        hooks = _load_hooks()
        assert hooks.get("backend-test-contracts-pre-push", {}).get("stages") == ["pre-push"]

    def test_touchpoints_integration_always_run_false(self) -> None:
        hooks = _load_hooks()
        assert hooks.get("touchpoints-test-integration-pre-push", {}).get("always_run") is False

    def test_touchpoints_integration_stages_pre_push_only(self) -> None:
        hooks = _load_hooks()
        assert hooks.get("touchpoints-test-integration-pre-push", {}).get("stages") == ["pre-push"]
