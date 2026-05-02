"""Download a YouTube video and transcribe its audio to an SRT subtitle file.

The transcript is generated from the audio (via faster-whisper), independent of
any YouTube-provided captions.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from faster_whisper import WhisperModel
from tqdm import tqdm

from commands.download import download

SUPPORTED_LANGS = ("en", "zh", "ja")


def _format_timestamp(seconds: float) -> str:
    if seconds < 0:
        seconds = 0
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int(round((seconds - int(seconds)) * 1000))
    if millis == 1000:
        millis = 0
        secs += 1
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def transcribe(media_path: Path, language: str, model_size: str) -> tuple[Path, Path]:
    print(f"==> Loading whisper model '{model_size}' (first run downloads ~hundreds of MB)")
    model = WhisperModel(model_size, device="cpu", compute_type="int8")

    print(f"==> Transcribing {media_path.name} (lang={language})")
    segments, info = model.transcribe(
        str(media_path),
        language=language,
        vad_filter=True,
    )

    srt_path = media_path.with_suffix(".srt")
    txt_path = media_path.with_suffix(".txt")
    total = float(getattr(info, "duration", 0) or 0)
    bar = tqdm(
        total=round(total, 2) if total else None,
        unit="s",
        bar_format="{l_bar}{bar}| {n:.1f}/{total:.1f}s [{elapsed}<{remaining}]",
    )
    last_end = 0.0
    with srt_path.open("w", encoding="utf-8") as srt, txt_path.open("w", encoding="utf-8") as txt:
        for index, seg in enumerate(segments, start=1):
            text = seg.text.strip()
            srt.write(f"{index}\n")
            srt.write(f"{_format_timestamp(seg.start)} --> {_format_timestamp(seg.end)}\n")
            srt.write(f"{text}\n\n")
            txt.write(f"{text}\n")
            if total:
                bar.update(max(0.0, min(seg.end, total) - last_end))
                last_end = min(seg.end, total)
    bar.close()
    return srt_path, txt_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Transcribe a YouTube video or local media file to SRT and TXT."
    )
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("-u", "--url", help="YouTube video URL")
    source.add_argument("-f", "--file", type=Path, help="Path to a local media file")
    parser.add_argument(
        "--lang",
        choices=SUPPORTED_LANGS,
        required=True,
        help="Audio language (en, zh, or ja)",
    )
    parser.add_argument(
        "-o",
        "--output-dir",
        type=Path,
        default=Path.cwd(),
        help="Directory to save the video and SRT into (default: current directory)",
    )
    parser.add_argument(
        "--model",
        default="small",
        help="faster-whisper model size: tiny, base, small, medium, large-v3 (default: small)",
    )
    parser.add_argument(
        "--cookies-from-browser",
        help="Browser to read cookies from (e.g. chrome, firefox, safari, brave, edge)",
    )
    args = parser.parse_args(argv)

    if args.url:
        media_path = download(
            args.url,
            args.output_dir,
            audio_only=False,
            cookies_from_browser=args.cookies_from_browser,
        )
    else:
        if not args.file.is_file():
            parser.error(f"file not found: {args.file}")
        media_path = args.file
    srt_path, txt_path = transcribe(media_path, args.lang, args.model)
    print(f"==> Wrote {srt_path}")
    print(f"==> Wrote {txt_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
