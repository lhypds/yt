"""Summarize a YouTube video by transcribing it and asking OpenAI for the main points."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

from .download import download
from .transcript import SUPPORTED_LANGS, transcribe

DEFAULT_MODEL = "gpt-5.5"

PROMPT = (
    "You are reading the transcript of a video. Extract the most "
    "informational content — the specific facts, claims, numbers, names, "
    "events, and conclusions a viewer would actually want to take away. "
    "Skip filler, intros, sponsor reads, and rhetorical throat-clearing. "
    "Write it as natural prose, not a bulleted list. Be faithful to the "
    "transcript and do not invent details."
)


def summarize_text(transcript: str, model: str) -> str:
    client = OpenAI()
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": PROMPT},
            {"role": "user", "content": transcript},
        ],
    )
    return response.choices[0].message.content or ""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Download a YouTube video, transcribe it, and summarize the main points."
    )
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("-u", "--url", help="YouTube video URL")
    source.add_argument(
        "-f",
        "--file",
        type=Path,
        help="Path to a local media file or an existing .txt transcript",
    )
    parser.add_argument(
        "--lang",
        choices=SUPPORTED_LANGS,
        help="Audio language (en, zh, or ja). Required unless --file points to a .txt",
    )
    parser.add_argument(
        "-o",
        "--output-dir",
        type=Path,
        default=Path.cwd(),
        help="Directory to save downloads and outputs into (default: current directory)",
    )
    parser.add_argument(
        "--whisper-model",
        default="small",
        help="faster-whisper model size: tiny, base, small, medium, large-v3 (default: small)",
    )
    parser.add_argument(
        "--openai-model",
        default=DEFAULT_MODEL,
        help=f"OpenAI chat model to use for summarization (default: {DEFAULT_MODEL})",
    )
    parser.add_argument(
        "--cookies-from-browser",
        help="Browser to read cookies from (e.g. chrome, firefox, safari, brave, edge)",
    )
    args = parser.parse_args(argv)

    load_dotenv()
    if not os.getenv("OPENAI_API_KEY"):
        parser.error(
            "OPENAI_API_KEY is not set. Copy .env.example to .env and add your key."
        )

    if args.file and args.file.suffix.lower() == ".txt":
        if not args.file.is_file():
            parser.error(f"file not found: {args.file}")
        txt_path = args.file
    else:
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
        txt_path = media_path.with_suffix(".txt")
        if txt_path.is_file():
            print(f"==> Reusing existing transcript {txt_path}")
        else:
            if args.lang is None:
                parser.error("--lang is required when transcribing audio/video")
            _, txt_path = transcribe(media_path, args.lang, args.whisper_model)

    transcript_text = txt_path.read_text(encoding="utf-8").strip()
    if not transcript_text:
        print(f"error: transcript at {txt_path} is empty", file=sys.stderr)
        return 1

    print(f"==> Summarizing {txt_path.name} with {args.openai_model}")
    summary = summarize_text(transcript_text, args.openai_model)

    summary_path = txt_path.with_suffix(".summary.md")
    summary_path.write_text(summary + "\n", encoding="utf-8")
    print(f"==> Wrote {summary_path}")
    print()
    print(summary)

    opener = "open" if sys.platform == "darwin" else "xdg-open"
    subprocess.run([opener, str(summary_path)], check=False)
    return 0


if __name__ == "__main__":
    sys.exit(main())
