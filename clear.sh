#!/usr/bin/env bash
# Remove local build outputs and Python bytecode caches (.venv and .git are left intact).
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

echo "==> Removing dist/, build/, and *.egg-info"
rm -rf dist build
# Editable installs or local builds may leave these at the repo root.
shopt -s nullglob
rm -rf ./*.egg-info

echo "==> Removing __pycache__ (except under .venv and .git)"
while IFS= read -r -d '' dir; do
    rm -rf "$dir"
done < <(find . -type d -name "__pycache__" ! -path "./.venv/*" ! -path "./.git/*" -print0)

echo "Clear complete."
