"""Backward-compatible launcher: `python yt.py` from the repo root."""

from __future__ import annotations

import sys
from pathlib import Path

# Allow running without `pip install` when executed from the repository root.
_root = Path(__file__).resolve().parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from yt.cli import main

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
