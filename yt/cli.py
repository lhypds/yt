"""yt CLI dispatcher.

Usage: yt <command> [args...]

Forwards all arguments after <command> to yt.commands.<command>'s main().
"""

from __future__ import annotations

import importlib
import sys
from importlib.metadata import PackageNotFoundError, version as pkg_version
from pathlib import Path


def _version_string() -> str:
    root = Path(__file__).resolve().parent.parent
    vf = root / "VERSION"
    if vf.is_file():
        return vf.read_text(encoding="utf-8").strip()
    try:
        return pkg_version("yt")
    except PackageNotFoundError:
        return "0.0.0"


def main(argv: list[str]) -> int:
    if argv and argv[0] in ("-v", "--version"):
        print(_version_string())
        return 0

    if len(argv) < 1 or argv[0] in ("-h", "--help"):
        available = sorted(
            p.stem
            for p in (Path(__file__).resolve().parent / "commands").glob("*.py")
            if not p.stem.startswith("_")
        )
        print(
            f"usage: yt <command> [args...]\n"
            f"       yt -v | --version\n\n"
            f"commands: {', '.join(available)}"
        )
        return 0 if argv else 1

    command, *rest = argv
    try:
        module = importlib.import_module(f"yt.commands.{command}")
    except ModuleNotFoundError:
        print(f"yt: unknown command '{command}'", file=sys.stderr)
        return 2

    return module.main(rest)


def run() -> int:
    """Console script entry point (reads sys.argv)."""
    return main(sys.argv[1:])


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
