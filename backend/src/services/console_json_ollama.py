from __future__ import annotations

from pathlib import Path
import subprocess


async def run_console_json_ollama(question: str, file_path: str) -> dict:
    """Run the DeepSeek model via the Ollama CLI using JSON/file context."""

    path = Path(file_path).expanduser().resolve()
    if not path.is_file():
        raise FileNotFoundError(f"File not found: {path}")

    try:
        file_contents = path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise UnicodeDecodeError(exc.encoding, exc.object, exc.start, exc.end, "Unable to decode file as UTF-8")

    question = "Опиши файл несколькими предложениями, подведи итог. Сделай выводы."
    prompt = (
        "Вам предоставлен контекст из файла. "
        "Используйте его, чтобы ответить на вопрос пользователя ясно и кратко.\n\n"
        f"Вопрос:\n{question}\n\n"
        f"Контекст файла ({path.name}):\n{file_contents}"
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


