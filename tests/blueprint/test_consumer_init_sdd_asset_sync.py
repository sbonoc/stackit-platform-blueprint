"""Regression: consumer-init SDD asset templates must stay in sync with their blueprint sources.

Catches the class of failure where a .spec-kit/templates/consumer/ or .spec-kit/control-catalog
file is updated without running sync_consumer_init_sdd_assets.py, which causes
quality-sdd-check-consumer-init-assets-sync to fail in CI while quality-hooks-fast passes locally.
"""

from __future__ import annotations

import subprocess
import sys
import unittest

from tests._shared.helpers import REPO_ROOT

SYNC_SCRIPT = REPO_ROOT / "scripts/lib/spec_kit/sync_consumer_init_sdd_assets.py"


class ConsumerInitSddAssetSyncTests(unittest.TestCase):
    def test_consumer_init_sdd_assets_in_sync(self) -> None:
        result = subprocess.run(
            [sys.executable, str(SYNC_SCRIPT), "--check"],
            capture_output=True,
            text=True,
        )
        self.assertEqual(
            result.returncode,
            0,
            msg=(
                "consumer-init SDD asset drift detected — run:\n"
                "  python3 scripts/lib/spec_kit/sync_consumer_init_sdd_assets.py\n\n"
                f"Drifted files:\n{result.stderr}"
            ),
        )


if __name__ == "__main__":
    unittest.main()
