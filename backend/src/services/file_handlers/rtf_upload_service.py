#!/usr/bin/env python3
"""
Асинхронный обработчик RTF-файлов для FastAPI.
Принимает UploadFile, извлекает текстовое содержимое и возвращает результат в JSON-совместимом виде.
"""

from __future__ import annotations

from typing import Any, Dict, List, Tuple

from fastapi import HTTPException, UploadFile

from ..utils.compat_asyncio import to_thread


def _decode_rtf_bytes(data: bytes) -> str:
    """
    RTF спецификация требует 7-битного ASCII, поэтому безопасно декодировать в latin-1, сохраняя байты 1:1.
    В ряде случаев файлы генерируются в UTF-8 — пробуем его сначала.
    """
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        return data.decode("latin-1", errors="ignore")


def _decode_hex_token(token: str, encoding: str) -> str:
    try:
        value = bytes.fromhex(token)
    except ValueError:
        return ""
    try:
        return value.decode(encoding)
    except UnicodeDecodeError:
        return value.decode("latin-1", errors="ignore")


def _rtf_to_text(rtf: str) -> str:
    """
    Минимальный парсер RTF -> plain text.
    """
    out: List[str] = []
    stack: List[Tuple[bool, int, str]] = []
    ignorable = False
    uc_skip = 1
    codepage = "cp1251"  # типичный код для русских документов; может быть переопределён \ansicpg

    i = 0
    length = len(rtf)

    while i < length:
        char = rtf[i]

        if char == "{":
            stack.append((ignorable, uc_skip, codepage))
            ignorable = False
            i += 1
            continue

        if char == "}":
            if stack:
                ignorable, uc_skip, codepage = stack.pop()
            i += 1
            continue

        if char == "\\":
            i += 1
            if i >= length:
                break

            control = rtf[i]

            if control in "\\{}":
                if not ignorable:
                    out.append(control)
                i += 1
                continue

            if control == "*":
                ignorable = True
                i += 1
                continue

            if control == "'":
                hex_token = rtf[i + 1 : i + 3]
                if len(hex_token) == 2 and not ignorable:
                    out.append(_decode_hex_token(hex_token, codepage))
                i += 3
                continue

            # Читаем управляющее слово
            j = i
            while j < length and rtf[j].isalpha():
                j += 1
            word = rtf[i:j]

            param = None
            if j < length and (rtf[j] == "-" or rtf[j].isdigit()):
                sign = 1
                if rtf[j] == "-":
                    sign = -1
                    j += 1
                k = j
                while k < length and rtf[k].isdigit():
                    k += 1
                if k > j:
                    param = sign * int(rtf[j:k])
                    j = k

            if j < length and rtf[j] == " ":
                j += 1

            i = j

            if ignorable:
                continue

            if word in ("par", "line"):
                out.append("\n")
                continue

            if word == "tab":
                out.append("\t")
                continue

            if word == "emdash":
                out.append("—")
                continue

            if word == "endash":
                out.append("–")
                continue

            if word == "lquote":
                out.append("‘")
                continue

            if word == "rquote":
                out.append("’")
                continue

            if word == "ldblquote":
                out.append("“")
                continue

            if word == "rdblquote":
                out.append("”")
                continue

            if word == "u" and param is not None:
                code_point = param if param >= 0 else param + 65536
                out.append(chr(code_point))
                skip = uc_skip
                while skip > 0 and i < length:
                    if rtf[i] == "\\" or rtf[i] in "{}":
                        break
                    i += 1
                    skip -= 1
                continue

            if word == "uc" and param is not None:
                uc_skip = max(0, param)
                continue

            if word == "ansicpg" and param is not None:
                codepage = f"cp{abs(param)}"
                continue

            # остальные управляющие слова игнорируем
            continue

        if not ignorable:
            if char == "\r":
                if i + 1 < length and rtf[i + 1] == "\n":
                    i += 1
                out.append("\n")
            elif char == "\n":
                out.append("\n")
            else:
                out.append(char)

        i += 1

    text = "".join(out)
    # Удаляем лишние пробелы по концам строк, чтобы унифицировать вывод
    normalized_lines = [line.rstrip() for line in text.splitlines()]
    return "\n".join(normalized_lines).strip()


def _prepare_rtf_payload(rtf_text: str) -> Dict[str, Any]:
    plain_text = _rtf_to_text(rtf_text)
    paragraphs = [line.strip() for line in plain_text.splitlines() if line.strip()]
    return {
        "plain_text": plain_text,
        "paragraphs": paragraphs,
        "stats": {
            "character_count": len(plain_text),
            "paragraph_count": len(paragraphs),
        },
    }


async def convert_rtf_upload_to_json(rtf_file: UploadFile) -> Dict[str, Any]:
    """
    Конвертирует RTF-файл, полученный через UploadFile, в словарь с извлечённым текстом.
    """
    if rtf_file is None:
        raise HTTPException(status_code=400, detail="Файл RTF обязателен для загрузки.")

    filename = rtf_file.filename or "uploaded.rtf"

    payload = await rtf_file.read()
    await rtf_file.seek(0)
    if not payload:
        raise HTTPException(status_code=400, detail="Загруженный RTF-файл пуст.")

    rtf_text = _decode_rtf_bytes(payload)

    try:
        parsed = await to_thread(_prepare_rtf_payload, rtf_text)
    except Exception as exc:  # pragma: no cover - защита от непредвиденных ошибок
        raise HTTPException(status_code=422, detail="Не удалось распарсить RTF-файл.") from exc

    return {
        "source_filename": filename,
        **parsed,
    }


__all__ = ["convert_rtf_upload_to_json"]



