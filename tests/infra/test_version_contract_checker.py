"""Tests for scripts/lib/platform/apps/version_contract_checker.py."""
from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tests._shared.helpers import REPO_ROOT

SCRIPT_PATH = REPO_ROOT / "scripts/lib/platform/apps/version_contract_checker.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("version_contract_checker", SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load module from {SCRIPT_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    return module


_m = _load_module()
parse_lock_file = _m.parse_lock_file
check_versions_lock = _m.check_versions_lock
check_manifest_yaml = _m.check_manifest_yaml
check_catalog_consistency = _m.check_catalog_consistency
LOCK_VAR_TO_MANIFEST_KEY = _m.LOCK_VAR_TO_MANIFEST_KEY


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write(tmpdir: str, name: str, content: str) -> Path:
    p = Path(tmpdir) / name
    p.write_text(content, encoding="utf-8")
    return p


SAMPLE_LOCK = (
    "PYTHON_RUNTIME_BASE_IMAGE_VERSION=3.13.9\n"
    "NODE_RUNTIME_BASE_IMAGE_VERSION=24.8.0\n"
    "NGINX_RUNTIME_BASE_IMAGE_VERSION=1.29.2\n"
    "FASTAPI_VERSION=0.117.1\n"
    "PYDANTIC_VERSION=2.11.10\n"
    "VUE_VERSION=3.5.31\n"
    "VUE_ROUTER_VERSION=5.0.4\n"
    "PINIA_VERSION=3.0.4\n"
    "APP_RUNTIME_GITOPS_ENABLED=true\n"
    "APP_RUNTIME_BACKEND_IMAGE=python:3.13.9\n"
    "APP_RUNTIME_TOUCHPOINTS_IMAGE=nginx:1.29.2\n"
)

SAMPLE_MANIFEST = (
    "schemaVersion: v1\n"
    "appVersionContract:\n"
    "  appVersionEnv: APP_VERSION\n"
    "runtimePinnedVersions:\n"
    "  python: 3.13.9\n"
    "  node: 24.8.0\n"
    "  nginx: 1.29.2\n"
    "frameworkPinnedVersions:\n"
    "  fastapi: 0.117.1\n"
    "  pydantic: 2.11.10\n"
    "  vue: 3.5.31\n"
    "  vue_router: 5.0.4\n"
    "  pinia: 3.0.4\n"
)

EXPECTED_VARS = {
    "PYTHON_RUNTIME_BASE_IMAGE_VERSION": "3.13.9",
    "NODE_RUNTIME_BASE_IMAGE_VERSION": "24.8.0",
    "NGINX_RUNTIME_BASE_IMAGE_VERSION": "1.29.2",
    "FASTAPI_VERSION": "0.117.1",
    "PYDANTIC_VERSION": "2.11.10",
    "VUE_VERSION": "3.5.31",
    "VUE_ROUTER_VERSION": "5.0.4",
    "PINIA_VERSION": "3.0.4",
}


# ---------------------------------------------------------------------------
# parse_lock_file
# ---------------------------------------------------------------------------

class ParseLockFileTests(unittest.TestCase):

    def test_parse_normal_lock_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            p = _write(tmpdir, "versions.lock", SAMPLE_LOCK)
            result = parse_lock_file(p)
        self.assertEqual(result["FASTAPI_VERSION"], "0.117.1")
        self.assertEqual(result["PYTHON_RUNTIME_BASE_IMAGE_VERSION"], "3.13.9")
        self.assertEqual(result["PINIA_VERSION"], "3.0.4")

    def test_missing_file_returns_empty_dict(self) -> None:
        result = parse_lock_file(Path("/nonexistent/path/versions.lock"))
        self.assertEqual(result, {})

    def test_empty_file_returns_empty_dict(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            p = _write(tmpdir, "versions.lock", "")
            result = parse_lock_file(p)
        self.assertEqual(result, {})


# ---------------------------------------------------------------------------
# check_versions_lock
# ---------------------------------------------------------------------------

class CheckVersionsLockTests(unittest.TestCase):

    def test_all_vars_match_returns_all_passed(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            lock = _write(tmpdir, "versions.lock", SAMPLE_LOCK)
            results = check_versions_lock(lock, EXPECTED_VARS)
        self.assertTrue(all(r.passed for r in results))
        self.assertEqual(len(results), len(EXPECTED_VARS))

    def test_single_var_mismatch_returns_failed_result(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            lock = _write(tmpdir, "versions.lock", SAMPLE_LOCK)
            results = check_versions_lock(lock, {"FASTAPI_VERSION": "99.99.99"})
        self.assertEqual(len(results), 1)
        self.assertFalse(results[0].passed)
        self.assertIn("FASTAPI_VERSION=99.99.99", results[0].expected_snippet)
        self.assertEqual(results[0].detail, "0.117.1")

    def test_var_missing_from_lock_returns_failed_with_not_found(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            lock = _write(tmpdir, "versions.lock", "PYTHON_RUNTIME_BASE_IMAGE_VERSION=3.13.9\n")
            results = check_versions_lock(lock, {"FASTAPI_VERSION": "0.117.1"})
        self.assertEqual(len(results), 1)
        self.assertFalse(results[0].passed)
        self.assertEqual(results[0].detail, "not found")

    def test_missing_lock_file_returns_skipped_passed(self) -> None:
        results = check_versions_lock(
            Path("/nonexistent/versions.lock"),
            {"FASTAPI_VERSION": "0.117.1"},
        )
        self.assertEqual(len(results), 1)
        self.assertTrue(results[0].passed)
        self.assertEqual(results[0].detail, "file-not-present")

    def test_extra_vars_in_lock_beyond_expected_are_ignored(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            lock = _write(tmpdir, "versions.lock", SAMPLE_LOCK + "EXTRA_VAR=whatever\n")
            results = check_versions_lock(lock, {"FASTAPI_VERSION": "0.117.1"})
        self.assertEqual(len(results), 1)
        self.assertTrue(results[0].passed)


# ---------------------------------------------------------------------------
# check_manifest_yaml
# ---------------------------------------------------------------------------

class CheckManifestYamlTests(unittest.TestCase):

    def test_all_vars_match_returns_all_passed(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            manifest = _write(tmpdir, "manifest.yaml", SAMPLE_MANIFEST)
            results = check_manifest_yaml(manifest, EXPECTED_VARS)
        self.assertTrue(all(r.passed for r in results))
        self.assertEqual(len(results), len(LOCK_VAR_TO_MANIFEST_KEY))

    def test_single_var_mismatch_returns_failed_result(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            manifest = _write(tmpdir, "manifest.yaml", SAMPLE_MANIFEST)
            results = check_manifest_yaml(manifest, {"FASTAPI_VERSION": "99.99.99"})
        self.assertEqual(len(results), 1)
        self.assertFalse(results[0].passed)
        self.assertIn("fastapi: 99.99.99", results[0].expected_snippet)
        self.assertEqual(results[0].detail, "0.117.1")

    def test_yaml_key_absent_from_manifest_returns_not_found(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            manifest = _write(tmpdir, "manifest.yaml", "schemaVersion: v1\n")
            results = check_manifest_yaml(manifest, {"FASTAPI_VERSION": "0.117.1"})
        self.assertEqual(len(results), 1)
        self.assertFalse(results[0].passed)
        self.assertEqual(results[0].detail, "not found")

    def test_missing_manifest_file_returns_skipped_passed(self) -> None:
        results = check_manifest_yaml(
            Path("/nonexistent/manifest.yaml"),
            {"FASTAPI_VERSION": "0.117.1"},
        )
        self.assertEqual(len(results), 1)
        self.assertTrue(results[0].passed)
        self.assertEqual(results[0].detail, "file-not-present")

    def test_var_without_manifest_key_mapping_is_skipped(self) -> None:
        """A var not in LOCK_VAR_TO_MANIFEST_KEY should produce no result."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manifest = _write(tmpdir, "manifest.yaml", SAMPLE_MANIFEST)
            results = check_manifest_yaml(manifest, {"UNKNOWN_VAR_XYZ": "1.0.0"})
        self.assertEqual(results, [])


# ---------------------------------------------------------------------------
# check_catalog_consistency
# ---------------------------------------------------------------------------

class CheckCatalogConsistencyTests(unittest.TestCase):

    def test_consistent_lock_and_manifest_returns_all_passed(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            lock = _write(tmpdir, "versions.lock", SAMPLE_LOCK)
            manifest = _write(tmpdir, "manifest.yaml", SAMPLE_MANIFEST)
            results = check_catalog_consistency(lock, manifest)
        self.assertTrue(all(r.passed for r in results), [r for r in results if not r.passed])

    def test_mismatch_between_lock_and_manifest_returns_failed(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            stale_lock = SAMPLE_LOCK.replace("FASTAPI_VERSION=0.117.1", "FASTAPI_VERSION=99.99.99")
            lock = _write(tmpdir, "versions.lock", stale_lock)
            manifest = _write(tmpdir, "manifest.yaml", SAMPLE_MANIFEST)
            results = check_catalog_consistency(lock, manifest)
        failed = [r for r in results if not r.passed]
        self.assertTrue(any("fastapi" in r.check_id for r in failed))

    def test_missing_lock_returns_single_failed_result(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            manifest = _write(tmpdir, "manifest.yaml", SAMPLE_MANIFEST)
            results = check_catalog_consistency(
                Path(tmpdir) / "nonexistent.lock",
                manifest,
            )
        self.assertEqual(len(results), 1)
        self.assertFalse(results[0].passed)
        self.assertIn("lock-missing", results[0].check_id)

    def test_missing_manifest_returns_single_failed_result(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            lock = _write(tmpdir, "versions.lock", SAMPLE_LOCK)
            results = check_catalog_consistency(
                lock,
                Path(tmpdir) / "nonexistent.yaml",
            )
        self.assertEqual(len(results), 1)
        self.assertFalse(results[0].passed)
        self.assertIn("manifest-missing", results[0].check_id)


# ---------------------------------------------------------------------------
# main() integration
# ---------------------------------------------------------------------------

class MainTests(unittest.TestCase):

    def test_catalog_check_mode_exits_zero_when_all_pass(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            lock = _write(tmpdir, "versions.lock", SAMPLE_LOCK)
            manifest = _write(tmpdir, "manifest.yaml", SAMPLE_MANIFEST)
            with mock.patch("sys.argv", [
                "version_contract_checker.py",
                "--mode", "catalog-check",
                "--versions-lock", str(lock),
                "--manifest", str(manifest),
                "--var", "FASTAPI_VERSION=0.117.1",
                "--var", "PYTHON_RUNTIME_BASE_IMAGE_VERSION=3.13.9",
            ]):
                result = _m.main()
        self.assertEqual(result, 0)

    def test_catalog_check_mode_exits_nonzero_when_lock_stale(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            stale_lock = SAMPLE_LOCK.replace("FASTAPI_VERSION=0.117.1", "FASTAPI_VERSION=0.0.1")
            lock = _write(tmpdir, "versions.lock", stale_lock)
            with mock.patch("sys.argv", [
                "version_contract_checker.py",
                "--mode", "catalog-check",
                "--versions-lock", str(lock),
                "--var", "FASTAPI_VERSION=0.117.1",
            ]):
                result = _m.main()
        self.assertNotEqual(result, 0)

    def test_consistency_mode_exits_zero_when_consistent(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            lock = _write(tmpdir, "versions.lock", SAMPLE_LOCK)
            manifest = _write(tmpdir, "manifest.yaml", SAMPLE_MANIFEST)
            with mock.patch("sys.argv", [
                "version_contract_checker.py",
                "--mode", "consistency",
                "--versions-lock", str(lock),
                "--manifest", str(manifest),
            ]):
                result = _m.main()
        self.assertEqual(result, 0)

    def test_consistency_mode_exits_nonzero_when_stale_lock(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            stale_lock = SAMPLE_LOCK.replace("FASTAPI_VERSION=0.117.1", "FASTAPI_VERSION=99.99.99")
            lock = _write(tmpdir, "versions.lock", stale_lock)
            manifest = _write(tmpdir, "manifest.yaml", SAMPLE_MANIFEST)
            with mock.patch("sys.argv", [
                "version_contract_checker.py",
                "--mode", "consistency",
                "--versions-lock", str(lock),
                "--manifest", str(manifest),
            ]):
                result = _m.main()
        self.assertNotEqual(result, 0)

    def test_catalog_check_mode_skips_when_catalog_files_absent(self) -> None:
        """When no catalog files exist, all checks are file-not-present (passed), exit 0."""
        with tempfile.TemporaryDirectory() as tmpdir:
            nonexistent_lock = Path(tmpdir) / "versions.lock"
            nonexistent_manifest = Path(tmpdir) / "manifest.yaml"
            with mock.patch("sys.argv", [
                "version_contract_checker.py",
                "--mode", "catalog-check",
                "--versions-lock", str(nonexistent_lock),
                "--manifest", str(nonexistent_manifest),
                "--var", "FASTAPI_VERSION=0.117.1",
            ]):
                result = _m.main()
        self.assertEqual(result, 0)


if __name__ == "__main__":
    unittest.main()
