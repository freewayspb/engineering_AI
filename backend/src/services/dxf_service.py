from __future__ import annotations

import asyncio
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict

from fastapi import HTTPException, UploadFile

try:  # pragma: no cover - dependency availability is runtime-specific
    import ezdxf  # type: ignore
except ImportError:  # pragma: no cover - handled at runtime
    ezdxf = None  # type: ignore[assignment]


if TYPE_CHECKING:  # pragma: no cover - typing helpers only
    from ezdxf.document import Drawing  # type: ignore
    from ezdxf.entities import DXFEntity  # type: ignore


SUPPORTED_EXTENSIONS = {".dxf", ".dwg"}


class DXFConversionError(Exception):
    """Raised when the DXF/DWG payload cannot be converted."""


def _ensure_dependency() -> None:
    if ezdxf is None:
        raise HTTPException(
            status_code=500,
            detail=(
                "DXF conversion requires the 'ezdxf' package. "
                "Install it with 'pip install ezdxf'."
            ),
        )


def _vec_to_list(vec: Any) -> list[float]:
    return [float(getattr(vec, axis, 0.0)) for axis in ("x", "y", "z")]


def _extract_entity_data(entity: "DXFEntity") -> Dict[str, Any]:
    data: Dict[str, Any] = {
        "type": entity.dxftype(),
        "layer": getattr(entity.dxf, "layer", None),
    }

    color = getattr(entity.dxf, "color", None)
    if color is not None:
        data["color"] = color

    entity_type = data["type"]

    if entity_type == "LINE":
        start = getattr(entity.dxf, "start", None)
        end = getattr(entity.dxf, "end", None)
        if start is not None:
            data["start"] = _vec_to_list(start)
        if end is not None:
            data["end"] = _vec_to_list(end)

    elif entity_type == "CIRCLE":
        center = getattr(entity.dxf, "center", None)
        radius = getattr(entity.dxf, "radius", None)
        if center is not None:
            data["center"] = _vec_to_list(center)
        if radius is not None:
            data["radius"] = radius

    elif entity_type == "ARC":
        center = getattr(entity.dxf, "center", None)
        radius = getattr(entity.dxf, "radius", None)
        if center is not None:
            data["center"] = _vec_to_list(center)
        if radius is not None:
            data["radius"] = radius
        data["start_angle"] = getattr(entity.dxf, "start_angle", None)
        data["end_angle"] = getattr(entity.dxf, "end_angle", None)

    elif entity_type == "LWPOLYLINE":
        points = []
        get_points = getattr(entity, "get_points", None)
        if callable(get_points):
            for point in get_points("xy"):
                points.append([float(point[0]), float(point[1])])
        data["points"] = points
        data["closed"] = getattr(entity, "closed", False)

    elif entity_type == "POLYLINE":
        points = []
        for vertex in getattr(entity, "vertices", []):
            location = getattr(vertex.dxf, "location", None)
            if location is not None:
                points.append(_vec_to_list(location))
        data["points"] = points
        data["closed"] = getattr(entity, "is_closed", False)

    elif entity_type == "TEXT":
        data["text"] = getattr(entity.dxf, "text", "")
        insert = getattr(entity.dxf, "insert", None)
        if insert is not None:
            data["insert"] = _vec_to_list(insert)
        data["height"] = getattr(entity.dxf, "height", None)

    elif entity_type == "MTEXT":
        data["text"] = getattr(entity, "text", "")
        insert = getattr(entity.dxf, "insert", None)
        if insert is not None:
            data["insert"] = _vec_to_list(insert)

    elif entity_type == "INSERT":
        data["name"] = getattr(entity.dxf, "name", None)
        insert = getattr(entity.dxf, "insert", None)
        if insert is not None:
            data["insert"] = _vec_to_list(insert)
        xscale = getattr(entity.dxf, "xscale", None)
        yscale = getattr(entity.dxf, "yscale", None)
        zscale = getattr(entity.dxf, "zscale", None)
        if None not in (xscale, yscale, zscale):
            data["scale"] = [xscale, yscale, zscale]

    elif entity_type == "DIMENSION":
        data["dimension_type"] = getattr(entity, "dimtype", None)
        defpoint = getattr(entity.dxf, "defpoint", None)
        if defpoint is not None:
            data["defpoint"] = _vec_to_list(defpoint)

    return data


def _build_result(doc: "Drawing", source_name: str) -> Dict[str, Any]:
    result: Dict[str, Any] = {
        "filename": source_name,
        "version": doc.dxfversion,
        "layers": {},
        "entities": [],
        "blocks": {},
        "statistics": {
            "total_entities": 0,
            "entities_by_type": {},
            "total_layers": 0,
            "total_blocks": 0,
        },
    }

    for layer in doc.layers:
        name = getattr(layer.dxf, "name", None)
        if name is None:
            continue
        result["layers"][name] = {
            "name": name,
            "color": getattr(layer.dxf, "color", None),
            "linetype": getattr(layer.dxf, "linetype", None),
        }
    result["statistics"]["total_layers"] = len(result["layers"])

    msp = doc.modelspace()
    for entity in msp:
        entity_data = _extract_entity_data(entity)
        result["entities"].append(entity_data)

        entity_type = entity_data.get("type")
        if entity_type is None:
            continue
        stats = result["statistics"]["entities_by_type"]
        stats[entity_type] = stats.get(entity_type, 0) + 1

    result["statistics"]["total_entities"] = len(result["entities"])

    for block in doc.blocks:
        name = getattr(block, "name", "")
        if not name or name.startswith("*"):
            continue
        block_entities = [_extract_entity_data(entity) for entity in block]
        result["blocks"][name] = {
            "name": name,
            "entities": block_entities,
        }

    result["statistics"]["total_blocks"] = len(result["blocks"])

    return result


def _convert_bytes_to_result(raw_bytes: bytes, suffix: str, original_name: str) -> Dict[str, Any]:
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as temp_file:
        temp_file.write(raw_bytes)
        temp_path = Path(temp_file.name)

    try:
        try:
            doc = ezdxf.readfile(str(temp_path))  # type: ignore[union-attr]
        except Exception as exc:
            if suffix == ".dwg":
                raise DXFConversionError(
                    "Unable to parse DWG files directly. Convert the file to DXF and retry."
                ) from exc
            raise DXFConversionError("Uploaded file is not a valid DXF document.") from exc

        return _build_result(doc, original_name)
    finally:
        temp_path.unlink(missing_ok=True)


async def convert_dxf_upload_to_json(dxf_file: UploadFile) -> Dict[str, Any]:
    _ensure_dependency()

    filename = dxf_file.filename or "uploaded.dxf"
    suffix = Path(filename).suffix.lower()

    if suffix not in SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="Only .dxf and .dwg files are supported for conversion.",
        )

    raw_bytes = await dxf_file.read()
    if not raw_bytes:
        raise HTTPException(status_code=400, detail=f"Uploaded file '{filename}' is empty.")

    try:
        return _convert_bytes_to_result(raw_bytes, suffix, filename)
    except DXFConversionError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover - unexpected conversion failure
        raise HTTPException(status_code=500, detail=str(exc)) from exc


__all__ = ["convert_dxf_upload_to_json"]


