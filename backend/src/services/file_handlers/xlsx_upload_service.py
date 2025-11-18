#!/usr/bin/env python3
"""
Асинхронный обработчик XLSX-файлов для FastAPI.
Принимает UploadFile, конвертирует Excel в JSON-совместимую структуру.
"""

from __future__ import annotations

import math
import re
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import pandas as pd
from dateutil.parser import ParserError
from fastapi import HTTPException, UploadFile

from ..utils.compat_asyncio import to_thread


EU_DECIMAL_RE = re.compile(
    r"""^\s*      # leading spaces
        (?:
          \d{1,3}(?:[ .\u00A0]\d{3})+  # 1 234 or 1.234 or 1 234 with group sep
          | \d+                         # or simple digits
        )
        (?:,\d+)?                       # optional decimal part with comma
        \s*$                            # trailing spaces
    """,
    re.X,
)


def try_parse_number(value: Any) -> Any:
    """Convert typical strings (including EU decimals) to float/int where possible."""
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return None
    if isinstance(value, (int, float)):
        if isinstance(value, float) and value.is_integer():
            return int(value)
        return value
    if isinstance(value, pd.Timestamp):
        return value.isoformat()

    if isinstance(value, str):
        s = value.strip()
        if not s:
            return None
        s = s.replace("\u00A0", " ")
        if EU_DECIMAL_RE.match(s):
            s_norm = re.sub(r"[ .\u00A0]", "", s)
            s_norm = s_norm.replace(",", ".")
            try:
                num = float(s_norm)
                if num.is_integer():
                    return int(num)
                return num
            except ValueError:
                pass
        try:
            if re.match(r"^\d+,\d+$", s):
                s = s.replace(",", ".")
            num = float(s)
            if num.is_integer():
                return int(num)
            return num
        except ValueError:
            return s or None
    return value


def clean_headers(cols: List[Any]) -> List[str]:
    out: List[str] = []
    for c in cols:
        if isinstance(c, tuple):
            c = " ".join(str(x) for x in c if x is not None and str(x).strip())
        c = "" if c is None else str(c)
        c = c.replace("\n", " ").strip()
        out.append(c or "col")
    seen: Dict[str, int] = {}
    uniq: List[str] = []
    for name in out:
        base = name or "col"
        if base not in seen:
            seen[base] = 0
            uniq.append(base)
        else:
            seen[base] += 1
            uniq.append(f"{base}_{seen[base]}")
    return uniq


def autodetect_header_row(
    df: pd.DataFrame,
    min_non_empty_ratio: float = 0.5,
    max_seek_rows: int = 30,
) -> int:
    """
    Find the first row that looks like headers:
    - at least 50% non-empty cells (configurable)
    - within the first N rows
    Returns row index (0-based). Fallback: 0.
    """
    width = df.shape[1] if df.shape[1] > 0 else 1
    for i in range(min(max_seek_rows, len(df))):
        row = df.iloc[i]
        non_empty = row.notna().sum()
        if non_empty / width >= min_non_empty_ratio:
            return i
    return 0


def normalize_dataframe(
    df: pd.DataFrame,
    header_row: Optional[int],
    ffill_merged: bool,
    drop_empty_rows: bool,
    drop_empty_cols: bool,
) -> pd.DataFrame:
    if header_row is None:
        header_row = autodetect_header_row(df)

    headers = df.iloc[header_row]
    data = df.iloc[header_row + 1 :].copy()

    if ffill_merged:
        headers = headers.ffill()
        data = data.ffill()

    cols = clean_headers(list(headers.values))
    data.columns = cols

    if drop_empty_cols:
        data = data.dropna(axis=1, how="all")
    if drop_empty_rows:
        data = data.dropna(axis=0, how="all")

    def clean_cell(x: Any) -> Any:
        if isinstance(x, str):
            x = x.strip()
            x = None if x == "" else x
        return try_parse_number(x)

    data = data.map(clean_cell)

    return data.reset_index(drop=True)


def dataframe_to_records(df: pd.DataFrame) -> List[Dict[str, Any]]:
    return df.to_dict(orient="records")


def convert_xlsx_to_json(
    xlsx_path: Union[str, Path],
    sheet: Optional[str],
    header_row: Optional[int],
    ffill_merged: bool,
    drop_empty_rows: bool,
    drop_empty_cols: bool,
) -> Dict[str, Any]:
    xlsx_path = Path(xlsx_path)
    if not xlsx_path.exists():
        raise FileNotFoundError(f"Not found: {xlsx_path}")

    sheets = pd.read_excel(
        xlsx_path,
        sheet_name=None if sheet is None else sheet,
        dtype=object,
        engine="openpyxl",
    )

    if isinstance(sheets, pd.DataFrame):
        sheets = {sheet or "Sheet1": sheets}

    result: Dict[str, Any] = {}
    for name, df in sheets.items():
        if df.empty:
            result[name] = []
            continue
        norm = normalize_dataframe(
            df,
            header_row=header_row,
            ffill_merged=ffill_merged,
            drop_empty_rows=drop_empty_rows,
            drop_empty_cols=drop_empty_cols,
        )
        result[name] = dataframe_to_records(norm)
    return result


async def convert_xlsx_upload_to_json(
    xlsx_file: UploadFile,
    *,
    sheet: Optional[str] = None,
    header_row: Optional[int] = None,
    ffill_merged: bool = True,
    drop_empty_rows: bool = True,
    drop_empty_cols: bool = True,
) -> Dict[str, Any]:
    """
    Конвертирует XLSX-файл, полученный через UploadFile, в словарь с данными листов.
    """
    if xlsx_file is None:
        raise HTTPException(status_code=400, detail="Файл XLSX обязателен для загрузки.")

    filename = xlsx_file.filename or "uploaded.xlsx"
    suffix = Path(filename).suffix or ".xlsx"

    payload = await xlsx_file.read()
    await xlsx_file.seek(0)
    if not payload:
        raise HTTPException(status_code=400, detail="Загруженный XLSX-файл пуст.")

    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
        tmp_file.write(payload)
        tmp_path = Path(tmp_file.name)

    try:
        sheets_payload = await to_thread(
            convert_xlsx_to_json,
            tmp_path,
            sheet,
            header_row,
            ffill_merged,
            drop_empty_rows,
            drop_empty_cols,
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=500, detail="Временный XLSX-файл не найден.") from exc
    except (ValueError, ParserError) as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc) or "Не удалось обработать XLSX-файл.",
        ) from exc
    except Exception as exc:  # pragma: no cover - защита от непредвиденных ошибок
        raise HTTPException(status_code=500, detail="Неожиданная ошибка при обработке XLSX.") from exc
    finally:
        tmp_path.unlink(missing_ok=True)

    return {
        "source_filename": filename,
        "sheet_count": len(sheets_payload),
        "sheets": sheets_payload,
    }


__all__ = ["convert_xlsx_to_json", "convert_xlsx_upload_to_json"]


