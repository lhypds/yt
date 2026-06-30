#!/usr/bin/env bash
# Preparation for ./install.sh: create .venv with Python >= 3.11, upgrade pip, check ffmpeg.
# Does not install project dependencies or the global yt command — run ./install.sh after this.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

VENV_DIR=".venv"

PY=""
for cmd in "${PYTHON:-}" python3.13 python3.12 python3.11 python3; do
    [ -z "$cmd" ] && continue
    command -v "$cmd" >/dev/null 2>&1 || continue
    if "$cmd" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)' 2>/dev/null; then
        PY="$cmd"
        break
    fi
done

if [ -z "$PY" ]; then
    echo "error: need Python >= 3.11 for this project." >&2
    echo "  PYTHON=/opt/homebrew/bin/python3.12 ./setup.sh" >&2
    exit 1
fi

if [ ! -d "$VENV_DIR" ]; then
    echo "==> Creating virtualenv at $VENV_DIR ($PY)"
    "$PY" -m venv "$VENV_DIR"
else
    echo "==> Reusing existing virtualenv at $VENV_DIR"
fi

# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"

echo "==> Upgrading pip"
pip install --upgrade pip

if [ -f ".env.example" ]; then
    if [ ! -f ".env" ]; then
        cp ".env.example" ".env"
        echo "==> Created .env from .env.example"
    else
        echo "==> Keeping existing .env"
    fi
fi

if ! command -v ffmpeg >/dev/null 2>&1; then
    cat >&2 <<'EOF'

warning: ffmpeg was not found on PATH.
  yt-dlp needs ffmpeg to merge best-quality video+audio streams and to
  extract audio (--audio-only). Install it with:
    macOS:        brew install ffmpeg
    Debian/Ubuntu: sudo apt install ffmpeg
EOF
fi

cat <<EOF

Setup complete — ready for ./install.sh

Next step (installs Python deps + global \`yt\` command):
    ./install.sh

Optional: activate the venv only (no global \`yt\` yet):
    source $VENV_DIR/bin/activate
EOF
