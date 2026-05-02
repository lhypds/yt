"""youtube-utils CLI dispatcher.

Usage: python yt.py <command> [args...]

Forwards all arguments after <command> to commands/<command>.py's main().
"""

import importlib
import sys
from pathlib import Path


def main(argv: list[str]) -> int:
    if len(argv) < 1 or argv[0] in ("-h", "--help"):
        available = sorted(
            p.stem
            for p in (Path(__file__).parent / "commands").glob("*.py")
            if not p.stem.startswith("_")
        )
        print(f"usage: yt <command> [args...]\n\ncommands: {', '.join(available)}")
        return 0 if argv else 1

    command, *rest = argv
    try:
        module = importlib.import_module(f"commands.{command}")
    except ModuleNotFoundError:
        print(f"yt: unknown command '{command}'", file=sys.stderr)
        return 2

    return module.main(rest)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
