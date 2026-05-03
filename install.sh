#!/usr/bin/env bash
# Run ./setup.sh first. Installs third-party deps into .venv and adds ~/.local/bin/yt
# (wrapper around yt.py using that venv). Does not install this repo as a pip package.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

VENV_DIR=".venv"
LAUNCHER_DIR="$HOME/.local/bin"
LAUNCHER="$LAUNCHER_DIR/yt"
MARKER="# yt-launcher:REPO=$ROOT_DIR"
VENV_PY="$VENV_DIR/bin/python"

if [ ! -x "$VENV_PY" ]; then
    echo "error: $VENV_DIR is missing or incomplete. Run ./setup.sh first." >&2
    exit 1
fi

if ! "$VENV_PY" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)' 2>/dev/null; then
    echo "error: $VENV_DIR was built with Python < 3.11. Remove it and run ./setup.sh again." >&2
    exit 1
fi

# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"

echo "==> Installing dependencies into $VENV_DIR"
pip install -r requirements.txt

mkdir -p "$LAUNCHER_DIR"

echo "==> Writing $LAUNCHER"
cat >"$LAUNCHER" <<EOF
#!/usr/bin/env bash
$MARKER
set -euo pipefail
exec "$ROOT_DIR/$VENV_DIR/bin/python" "$ROOT_DIR/yt.py" "\$@"
EOF
chmod +x "$LAUNCHER"

cat <<EOF

Install complete. \`yt\` runs from:
  $LAUNCHER

If the command is not found, add this to ~/.zshrc and open a new terminal:
  export PATH="\$HOME/.local/bin:\$PATH"
EOF
