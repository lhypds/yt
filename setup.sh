#!/usr/bin/env bash
# Set up the youtube-utils environment: creates .venv and installs requirements.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

PYTHON="${PYTHON:-python3}"
VENV_DIR=".venv"

if ! command -v "$PYTHON" >/dev/null 2>&1; then
    echo "error: $PYTHON not found on PATH" >&2
    exit 1
fi

if [ ! -d "$VENV_DIR" ]; then
    echo "==> Creating virtualenv at $VENV_DIR"
    "$PYTHON" -m venv "$VENV_DIR"
else
    echo "==> Reusing existing virtualenv at $VENV_DIR"
fi

# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"

echo "==> Upgrading pip"
pip install --upgrade pip

echo "==> Installing requirements"
pip install -r requirements.txt

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

Setup complete.

Activate the venv with:
    source $VENV_DIR/bin/activate

Or run the downloader directly:
    $VENV_DIR/bin/python video-download/download.py "<youtube-url>"
EOF
