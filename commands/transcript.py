"""Download a YouTube video and transcribe its audio to an SRT subtitle file.

The transcript is generated from the audio (via faster-whisper), independent of
any YouTube-provided captions.
"""

import argparse
import sys
from pathlib import Path

from faster_whisper import WhisperModel

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


def transcribe(media_path: Path, language: str, model_size: str) -> Path:
    print(f"==> Loading whisper model '{model_size}' (first run downloads ~hundreds of MB)")
    model = WhisperModel(model_size, device="cpu", compute_type="int8")

    print(f"==> Transcribing {media_path.name} (lang={language})")
    segments, _ = model.transcribe(
        str(media_path),
        language=language,
        vad_filter=True,
    )

    srt_path = media_path.with_suffix(".srt")
    with srt_path.open("w", encoding="utf-8") as f:
        for index, seg in enumerate(segments, start=1):
            f.write(f"{index}\n")
            f.write(f"{_format_timestamp(seg.start)} --> {_format_timestamp(seg.end)}\n")
            f.write(f"{seg.text.strip()}\n\n")
    return srt_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Download a YouTube video and transcribe its audio to SRT."
    )
    parser.add_argument("url", help="YouTube video URL")
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
    args = parser.parse_args(argv)

    media_path = download(args.url, args.output_dir, audio_only=False)
    srt_path = transcribe(media_path, args.lang, args.model)
    print(f"==> Wrote {srt_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
