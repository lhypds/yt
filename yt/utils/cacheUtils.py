"""Cache directory helpers for the yt CLI.

All generated artifacts (.mp4, .srt, .txt, .summary.md) live under a single
cache directory so they're easy to find — and easy to throw away. The cache is
cleared at the start of every command (see :func:`reset_cache_dir`) so each run
starts from a known empty state.
"""

from __future__ import annotations

import shutil
from pathlib import Path

CACHE_DIR = Path.home() / ".cache" / "yt"


def reset_cache_dir() -> Path:
    """Remove the cache directory if it exists and re-create it empty."""
    if CACHE_DIR.exists():
        shutil.rmtree(CACHE_DIR)
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    return CACHE_DIR
