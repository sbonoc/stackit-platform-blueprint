from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


# Load the validate_contract module from its bin path (no package __init__.py).
_REPO_ROOT = Path(__file__).resolve().parents[2]
_VALIDATE_CONTRACT_PATH = _REPO_ROOT / "scripts/bin/blueprint/validate_contract.py"

_spec = importlib.util.spec_from_file_location("validate_contract", _VALIDATE_CONTRACT_PATH)
assert _spec is not None and _spec.loader is not None
_validate_contract_mod = importlib.util.module_from_spec(_spec)
sys.modules.setdefault("validate_contract", _validate_contract_mod)
_spec.loader.exec_module(_validate_contract_mod)  # type: ignore[union-attr]

_validate_absent_files = _validate_contract_mod._validate_absent_files  # type: ignore[attr-defined]


class TestValidateAbsentFiles(unittest.TestCase):
    """FR-002/FR-003 / AC-002–AC-005: _validate_absent_files classification."""

    def _make_consumer(self, files: dict[str, str]) -> Path:
        tmp = Path(tempfile.mkdtemp())
        for rel, content in files.items():
            p = tmp / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(content, encoding="utf-8")
        return tmp

    def test_validate_absent_files_directory_entry(self) -> None:
        """AC-002: a directory-prefix entry (trailing /) must NOT trigger an absent-file error.

        Reproduces #215: .exists() returns True for directories, causing a false positive.
        With the fix (.is_file()), a directory at the path is not a file → no error.
        """
        consumer = self._make_consumer({})
        # Create an actual directory at the path referenced by source_only.
        adr_dir = consumer / "docs/blueprint/architecture/decisions"
        adr_dir.mkdir(parents=True, exist_ok=True)

        errors = _validate_absent_files(
            consumer,
            ["docs/blueprint/architecture/decisions/"],
        )
        self.assertEqual(errors, [], msg="directory-prefix entry must not trigger absent-file error")

    def test_validate_absent_files_glob_matching(self) -> None:
        """AC-003: a glob entry must produce an error for each matching file present in consumer."""
        consumer = self._make_consumer(
            {"docs/blueprint/architecture/decisions/ADR-001-test.md": "# ADR\n"}
        )

        errors = _validate_absent_files(
            consumer,
            ["docs/blueprint/architecture/decisions/ADR-*.md"],
        )
        self.assertTrue(
            len(errors) > 0,
            msg="glob entry matching a present file must produce at least one error",
        )
        self.assertTrue(
            any("ADR-001-test.md" in e for e in errors),
            msg="error must mention the matched file path",
        )

    def test_validate_absent_files_glob_no_match(self) -> None:
        """AC-004: a glob entry with no matching files must produce no error."""
        consumer = self._make_consumer(
            {"docs/blueprint/architecture/decisions/NOTES.md": "# notes\n"}
        )

        errors = _validate_absent_files(
            consumer,
            ["docs/blueprint/architecture/decisions/ADR-*.md"],
        )
        self.assertEqual(errors, [], msg="glob entry with no match must produce no error")

    def test_validate_absent_files_exact_file_present(self) -> None:
        """AC-005: backward-compat — exact file entry with a present file must produce an error."""
        consumer = self._make_consumer({"some-file.yaml": "key: value\n"})

        errors = _validate_absent_files(consumer, ["some-file.yaml"])
        self.assertTrue(
            len(errors) > 0,
            msg="exact file entry with a present file must produce an error",
        )


if __name__ == "__main__":
    unittest.main()
