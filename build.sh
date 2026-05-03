#!/usr/bin/env bash
# Build wheel and sdist into dist/. Uses .venv; run setup.sh first if needed.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

VENV_DIR=".venv"

if [ ! -d "$VENV_DIR" ]; then
    echo "error: $VENV_DIR not found. Run ./setup.sh first." >&2
    exit 1
fi

# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"

echo "==> Installing build backend (isolated build still uses pyproject [build-system])"
pip install -q build

echo "==> Building sdist and wheel"
python -m build

cat <<EOF

Artifacts are in dist/
EOF
