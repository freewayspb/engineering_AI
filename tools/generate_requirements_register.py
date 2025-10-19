#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import sys
import json
import zipfile
from datetime import datetime

# Workspace root discovery (default to current working directory)
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

# Input files
FILES = [
    os.path.join(ROOT, "documentation/02-requirements/business-requirements.md"),
    os.path.join(ROOT, "documentation/02-requirements/technical-requirements.md"),
    os.path.join(ROOT, "documentation/02-requirements/use-cases.md"),
]

OUTPUT_XLSX = os.path.join(ROOT, "requirements_register.xlsx")

# Columns for the register
COLUMNS = [
    "Req_ID",
    "Category",
    "Name",
    "Description",
    "Source_File",
    "Section_Path",
    "Related_Artifacts",
]


def read_text(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def normalize_whitespace(text: str) -> str:
    # Collapse multiple spaces and trim lines
    lines = [re.sub(r"\s+", " ", ln).strip() for ln in text.splitlines()]
    # Keep empty lines as separators but avoid multiple empty lines
    result = []
    last_empty = False
    for ln in lines:
        if ln == "":
            if not last_empty:
                result.append("")
            last_empty = True
        else:
            result.append(ln)
            last_empty = False
    return "\n".join(result).strip()


def extract_headings_with_path(md_text: str):
    # Return list of (line_index, level, heading_text)
    headings = []
    for idx, line in enumerate(md_text.splitlines()):
        m = re.match(r"^(#{1,6})\s+(.*)$", line)
        if m:
            level = len(m.group(1))
            text = m.group(2).strip()
            headings.append((idx, level, text))
    return headings


def build_section_path(headings, occurrence_line: int) -> str:
    # Find nearest headings above the occurrence and build path using their texts
    parents = []
    for idx, level, text in reversed(headings):
        if idx < occurrence_line:
            # include up to level 3 for compact path
            if level <= 3:
                parents.append(text)
    parents = list(reversed(parents[-3:]))
    return " → ".join(parents)


def parse_brd(path: str):
    text = read_text(path)
    headings = extract_headings_with_path(text)
    rows = []

    # Pattern for BR entries in headings level 4: #### BR-123: Title
    pattern = re.compile(r"^####\s*(BR-\d{3,})\s*:\s*(.+)$")

    lines = text.splitlines()
    for i, line in enumerate(lines):
        m = pattern.match(line.strip())
        if not m:
            continue
        req_id = m.group(1).strip()
        name = m.group(2).strip()

        # Description: collect following lines until next heading of same/higher level (#### or higher) or blank line group end
        desc_lines = []
        j = i + 1
        while j < len(lines):
            ln = lines[j]
            if re.match(r"^###", ln):
                break
            if re.match(r"^####", ln):
                break
            # stop section when a major divider appears
            desc_lines.append(ln)
            j += 1
        description = normalize_whitespace("\n".join(desc_lines).strip())
        if not description:
            description = name

        section_path = f"business-requirements.md → {build_section_path(headings, i)}"

        # Related artifacts: search local block for references
        related = []
        block = "\n".join(lines[i:j])
        if "metrics.md" in block:
            related.append("metrics.md")
        if "prototype" in block.lower() or "прототип" in block.lower():
            related.append("documentation/03-prototypes/")
        if not related:
            related_str = "-"
        else:
            # unique preserve order
            seen = set()
            tmp = []
            for r in related:
                if r not in seen:
                    tmp.append(r)
                    seen.add(r)
            related_str = ", ".join(tmp)

        rows.append({
            "Req_ID": req_id,
            "Category": "BR",
            "Name": name,
            "Description": description,
            "Source_File": "business-requirements.md",
            "Section_Path": section_path,
            "Related_Artifacts": related_str,
        })

    return rows


def parse_srs(path: str):
    text = read_text(path)
    headings = extract_headings_with_path(text)
    rows = []

    lines = text.splitlines()

    # FR lines like: - FR-LEARN-01: Description...
    fr_pattern = re.compile(r"^-\s*(FR-[A-Z]+-\d{2,}|FR-[A-Z]+-\d{2,}|FR-[A-Z]+\d*|FR-[A-Z]+-[A-Z]+-\d+|FR-[A-Z]+-\d+)\s*:\s*(.+)$")
    # Also allow FR-LOG-01 etc.
    fr_pattern_generic = re.compile(r"^-\s*(FR-[A-Z]+(?:-[A-Z]+)?-\d{2,})\s*:\s*(.+)$")

    # Track current section path context
    current_section_line = 0

    for i, line in enumerate(lines):
        if re.match(r"^### ", line) or re.match(r"^#### ", line):
            current_section_line = i

        m = fr_pattern_generic.match(line.strip()) or fr_pattern.match(line.strip())
        if not m:
            continue
        req_id = m.group(1).strip()
        full_desc = m.group(2).strip()

        # Split name and description: before first dot as name if Cyrillic, else use phrase before first semicolon/parenthesis or up to 120 chars
        name = full_desc
        # heuristic: name up to 120 chars or until first period
        period_pos = full_desc.find(".")
        if 10 <= period_pos <= 120:
            name = full_desc[:period_pos].strip()
        elif len(full_desc) > 120:
            name = full_desc[:120].strip()

        # Gather following lines until next list item or blank or new heading to enrich description
        desc_lines = [full_desc]
        j = i + 1
        while j < len(lines):
            ln = lines[j]
            if re.match(r"^\s*-\s*FR-", ln):
                break
            if re.match(r"^### ", ln) or re.match(r"^#### ", ln):
                break
            if re.match(r"^\s*Связанные UC\s*:\s*", ln):
                # capture related
                related_line = ln
                # also consider next line if same paragraph
                pass
            desc_lines.append(ln)
            j += 1
        description = normalize_whitespace("\n".join(desc_lines).strip())

        # Related artifacts: capture explicit "Связанные UC:" line within local block
        related = []
        block = "\n".join(lines[i:j])
        rel_m = re.search(r"Связанные UC\s*:\s*([^\n]+)", block)
        if rel_m:
            related.append(rel_m.group(1).strip())
        if "metrics.md" in block:
            related.append("metrics.md")
        section_path = f"technical-requirements.md → {build_section_path(headings, current_section_line)}"

        if not related:
            related_str = "-"
        else:
            seen = set()
            tmp = []
            for r in related:
                if r not in seen:
                    tmp.append(r)
                    seen.add(r)
            related_str = ", ".join(tmp)

        rows.append({
            "Req_ID": req_id,
            "Category": "FR",
            "Name": name,
            "Description": description,
            "Source_File": "technical-requirements.md",
            "Section_Path": section_path,
            "Related_Artifacts": related_str,
        })

    return rows


def parse_use_cases(path: str):
    text = read_text(path)
    headings = extract_headings_with_path(text)
    rows = []

    lines = text.splitlines()

    # Headings like: ### UC-01 | Name
    uc_head_pattern = re.compile(r"^###\s*(UC-[0-9A-Za-z]+)\s*\|\s*(.+)$")

    for i, line in enumerate(lines):
        m = uc_head_pattern.match(line.strip())
        if not m:
            continue
        req_id = m.group(1).strip()
        name = m.group(2).strip()

        # Description: look for '**Краткое описание**: ...' then collect until next '### '
        desc_lines = []
        j = i + 1
        while j < len(lines):
            ln = lines[j]
            if re.match(r"^### ", ln):
                break
            desc_match = re.match(r"^\*\*Краткое описание\*\*:\s*(.*)$", ln)
            if desc_match:
                desc_lines.append(desc_match.group(1).strip())
            # Also include 'Основной сценарий' in one-liner form
            main_match = re.match(r"^\*\*Основной сценарий\*\*:\s*(.*)$", ln)
            if main_match:
                desc_lines.append("Main: " + main_match.group(1).strip())
            j += 1
        description = normalize_whitespace("\n".join(desc_lines).strip())
        if not description:
            # fallback: take first paragraph
            k = i + 1
            temp = []
            while k < len(lines) and lines[k].strip() != "":
                temp.append(lines[k])
                k += 1
            description = normalize_whitespace("\n".join(temp).strip())
            if not description:
                description = name

        # Related artifacts: look for lines mentioning 'Traceability:' or 'Acceptance:' in the block
        block = "\n".join(lines[i:j])
        related = []
        tr = re.search(r"Traceability:\s*(.+)$", block, re.MULTILINE)
        if tr:
            related.append(tr.group(1).strip())
        if "metrics.md" in block:
            related.append("metrics.md")
        section_path = f"use-cases.md → {build_section_path(headings, i)}"

        related_str = "-" if not related else ", ".join(dict.fromkeys(related))

        rows.append({
            "Req_ID": req_id,
            "Category": "UC",
            "Name": name,
            "Description": description,
            "Source_File": "use-cases.md",
            "Section_Path": section_path,
            "Related_Artifacts": related_str,
        })

    return rows


# Minimal XLSX writer (no external dependencies) using inline strings

def xml_escape(value: str) -> str:
    return (
        value.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace("\"", "&quot;")
        .replace("'", "&apos;")
    )


def build_sheet_xml(headers, rows):
    # Build worksheet XML with inline strings
    cols = len(headers)
    rows_count = 1 + len(rows)

    def col_ref(col_idx: int) -> str:
        # Convert 1-based column index to Excel letters
        s = ""
        x = col_idx
        while x:
            x, r = divmod(x - 1, 26)
            s = chr(65 + r) + s
        return s

    xml = []
    xml.append('<?xml version="1.0" encoding="UTF-8"?>')
    xml.append('<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">')
    xml.append('<sheetData>')

    # Header row (r=1)
    xml.append('<row r="1">')
    for c_idx, h in enumerate(headers, start=1):
        cell_ref = f"{col_ref(c_idx)}1"
        xml.append(f'<c r="{cell_ref}" t="inlineStr"><is><t>{xml_escape(str(h))}</t></is></c>')
    xml.append('</row>')

    # Data rows
    for r_idx, row in enumerate(rows, start=2):
        xml.append(f'<row r="{r_idx}">')
        for c_idx, h in enumerate(headers, start=1):
            cell_ref = f"{col_ref(c_idx)}{r_idx}"
            val = row.get(h, "")
            xml.append(f'<c r="{cell_ref}" t="inlineStr"><is><t>{xml_escape(str(val))}</t></is></c>')
        xml.append('</row>')

    xml.append('</sheetData>')
    xml.append('</worksheet>')
    return "".join(xml)


def build_workbook_xml():
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
        '<sheets>'
        '<sheet name="Requirements" sheetId="1" r:id="rId1"/>'
        '</sheets>'
        '</workbook>'
    )


def build_workbook_rels_xml():
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" '
        'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" '
        'Target="worksheets/sheet1.xml"/>'
        '</Relationships>'
    )


def build_content_types_xml():
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
        '<Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
        '</Types>'
    )


def build_root_rels_xml():
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" '
        'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" '
        'Target="/xl/workbook.xml"/>'
        '</Relationships>'
    )


def write_minimal_xlsx(headers, rows, out_path):
    sheet_xml = build_sheet_xml(headers, rows)
    workbook_xml = build_workbook_xml()
    workbook_rels_xml = build_workbook_rels_xml()
    content_types_xml = build_content_types_xml()
    root_rels_xml = build_root_rels_xml()

    with zipfile.ZipFile(out_path, "w", compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", content_types_xml)
        z.writestr("_rels/.rels", root_rels_xml)
        z.writestr("xl/workbook.xml", workbook_xml)
        z.writestr("xl/_rels/workbook.xml.rels", workbook_rels_xml)
        z.writestr("xl/worksheets/sheet1.xml", sheet_xml)


def ensure_unique_ids(rows):
    seen = set()
    unique_rows = []
    for r in rows:
        key = (r["Req_ID"], r["Category"], r["Source_File"])
        if key in seen:
            # skip duplicates
            continue
        seen.add(key)
        unique_rows.append(r)
    return unique_rows


def main():
    all_rows = []

    # Parse BR
    try:
        all_rows.extend(parse_brd(FILES[0]))
    except Exception as e:
        print(f"WARN: Failed to parse BRD: {e}", file=sys.stderr)

    # Parse FR
    try:
        all_rows.extend(parse_srs(FILES[1]))
    except Exception as e:
        print(f"WARN: Failed to parse SRS: {e}", file=sys.stderr)

    # Parse UC
    try:
        all_rows.extend(parse_use_cases(FILES[2]))
    except Exception as e:
        print(f"WARN: Failed to parse Use Cases: {e}", file=sys.stderr)

    # Deduplicate
    all_rows = ensure_unique_ids(all_rows)

    # Sort by category order and then Req_ID natural
    cat_order = {"BR": 0, "FR": 1, "UC": 2}

    def id_key(req_id: str) -> tuple:
        # Extract numbers for sorting; fallback to string
        nums = re.findall(r"\d+", req_id)
        return tuple(int(n) for n in nums) if nums else (req_id,)

    all_rows.sort(key=lambda r: (cat_order.get(r["Category"], 9), id_key(r["Req_ID"])) )

    # Write XLSX
    write_minimal_xlsx(COLUMNS, all_rows, OUTPUT_XLSX)

    # Emit brief stats JSON to stdout
    stats = {
        "total": len(all_rows),
        "by_category": {
            "BR": sum(1 for r in all_rows if r["Category"] == "BR"),
            "FR": sum(1 for r in all_rows if r["Category"] == "FR"),
            "UC": sum(1 for r in all_rows if r["Category"] == "UC"),
        },
        "output": OUTPUT_XLSX,
        "generated_at": datetime.utcnow().isoformat() + "Z",
    }
    print(json.dumps(stats, ensure_ascii=False))


if __name__ == "__main__":
    main()
