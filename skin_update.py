"""Repository-local entry point for League skin version maintenance."""

from __future__ import annotations

import sys
from pathlib import Path


_SOURCE_ROOT = Path(__file__).resolve().parent / "src"
if str(_SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(_SOURCE_ROOT))

from league_skin_version import updater as _implementation  # noqa: E402


if __name__ == "__main__":
    _implementation.main()
else:
    sys.modules[__name__] = _implementation
