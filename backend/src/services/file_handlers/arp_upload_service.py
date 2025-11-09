#!/usr/bin/env python3
"""
Асинхронный обработчик ARP-файлов для FastAPI.
Принимает UploadFile, декодирует содержимое и возвращает результат в формате JSON-совместимого словаря.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import HTTPException, UploadFile

from ..utils.compat_asyncio import to_thread

_CANDIDATE_ENCODINGS = ("cp866", "cp1251", "utf-8")


def _to_number(value: Optional[str]) -> Optional[float]:
    if value is None or value == "":
        return None
    normalized = value.replace(",", ".")
    try:
        return float(normalized)
    except ValueError:
        return None


def _split_fields(line: str) -> List[str]:
    return line.rstrip("\r\n").split("#")


def _parse_type1(fields: List[str]) -> Dict[str, Any]:
    return {
        "type": 1,
        "standard": fields[1] if len(fields) > 1 else None,
        "producer_program": fields[2] if len(fields) > 2 else None,
        "producer_version": fields[3] if len(fields) > 3 else None,
    }


def _parse_type3(fields: List[str]) -> Dict[str, Any]:
    def f(index: int) -> Optional[str]:
        return fields[index] if len(fields) > index and fields[index] != "" else None

    def n(index: int) -> Optional[float]:
        return _to_number(f(index))

    return {
        "type": 3,
        "contract_number": f(1),
        "contract_name": f(2),
        "address": f(3),
        "doc_number_or_estimate_name": f(4),
        "doc_name": f(5),
        "customer": f(6),
        "customer_rep": f(7),
        "contractor": f(8),
        "contractor_rep": f(9),
        "subcontractor": f(10),
        "subcontractor_rep": f(11),
        "author": f(12),
        "controller": f(13),
        "total_cost": n(14),
        "price_level_year": n(15),
        "period": n(16),
        "project_code": f(17),
        "project_name": f(18),
        "basis": f(19),
        "normative_base": f(20),
    }


def _parse_type10(fields: List[str]) -> Dict[str, Any]:
    return {
        "type": 10,
        "level": int(fields[1]) if len(fields) > 1 and fields[1] else 0,
        "number": int(fields[2]) if len(fields) > 2 and fields[2] else 0,
        "name": fields[3] if len(fields) > 3 else "",
        "items": [],
    }


def _parse_type20(fields: List[str]) -> Dict[str, Any]:
    def f(index: int) -> Optional[str]:
        return fields[index] if len(fields) > index and fields[index] != "" else None

    def n(index: int) -> Optional[float]:
        return _to_number(f(index))

    line_no = n(1)
    abc = f(25)
    return {
        "type": 20,
        "line_no": line_no,
        "code": f(2),
        "unit": f(3),
        "name": f(4),
        "unit_base": {
            "direct_cost": n(5),
            "wages": n(6),
            "machines": n(7),
            "operators_wages": n(8),
            "materials": n(9),
            "materials_return": n(10),
            "materials_transport": n(11),
            "supervision": n(12),
            "labor_main": n(13),
            "labor_operators": n(14),
        },
        "unit_adjusted": {
            "direct_cost": n(15),
            "wages": n(16),
            "machines": n(17),
            "operators_wages": n(18),
            "materials": n(19),
            "materials_return": n(20),
            "materials_transport": n(21),
            "supervision": n(22),
            "labor_main": n(23),
            "labor_operators": n(24),
        },
        "abc_determinant": int(abc) if abc not in (None, "") else None,
        "volume": n(26),
        "subordinate_flag_or_norm": n(27),
        "estimate_line_number": f(28),
        "estimate_number": f(29),
    }


def _parse_type25(fields: List[str]) -> Dict[str, Any]:
    def n(index: int) -> Optional[float]:
        return _to_number(fields[index] if len(fields) > index else None)

    kind = fields[1] if len(fields) > 1 else None
    applies_to = fields[2] if len(fields) > 2 else None
    return {
        "type": 25,
        "kind": int(kind) if kind else None,
        "applies_to": int(applies_to) if applies_to else None,
        "value": n(3),
    }


def _parse_arp(text: str) -> Dict[str, Any]:
    document: Dict[str, Any] = {
        "standard": None,
        "document": None,
        "sections": [],
        "unknown_records": [],
    }
    section_stack: List[tuple[int, Dict[str, Any]]] = []

    for raw in text.splitlines():
        if not raw.strip():
            continue

        fields = _split_fields(raw)
        try:
            record_type = int(fields[0])
        except ValueError:
            document["unknown_records"].append({"raw": raw})
            continue

        if record_type == 1:
            document["standard"] = _parse_type1(fields)
        elif record_type == 3:
            document["document"] = _parse_type3(fields)
        elif record_type == 10:
            section = _parse_type10(fields)
            level = section["level"]
            while section_stack and section_stack[-1][0] >= level:
                section_stack.pop()
            if section_stack:
                section_stack[-1][1]["items"].append(section)
            else:
                document["sections"].append(section)
            section_stack.append((level, section))
        elif record_type == 20:
            position = _parse_type20(fields)
            if section_stack:
                section_stack[-1][1]["items"].append(position)
            else:
                document.setdefault("items", []).append(position)
        elif record_type == 25:
            coefficient = _parse_type25(fields)
            target = None
            if section_stack and section_stack[-1][1]["items"]:
                last_item = section_stack[-1][1]["items"][-1]
                if isinstance(last_item, dict) and last_item.get("type") == 20:
                    target = last_item
            if target is None and section_stack:
                target = section_stack[-1][1]
            if target is not None:
                target.setdefault("coefficients", []).append(coefficient)
            else:
                document.setdefault("coefficients", []).append(coefficient)
        elif record_type == 0:
            comment = fields[1] if len(fields) > 1 else ""
            attach_to = None
            if section_stack and section_stack[-1][1]["items"]:
                attach_to = section_stack[-1][1]["items"][-1]
            elif section_stack:
                attach_to = section_stack[-1][1]
            if attach_to is not None:
                attach_to.setdefault("comments", []).append(comment)
            else:
                document.setdefault("comments", []).append(comment)
        else:
            document["unknown_records"].append({"type": record_type, "fields": fields[1:]})

    return document


def _decode_arp_bytes(data: bytes) -> str:
    """
    Подбирает подходящую кодировку для ARP-файла.
    Возвращает текстовое содержимое, заменяя некорректные символы в крайнем случае.
    """
    for encoding in _CANDIDATE_ENCODINGS:
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    return data.decode("cp866", errors="replace")


async def convert_arp_upload_to_json(arp_file: UploadFile) -> Dict[str, Any]:
    """
    Конвертирует ARP-файл, полученный через UploadFile, в словарь с распарсенными данными.
    """
    if arp_file is None:
        raise HTTPException(status_code=400, detail="Файл ARP обязателен для загрузки.")

    filename = arp_file.filename or "uploaded.arp"

    payload = await arp_file.read()
    await arp_file.seek(0)
    if not payload:
        raise HTTPException(status_code=400, detail="Загруженный ARP-файл пуст.")

    text = _decode_arp_bytes(payload)

    try:
        data = await to_thread(_parse_arp, text)
    except Exception as exc:  # pragma: no cover - защита от непредвиденных ошибок
        raise HTTPException(status_code=422, detail="Не удалось распарсить ARP-файл.") from exc

    return {
        "source_filename": filename,
        "data": data,
    }


__all__ = ["convert_arp_upload_to_json"]


