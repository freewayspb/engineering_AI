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

try:
    import pandas as pd  # type: ignore[import-untyped]
except ImportError as exc:
    raise ImportError(
        "pandas is required but not installed. Install it with: pip install pandas>=2.0.0"
    ) from exc

try:
    from dateutil.parser import ParserError  # type: ignore[import-untyped]
except ImportError as exc:
    raise ImportError(
        "python-dateutil is required but not installed. Install it with: pip install python-dateutil>=2.8.0"
    ) from exc

from fastapi import HTTPException, UploadFile

try:
    from openpyxl.utils.exceptions import InvalidFileException  # type: ignore[import-untyped]
    from openpyxl.utils.exceptions import ReadOnlyWorkbookException  # type: ignore[import-untyped]
except ImportError as exc:
    raise ImportError(
        "openpyxl is required but not installed. Install it with: pip install openpyxl>=3.0.0"
    ) from exc

try:
    from pandas.errors import EmptyDataError  # type: ignore[import-untyped]
except ImportError:
    # Для старых версий pandas создаем фиктивный класс
    class EmptyDataError(Exception):  # type: ignore[misc]
        pass

from zipfile import BadZipFile
import logging

from ..utils.compat_asyncio import to_thread

logger = logging.getLogger(__name__)


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

    try:
        sheets = pd.read_excel(
            xlsx_path,
            sheet_name=None if sheet is None else sheet,
            dtype=object,
            engine="openpyxl",
        )
    except Exception as exc:
        # Перехватываем ошибки чтения и добавляем контекст
        error_type = type(exc).__name__
        error_msg = str(exc)
        raise ValueError(
            f"Ошибка чтения Excel файла ({error_type}): {error_msg}"
        ) from exc

    if isinstance(sheets, pd.DataFrame):
        sheets = {sheet or "Sheet1": sheets}

    result: Dict[str, Any] = {}
    for name, df in sheets.items():
        if df.empty:
            result[name] = []
            continue
        try:
            norm = normalize_dataframe(
                df,
                header_row=header_row,
                ffill_merged=ffill_merged,
                drop_empty_rows=drop_empty_rows,
                drop_empty_cols=drop_empty_cols,
            )
            result[name] = dataframe_to_records(norm)
        except Exception as exc:
            # Добавляем информацию о листе в ошибку
            error_type = type(exc).__name__
            error_msg = str(exc)
            raise ValueError(
                f"Ошибка обработки листа '{name}' ({error_type}): {error_msg}"
            ) from exc
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
    logger.info("=== XLSX START === file=%s", filename)
    suffix = Path(filename).suffix or ".xlsx"

    payload = await xlsx_file.read()
    await xlsx_file.seek(0)
    if not payload:
        raise HTTPException(status_code=400, detail="Загруженный XLSX-файл пуст.")

    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix, mode='wb') as tmp_file:
        tmp_file.write(payload)
        tmp_file.flush()  # Убеждаемся, что данные записаны на диск
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
    except BadZipFile as exc:
        raise HTTPException(
            status_code=422,
            detail=f"Файл '{filename}' не является валидным XLSX-файлом (поврежденный ZIP-архив)."
        ) from exc
    except InvalidFileException as exc:
        raise HTTPException(
            status_code=422,
            detail=f"Файл '{filename}' не является валидным Excel-файлом: {str(exc)}"
        ) from exc
    except ReadOnlyWorkbookException as exc:
        raise HTTPException(
            status_code=422,
            detail=f"Файл '{filename}' открыт только для чтения или защищен от записи: {str(exc)}"
        ) from exc
    except EmptyDataError as exc:
        raise HTTPException(
            status_code=422,
            detail=f"Файл '{filename}' не содержит данных или все листы пусты."
        ) from exc
    except (ValueError, ParserError) as exc:
        error_msg = str(exc) or "Не удалось обработать XLSX-файл."
        raise HTTPException(
            status_code=422,
            detail=f"Ошибка обработки XLSX-файла '{filename}': {error_msg}",
        ) from exc
    except ImportError as exc:
        if "openpyxl" in str(exc).lower():
            raise HTTPException(
                status_code=500,
                detail="Модуль openpyxl не установлен. Установите его командой: pip install openpyxl"
            ) from exc
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка импорта модуля: {str(exc)}"
        ) from exc
    except (IndexError, KeyError) as exc:
        error_msg = str(exc) or "Ошибка доступа к данным"
        raise HTTPException(
            status_code=422,
            detail=f"Ошибка структуры XLSX-файла '{filename}': {error_msg}. Проверьте наличие листов и корректность структуры данных."
        ) from exc
    except OSError as exc:
        error_msg = str(exc) or "Ошибка файловой системы"
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при чтении XLSX-файла '{filename}': {error_msg}"
        ) from exc
    except Exception as exc:  # pragma: no cover - защита от непредвиденных ошибок
        error_type = type(exc).__name__
        error_msg = str(exc) or "Неизвестная ошибка"
        logger.error("=== XLSX ERROR === file=%s, type=%s, msg=%s", filename, error_type, error_msg, exc_info=True)
        # Включаем детали ошибки в сообщение для отладки
        detail_msg = f"Неожиданная ошибка при обработке XLSX-файла '{filename}' ({error_type}): {error_msg}"
        logger.error("=== XLSX ERROR DETAIL === %s", detail_msg)
        raise HTTPException(
            status_code=500,
            detail=detail_msg
        ) from exc
    finally:
        tmp_path.unlink(missing_ok=True)

    return {
        "source_filename": filename,
        "sheet_count": len(sheets_payload),
        "sheets": sheets_payload,
    }


__all__ = ["convert_xlsx_to_json", "convert_xlsx_upload_to_json"]


