#!/usr/bin/env python3
"""Speaker diarization + Whisper alignment helper.

Run pyannote's speaker diarization pipeline on a meeting recording and align the
resulting speaker turns with Whisper transcript segments. Outputs a Markdown
transcript with speaker labels and a JSON file for further processing.

This script is intended to be executed from the dedicated diarization virtual
environment (.venv_diar) which includes pyannote.audio and its dependencies.
"""
from __future__ import annotations

import argparse
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List

from pyannote.audio import Pipeline


@dataclass
class Segment:
    start: float
    end: float
    speaker: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run speaker diarization and align with Whisper segments")
    parser.add_argument("audio", type=Path, help="Path to the audio file used for diarization")
    parser.add_argument("segments", type=Path, help="Path to Whisper transcript_segments.json")
    parser.add_argument(
        "--hf-token",
        default=None,
        help="HuggingFace access token (if omitted, read from HF_TOKEN environment variable)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("outputs") / "speaker_alignment",
        help="Directory for speaker-attributed outputs",
    )
    parser.add_argument(
        "--pipeline",
        default="pyannote/speaker-diarization",
        help="Pyannote pipeline identifier",
    )
    return parser.parse_args()


def load_token(args: argparse.Namespace) -> str:
    token = args.hf_token or os.environ.get("HF_TOKEN") or os.environ.get("HUGGINGFACE_TOKEN")
    if not token:
        raise RuntimeError(
            "HuggingFace token required. Pass via --hf-token or export HF_TOKEN before running."
        )
    return token


def run_diarization(audio_path: Path, pipeline_name: str, token: str) -> List[Segment]:
    pipeline = Pipeline.from_pretrained(pipeline_name, use_auth_token=token)
    diarization = pipeline({"audio": str(audio_path)})

    segments: List[Segment] = []
    for turn, _, speaker in diarization.itertracks(yield_label=True):
        segments.append(Segment(start=float(turn.start), end=float(turn.end), speaker=speaker))
    segments.sort(key=lambda seg: seg.start)
    return segments


def load_whisper_segments(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("segments", [])


def overlap_duration(a_start: float, a_end: float, b_start: float, b_end: float) -> float:
    return max(0.0, min(a_end, b_end) - max(a_start, b_start))


def assign_speaker_to_whisper(whisper_segments: Iterable[dict], diar_segments: List[Segment]) -> list[dict]:
    assigned: list[dict] = []
    for seg in whisper_segments:
        start = float(seg.get("start", 0.0))
        end = float(seg.get("end", start))
        best_speaker = None
        best_overlap = 0.0

        for diar in diar_segments:
            overlap = overlap_duration(start, end, diar.start, diar.end)
            if overlap > best_overlap:
                best_overlap = overlap
                best_speaker = diar.speaker

        if best_speaker is None and diar_segments:
            midpoint = (start + end) / 2
            for diar in diar_segments:
                if diar.start <= midpoint <= diar.end:
                    best_speaker = diar.speaker
                    break
            if best_speaker is None:
                best_speaker = diar_segments[0].speaker

        seg_with_speaker = dict(seg)
        seg_with_speaker["speaker"] = best_speaker or "UNKNOWN"
        assigned.append(seg_with_speaker)
    return assigned


def write_outputs(segments: list[dict], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    json_path = output_dir / "speaker_segments.json"
    with json_path.open("w", encoding="utf-8") as f:
        json.dump({"segments": segments}, f, ensure_ascii=False, indent=2)

    markdown_path = output_dir / "speaker_transcript.md"
    with markdown_path.open("w", encoding="utf-8") as f:
        f.write("# Speaker Transcript\n\n")
        for seg in segments:
            speaker = seg.get("speaker", "UNKNOWN")
            start = seg.get("start", 0.0)
            end = seg.get("end", 0.0)
            text = seg.get("text", "").strip()
            f.write(f"- {speaker} [{format_timestamp(start)}-{format_timestamp(end)}]: {text}\n")


def format_timestamp(value: float) -> str:
    minutes, seconds = divmod(int(value), 60)
    return f"{minutes:02d}:{seconds:02d}"


def main() -> None:
    args = parse_args()
    token = load_token(args)

    if not args.audio.exists():
        raise FileNotFoundError(f"Audio file not found: {args.audio}")
    if not args.segments.exists():
        raise FileNotFoundError(f"Whisper segments JSON not found: {args.segments}")

    diar_segments = run_diarization(args.audio, args.pipeline, token)
    whisper_segments = load_whisper_segments(args.segments)

    assigned_segments = assign_speaker_to_whisper(whisper_segments, diar_segments)
    write_outputs(assigned_segments, args.output_dir)

    print(f"Wrote speaker-attributed segments to {args.output_dir}")


if __name__ == "__main__":
    main()
