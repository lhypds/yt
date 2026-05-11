"""Download the latest yt release from GitHub and reinstall it in place.

Behaviour:
    1. Reads the local version from ``yt -v``.
    2. Fetches the latest release metadata from ``lhypds/yt``.
    3. If a newer version exists (or --force is given), downloads the asset
       ``yt_v<VERSION>.zip`` to ``~/.yt/updates/``.
    4. Locates the existing install root from the ``~/.local/bin/yt`` launcher
       marker. If found, the new files are overlaid on top (preserving
       ``.venv`` and ``.env``); otherwise a fresh install is created under
       ``~/.yt/yt``.
    5. Runs ``setup.sh`` (when no ``.venv`` is present) and ``install.sh``
       from the install root so deps and the launcher are refreshed.

Usage:
    yt update              # update if a newer release is available
    yt update -f|--force   # reinstall even when already up to date
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import urllib.request
import zipfile

REPO = "lhypds/yt"
GITHUB_API_URL = f"https://api.github.com/repos/{REPO}/releases/latest"

UPDATES_DIR = os.path.expanduser("~/.yt/updates")
DEFAULT_INSTALL_ROOT = os.path.expanduser("~/.yt/yt")

LAUNCHER_PATH = os.path.expanduser("~/.local/bin/yt")
LAUNCHER_MARKER_PREFIX = "# yt-launcher:REPO="

# Names that exist in an installed checkout but must never be overwritten by
# the release archive — they are local state, not part of the release.
PRESERVE = {".venv", ".git", ".env"}


# ── version helpers ─────────────────────────────────────────────────────────

def get_current_version() -> str:
    """Run ``yt -v`` and return the bare version string (no leading 'v')."""
    try:
        result = subprocess.run(
            ["yt", "-v"],
            capture_output=True,
            text=True,
            check=True,
        )
    except FileNotFoundError:
        print("Error: 'yt' command not found in PATH.")
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        print(f"Error: 'yt -v' failed: {e}")
        sys.exit(1)

    output = result.stdout.strip()
    if not output:
        print("Error: 'yt -v' produced no output.")
        sys.exit(1)
    # Take the first token in case future versions append metadata.
    return output.split()[0].lstrip("v")


def parse_version(version_str: str) -> tuple[int, ...]:
    return tuple(int(x) for x in version_str.lstrip("v").split("."))


# ── github helpers ──────────────────────────────────────────────────────────

def get_latest_release() -> dict:
    req = urllib.request.Request(
        GITHUB_API_URL,
        headers={"User-Agent": "yt-updater"},
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            return json.loads(response.read().decode())
    except Exception as e:
        print(f"Error: could not fetch latest release from GitHub: {e}")
        sys.exit(1)


def find_asset_url(assets: list[dict], filename: str) -> str | None:
    for asset in assets:
        if asset.get("name") == filename:
            return asset.get("browser_download_url")
    return None


def download_file(url: str, dest_path: str) -> None:
    print(f"  Downloading {os.path.basename(dest_path)} ...")
    req = urllib.request.Request(url, headers={"User-Agent": "yt-updater"})
    try:
        with urllib.request.urlopen(req, timeout=60) as response:
            total = int(response.headers.get("Content-Length", 0))
            downloaded = 0
            chunk_size = 65536
            with open(dest_path, "wb") as f:
                while True:
                    chunk = response.read(chunk_size)
                    if not chunk:
                        break
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total:
                        pct = downloaded * 100 // total
                        print(f"\r  Progress: {pct}%", end="", flush=True)
        print()
    except Exception as e:
        print(f"\nError: download failed: {e}")
        sys.exit(1)


def extract_archive(archive_path: str, extract_dir: str) -> None:
    if os.path.exists(extract_dir):
        shutil.rmtree(extract_dir)
    os.makedirs(extract_dir, exist_ok=True)
    print(f"  Extracting to {extract_dir} ...")
    try:
        with zipfile.ZipFile(archive_path, "r") as zf:
            for info in zf.infolist():
                extracted = zf.extract(info, extract_dir)
                # Preserve Unix file mode (e.g. 0o755 on install.sh).
                unix_mode = (info.external_attr >> 16) & 0xFFFF
                if unix_mode:
                    os.chmod(extracted, unix_mode)
    except zipfile.BadZipFile as e:
        print(f"Error: archive is not a valid zip file: {e}")
        sys.exit(1)


# ── install-root resolution ─────────────────────────────────────────────────

def find_install_root() -> str | None:
    """Return the existing install root by reading the launcher marker."""
    if not os.path.isfile(LAUNCHER_PATH):
        return None
    try:
        with open(LAUNCHER_PATH) as f:
            for line in f:
                line = line.strip()
                if line.startswith(LAUNCHER_MARKER_PREFIX):
                    path = line[len(LAUNCHER_MARKER_PREFIX):]
                    return path or None
    except OSError:
        pass
    return None


def overlay_files(src_dir: str, dst_dir: str) -> None:
    """Copy each top-level entry from src_dir into dst_dir, replacing files
    and directories that exist there. Items whose name is in PRESERVE are
    left untouched in dst_dir."""
    os.makedirs(dst_dir, exist_ok=True)
    for entry in os.listdir(src_dir):
        if entry in PRESERVE:
            continue
        src = os.path.join(src_dir, entry)
        dst = os.path.join(dst_dir, entry)
        if os.path.isdir(src) and not os.path.islink(src):
            if os.path.exists(dst) or os.path.islink(dst):
                if os.path.isdir(dst) and not os.path.islink(dst):
                    shutil.rmtree(dst)
                else:
                    os.remove(dst)
            shutil.copytree(src, dst, symlinks=True)
        else:
            if os.path.isdir(dst) and not os.path.islink(dst):
                shutil.rmtree(dst)
            shutil.copy2(src, dst, follow_symlinks=False)


# ── install runner ──────────────────────────────────────────────────────────

def run_install(install_root: str) -> None:
    """Run setup.sh (if .venv is missing) then install.sh inside install_root."""
    setup_sh = os.path.join(install_root, "setup.sh")
    install_sh = os.path.join(install_root, "install.sh")
    venv_python = os.path.join(install_root, ".venv", "bin", "python")

    if not os.path.isfile(venv_python):
        if not os.path.isfile(setup_sh):
            print(f"Error: {setup_sh} not found.")
            sys.exit(1)
        os.chmod(setup_sh, 0o755)
        print("  Running setup.sh ...")
        result = subprocess.run(["bash", setup_sh], cwd=install_root)
        if result.returncode != 0:
            print(f"Error: setup.sh exited with code {result.returncode}.")
            sys.exit(result.returncode)

    if not os.path.isfile(install_sh):
        print(f"Error: {install_sh} not found.")
        sys.exit(1)
    os.chmod(install_sh, 0o755)
    print("  Running install.sh ...")
    result = subprocess.run(["bash", install_sh], cwd=install_root)
    if result.returncode != 0:
        print(f"Error: install.sh exited with code {result.returncode}.")
        sys.exit(result.returncode)


# ── entry point ─────────────────────────────────────────────────────────────

def main(argv: list[str] | None = None) -> int:
    argv = list(argv or [])
    force = "-f" in argv or "--force" in argv

    # 1. Current version
    current_version = get_current_version()
    print(f"Current version : v{current_version}")

    # 2. Latest release
    print("Checking for updates ...")
    release = get_latest_release()
    latest_tag = release.get("tag_name", "")
    if not latest_tag:
        print("Error: latest release has no tag_name.")
        return 1
    latest_version = latest_tag.lstrip("v")
    print(f"Latest version  : v{latest_version}")

    # 3. Compare
    try:
        current_tuple = parse_version(current_version)
        latest_tuple = parse_version(latest_version)
    except ValueError:
        print("Error: could not parse version numbers.")
        return 1

    if current_tuple >= latest_tuple:
        if not force:
            print("Already up to date.")
            return 0
        print("Already up to date, but forcing reinstall.")
    else:
        print(f"Update available : v{current_version} → v{latest_version}")

    # 4. Resolve asset
    asset_filename = f"yt_v{latest_version}.zip"
    download_url = find_asset_url(release.get("assets", []), asset_filename)
    if not download_url:
        print(f"Error: release asset '{asset_filename}' not found in latest release.")
        available = [a.get("name") for a in release.get("assets", [])]
        if available:
            print("  Available assets: " + ", ".join(a for a in available if a))
        return 1

    # 5. Prepare updates dir
    os.makedirs(UPDATES_DIR, exist_ok=True)
    archive_path = os.path.join(UPDATES_DIR, asset_filename)

    # 6. Download
    download_file(download_url, archive_path)

    # 7. Extract
    extract_dir = os.path.join(UPDATES_DIR, f"yt_v{latest_version}")
    extract_archive(archive_path, extract_dir)

    # 8. Install
    install_root = find_install_root()
    if install_root and os.path.isdir(install_root):
        print(f"Detected existing install at {install_root}.")
        print(f"  Overlaying new files (preserving {', '.join(sorted(PRESERVE))}) ...")
        overlay_files(extract_dir, install_root)
    else:
        if install_root:
            print(f"Launcher pointed to {install_root}, but that path is gone.")
        else:
            print("No previous yt install detected.")
        install_root = DEFAULT_INSTALL_ROOT
        print(f"Installing to {install_root}.")
        if os.path.exists(install_root):
            shutil.rmtree(install_root)
        shutil.copytree(extract_dir, install_root, symlinks=True)

    run_install(install_root)

    print(f"\nyt has been updated to v{latest_version}.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
