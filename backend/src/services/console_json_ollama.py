from __future__ import annotations

from pathlib import Path
import subprocess


def run_console_json_ollama(question: str, file_path: str) -> dict:
    """Run the DeepSeek model via the Ollama CLI using JSON/file context."""

    path = Path(file_path).expanduser().resolve()
    if not path.is_file():
        raise FileNotFoundError(f"File not found: {path}")

    try:
        file_contents = path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise UnicodeDecodeError(exc.encoding, exc.object, exc.start, exc.end, "Unable to decode file as UTF-8")

    prompt = (
        "You are provided with file context. "
        "Use it to answer the user's question clearly and concisely.\n\n"
        f"Question:\n{question}\n\n"
        f"File Context ({path.name}):\n{file_contents}"
    )

    try:
        result = subprocess.run(
            ["ollama", "run", "deepseek-r1"],
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
        "model": "deepseek-r1",
        "prompt": prompt,
        "response": result.stdout.strip(),
    }


