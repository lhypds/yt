"""Download a YouTube video given its URL."""

import argparse
import sys
from datetime import datetime
from pathlib import Path

from yt_dlp import YoutubeDL


def download(url: str, output_dir: Path, audio_only: bool = False) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d%H%M")
    name_template = (
        f"{timestamp}_%(id)s_[%(channel|NA)s]_[%(title)s].%(ext)s"
    )
    opts = {
        "outtmpl": str(output_dir / name_template),
        "noplaylist": True,
    }

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
    parser.add_argument("url", help="YouTube video URL")
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
    args = parser.parse_args(argv)

    download(args.url, args.output_dir, audio_only=args.audio_only)
    return 0


if __name__ == "__main__":
    sys.exit(main())
