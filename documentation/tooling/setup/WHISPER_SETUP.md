# Whisper Voice-to-Text Pipeline

This repository now contains a minimal offline pipeline to transcribe 47-minute (and longer) meeting recordings with [OpenAI Whisper](https://github.com/openai/whisper) and auto-generate draft meeting notes.

## 1. Install prerequisites

1. Ensure Python 3.9+ is available.
2. Install FFmpeg (audio conversion utility):
   ```bash
   brew install ffmpeg
   ```
3. Create a virtual environment and install the Python dependencies:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install --upgrade pip
   pip install openai-whisper torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
   ```
   *If you have a CUDA GPU, replace the last line with the official CUDA wheels from pytorch.org to speed up inference.*

## 2. (Optional) Normalize audio

For best accuracy, convert the source recording to 16 kHz mono WAV:
```bash
ffmpeg -i input_audio.m4a -ac 1 -ar 16000 normalized.wav
```

## 3. Run the transcription script

The helper script lives in `scripts/transcribe_meeting.py`. Example usage:
```bash
source .venv/bin/activate
python scripts/transcribe_meeting.py normalized.wav --model small --language ru --output-dir outputs/meeting_2024_06_01
```

Key options:
- `--model`: Whisper size (`tiny`, `base`, `small`, `medium`). Larger models increase accuracy at the cost of runtime and memory.
- `--device`: `cpu` by default. Use `--device cuda` if CUDA is available.
- `--translate`: If set, Whisper translates speech to English instead of transcribing in Russian.

## 4. Generated artifacts

The script writes the following files inside the chosen output directory:
- `transcript.txt` – full plain-text transcript.
- `transcript_segments.json` – Whisper JSON with timestamps for each utterance.
- `meeting_notes.md` – auto-extracted highlights grouped by decisions, action items, risks, and questions based on keyword heuristics.

If `meeting_notes.md` contains the fallback note "No matches...", adjust keywords in `NOTE_PATTERNS` inside the script to match your vocabulary.

## 5. Next steps

- The notes extraction currently uses simple regular expressions. Extend `NOTE_PATTERNS` or post-process `transcript_segments.json` with your own logic if you need richer summaries.
- To integrate into other documents (e.g., BRD templates), paste the relevant sections from `meeting_notes.md`.
- For batch processing, wrap the script call in a shell loop or invoke it from another Python module.
