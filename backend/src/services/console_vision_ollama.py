from __future__ import annotations

from pathlib import Path
import base64
import subprocess
from typing import Iterable


def run_console_vision_ollama(question: str, file_paths: Iterable[str]) -> dict:
    """Run the vision model via the Ollama CLI with attached images."""

    normalized_paths = []
    encoded_images = []

    for file_path in file_paths:
        path = Path(file_path).expanduser().resolve()
        if not path.is_file():
            raise FileNotFoundError(f"File not found: {path}")

        data = path.read_bytes()
        if not data:
            raise ValueError(f"File is empty: {path}")

        encoded_images.append(base64.b64encode(data).decode("utf-8"))
        normalized_paths.append(str(path))

    if not encoded_images:
        raise ValueError("At least one image file must be provided")

    prompt = (
        "You are provided with one or more images encoded in base64. "
        "Use them to answer the user's question clearly and concisely.\n\n"
        f"Question:\n{question}\n\n"
        "Image Data (base64-encoded):\n"
    )

    for idx, (path, encoded) in enumerate(zip(normalized_paths, encoded_images), start=1):
        prompt += f"\n[Image {idx}: {Path(path).name}]\n{encoded}\n"

    try:
        result = subprocess.run(
            ["ollama", "run", "llama3.2-vision"],
            input=prompt,
            text=True,
            capture_output=True,
            check=True,
        )
    except FileNotFoundError as exc:
        raise RuntimeError("The 'ollama' executable is not available in PATH.") from exc
    except subprocess.CalledProcessError as exc:
        stderr = exc.stderr.strip() if exc.stderr else ""
        raise RuntimeError(
            "Ollama CLI call failed with exit code "
            f"{exc.returncode}. {stderr}"
        ) from exc

    return {
        "model": "llama3.2-vision",
        "prompt": prompt,
        "response": result.stdout.strip(),
    }


