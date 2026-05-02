"""Download a YouTube video given its URL."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from yt_dlp import YoutubeDL


def download(
    url: str,
    output_dir: Path,
    audio_only: bool = False,
    cookies_from_browser: str | None = None,
) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)

    name_template = "[%(channel|NA)s]_[%(title)s].%(ext)s"
    opts: dict = {
        "outtmpl": str(output_dir / name_template),
        "noplaylist": True,
        "extractor_args": {
            "youtube": {"player_client": ["tv_simply", "mweb", "default"]}
        },
    }
    if cookies_from_browser:
        opts["cookiesfrombrowser"] = (cookies_from_browser,)

    if audio_only:
        opts["format"] = "bestaudio/best"
        opts["postprocessors"] = [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }
        ]
    else:
        opts["format"] = "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best"
        opts["merge_output_format"] = "mp4"

    with YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=True)
        downloads = info.get("requested_downloads") or []
        if downloads and downloads[-1].get("filepath"):
            return Path(downloads[-1]["filepath"])
        return Path(ydl.prepare_filename(info))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Download a YouTube video.")
    parser.add_argument("-u", "--url", required=True, help="YouTube video URL")
    parser.add_argument(
        "-o",
        "--output-dir",
        type=Path,
        default=Path.cwd(),
        help="Directory to save the video into (default: current directory)",
    )
    parser.add_argument(
        "--audio-only",
        action="store_true",
        help="Download audio only (mp3) instead of video",
    )
    parser.add_argument(
        "--cookies-from-browser",
        help="Browser to read cookies from (e.g. chrome, firefox, safari, brave, edge)",
    )
    args = parser.parse_args(argv)

    download(
        args.url,
        args.output_dir,
        audio_only=args.audio_only,
        cookies_from_browser=args.cookies_from_browser,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
