# Speaker Diarization Workflow

This guide explains how to label Whisper transcripts with speaker tags using the
`pyannote/speaker-diarization` pipeline and the helper script
`scripts/diarize_and_align.py`.

## 1. Prerequisites

1. Obtain a Hugging Face account and request access to the gated model
   [`pyannote/speaker-diarization`](https://huggingface.co/pyannote/speaker-diarization).
2. Create an access token on Hugging Face and export it before running the
   script:
   ```bash
   export HF_TOKEN="hf_xxx YOUR TOKEN"
   ```
3. Install FFmpeg if not already present (`brew install ffmpeg`).

## 2. Prepare environments

Two Python virtualenvs are used to avoid conflicting dependencies between
Whisper and pyannote.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install openai-whisper torch==2.2.2 torchaudio==2.2.2 torchvision==0.17.2 --index-url https://download.pytorch.org/whl/cpu
pip install 'numpy<2'

python3 -m venv .venv_diar
source .venv_diar/bin/activate
pip install pyannote.audio==3.3.1
pip install 'numpy<2'  # required for the current CPU PyTorch wheels
```

> If you already ran the Whisper setup earlier, only the `.venv_diar`
> environment needs to be created.

## 3. Generate Whisper transcript

Use `scripts/transcribe_meeting.py` (from `.venv`) to create
`transcript_segments.json`, e.g.:

```bash
source .venv/bin/activate
python scripts/transcribe_meeting.py Recording.m4a --model small --language ru --output-dir outputs/recording_demo
```

## 4. Run diarization and alignment

Switch to the diarization environment and run the helper:

```bash
source .venv_diar/bin/activate
python scripts/diarize_and_align.py Recording.m4a outputs/recording_demo/transcript_segments.json \
  --output-dir outputs/recording_demo/speaker_alignment
```

The script produces:
- `speaker_segments.json` — Whisper segments enriched with a `speaker` field.
- `speaker_transcript.md` — markdown list of `Speaker [start-end]` entries.

## 5. Customisation

- Use `--hf-token` to pass the token directly instead of relying on the
  environment variable.
- `--pipeline` lets you try alternative diarization checkpoints if you have
  them locally.
- Keyword heuristics in `scripts/transcribe_meeting.py` still work; you can now
  combine them with speaker metadata by post-processing `speaker_segments.json`.

## 6. Troubleshooting

- **`HuggingFace token required`** — ensure `HF_TOKEN` is exported or pass
  `--hf-token`.
- **NumPy version warnings** — if PyTorch complains about NumPy 2.x, reinstall
  `numpy<2` inside `.venv_diar` as shown above.
- **Model download failures** — the first run downloads several hundred MB.
  Retry after reactivating the environment; the checkpoint is cached locally.
