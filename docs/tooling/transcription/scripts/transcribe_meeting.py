#!/usr/bin/env python3
"""
CLI utility to transcribe Russian-language meeting audio with Whisper
and automatically derive structured meeting notes. The tool runs fully
offline using open-source models, so it stays free of usage fees.
"""
import argparse
import json
import re
from pathlib import Path

import whisper

NOTE_PATTERNS = {
    "decisions": re.compile(r"\b(решили|договорились|приняли|согласовали|утвердили)\b", re.I),
    "actions": re.compile(r"\b(сделает|выполнит|ответственный|назначить|поручено|нужно сделать)\b", re.I),
    "risks": re.compile(r"\b(риски?|проблема|риск|задержка|задержится|не получится|препятствие)\b", re.I),
    "questions": re.compile(r"\?|нужно уточнить|вопрос|уточнить", re.I),
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Transcribe audio to text and extract meeting notes")
    parser.add_argument("audio", type=Path, help="Path to source audio or video file")
    parser.add_argument("--model", default="small", help="Whisper model size to load (e.g. tiny, base, small, medium)")
    parser.add_argument("--language", default="ru", help="Two-letter language code, default ru")
    parser.add_argument("--device", default="cpu", choices=["cpu", "cuda"], help="Execution device for Whisper")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("outputs"),
        help="Directory to store transcript and notes",
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.0,
        help="Decoding temperature (0 == more deterministic)",
    )
    parser.add_argument(
        "--translate",
        action="store_true",
        help="Translate to English instead of transcribing in source language",
    )
    return parser.parse_args()


def ensure_audio_exists(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(f"Audio file not found: {path}")
    if not path.is_file():
        raise ValueError(f"Audio path is not a regular file: {path}")


def prepare_output_dir(directory: Path) -> None:
    directory.mkdir(parents=True, exist_ok=True)


def transcribe(args: argparse.Namespace) -> dict:
    model = whisper.load_model(args.model, device=args.device)
    result = model.transcribe(
        str(args.audio),
        language=args.language,
        task="translate" if args.translate else "transcribe",
        temperature=args.temperature,
        verbose=True,
    )
    return result


def write_transcript(result: dict, output_dir: Path) -> Path:
    transcript_path = output_dir / "transcript.txt"
    with transcript_path.open("w", encoding="utf-8") as f:
        f.write(result.get("text", "").strip())
    json_path = output_dir / "transcript_segments.json"
    with json_path.open("w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    return transcript_path


def format_timestamp(value: float) -> str:
    minutes, seconds = divmod(int(value), 60)
    return f"{minutes:02d}:{seconds:02d}"


def categorize_segment(text: str) -> str | None:
    for label, pattern in NOTE_PATTERNS.items():
        if pattern.search(text):
            return label
    return None


def derive_notes(result: dict, output_dir: Path) -> Path:
    segments = result.get("segments", [])
    grouped: dict[str, list[str]] = {key: [] for key in NOTE_PATTERNS}

    for segment in segments:
        text = segment.get("text", "").strip()
        if not text:
            continue
        label = categorize_segment(text)
        if not label:
            continue
        start = format_timestamp(segment.get("start", 0.0))
        end = format_timestamp(segment.get("end", 0.0))
        grouped[label].append(f"- {start}-{end}: {text}")

    notes_path = output_dir / "meeting_notes.md"
    with notes_path.open("w", encoding="utf-8") as f:
        f.write("# Meeting Notes\n")
        for label, entries in grouped.items():
            if not entries:
                continue
            f.write(f"\n## {label.capitalize()}\n")
            f.write("\n".join(entries))
            f.write("\n")
        if all(len(entries) == 0 for entries in grouped.values()):
            f.write("\n_No matches for decision/action/risk/question keywords. Review the transcript manually._\n")
    return notes_path


def main() -> None:
    args = parse_args()
    ensure_audio_exists(args.audio)
    prepare_output_dir(args.output_dir)

    print("Loading Whisper model…")
    result = transcribe(args)

    transcript_path = write_transcript(result, args.output_dir)
    notes_path = derive_notes(result, args.output_dir)

    print(f"Transcript saved to {transcript_path}")
    print(f"Meeting notes saved to {notes_path}")


if __name__ == "__main__":
    main()
