from __future__ import annotations

import sys
from pathlib import Path

# importmode=importlib (pytest.ini) does not inject rootdir into sys.path the
# way the legacy prepend mode did. Add it explicitly so that uninstalled source
# packages (scripts.*, tests._shared.*) remain importable regardless of how
# pytest is invoked (python -m pytest vs. the pytest script, cwd, absolute
# vs. relative test paths).
_ROOT = Path(__file__).parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
