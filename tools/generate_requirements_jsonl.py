#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import json
from datetime import datetime

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
FILES = [
    os.path.join(ROOT, "documentation/02-requirements/business-requirements.md"),
    os.path.join(ROOT, "documentation/02-requirements/technical-requirements.md"),
    os.path.join(ROOT, "documentation/02-requirements/use-cases.md"),
]
OUT_JSONL = os.path.join(ROOT, "requirements_register.jsonl")

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
    import re as _re
    lines = [_re.sub(r"\s+", " ", ln).strip() for ln in text.splitlines()]
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
    headings = []
    for idx, line in enumerate(md_text.splitlines()):
        m = re.match(r"^(#{1,6})\s+(.*)$", line)
        if m:
            level = len(m.group(1))
            text = m.group(2).strip()
            headings.append((idx, level, text))
    return headings


def build_section_path(headings, occurrence_line: int) -> str:
    parents = []
    for idx, level, text in reversed(headings):
        if idx < occurrence_line and level <= 3:
            parents.append(text)
    parents = list(reversed(parents[-3:]))
    return " → ".join(parents)


def parse_brd(path: str):
    text = read_text(path)
    headings = extract_headings_with_path(text)
    rows = []
    pattern = re.compile(r"^####\s*(BR-\d{3,}|PT-\d{3,})\s*:\s*(.+)$")
    lines = text.splitlines()
    for i, line in enumerate(lines):
        m = pattern.match(line.strip())
        if not m:
            continue
        req_id = m.group(1).strip()
        category = "BR" if req_id.startswith("BR-") else None
        if category is None:
            # skip PT-### from the product register
            continue
        name = m.group(2).strip()
        desc_lines = []
        j = i + 1
        while j < len(lines):
            ln = lines[j]
            if re.match(r"^###", ln) or re.match(r"^####", ln):
                break
            desc_lines.append(ln)
            j += 1
        description = normalize_whitespace("\n".join(desc_lines).strip()) or name
        section_path = f"business-requirements.md → {build_section_path(headings, i)}"
        related = []
        block = "\n".join(lines[i:j])
        if "metrics.md" in block:
            related.append("metrics.md")
        related_str = "-" if not related else ", ".join(dict.fromkeys(related))
        rows.append({
            "Req_ID": req_id,
            "Category": category,
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
    fr_pattern = re.compile(r"^-\s*(FR-[A-Z]+(?:-[A-Z]+)?-\d{2,})\s*:\s*(.+)$")
    current_section_line = 0
    for i, line in enumerate(lines):
        if re.match(r"^### ", line) or re.match(r"^#### ", line):
            current_section_line = i
        m = fr_pattern.match(line.strip())
        if not m:
            continue
        req_id = m.group(1).strip()
        full_desc = m.group(2).strip()
        # name heuristic
        name = full_desc.split(".")[0]
        if len(name) > 120:
            name = name[:120]
        desc_lines = [full_desc]
        j = i + 1
        while j < len(lines):
            ln = lines[j]
            if re.match(r"^\s*-\s*FR-", ln):
                break
            if re.match(r"^### ", ln) or re.match(r"^#### ", ln):
                break
            desc_lines.append(ln)
            j += 1
        description = normalize_whitespace("\n".join(desc_lines).strip())
        related = []
        block = "\n".join(lines[i:j])
        rel_m = re.search(r"Связанные UC\s*:\s*([^\n]+)", block)
        if rel_m:
            related.append(rel_m.group(1).strip())
        if "metrics.md" in block:
            related.append("metrics.md")
        section_path = f"technical-requirements.md → {build_section_path(headings, current_section_line)}"
        related_str = "-" if not related else ", ".join(dict.fromkeys(related))
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
    uc_head_pattern = re.compile(r"^###\s*(UC-[0-9A-Za-z]+)\s*\|\s*(.+)$")
    for i, line in enumerate(lines):
        m = uc_head_pattern.match(line.strip())
        if not m:
            continue
        req_id = m.group(1).strip()
        name = m.group(2).strip()
        desc_lines = []
        j = i + 1
        while j < len(lines):
            ln = lines[j]
            if re.match(r"^### ", ln):
                break
            # capture brief parts
            for key in ["**Краткое описание**:", "**Основной сценарий**:"]:
                if ln.startswith(key):
                    desc_lines.append(ln[len(key):].strip())
            j += 1
        description = normalize_whitespace("\n".join(desc_lines).strip()) or name
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


def ensure_unique_ids(rows):
    seen = set()
    unique = []
    for r in rows:
        key = (r["Req_ID"], r["Category"], r["Source_File"])
        if key in seen:
            continue
        seen.add(key)
        unique.append(r)
    return unique


def main():
    rows = []
    rows.extend(parse_brd(FILES[0]))
    rows.extend(parse_srs(FILES[1]))
    rows.extend(parse_use_cases(FILES[2]))
    rows = ensure_unique_ids(rows)
    # sort
    cat_order = {"BR": 0, "FR": 1, "UC": 2}
    def id_key(req_id: str):
        import re as _re
        nums = _re.findall(r"\d+", req_id)
        return tuple(int(n) for n in nums) if nums else (req_id,)
    rows.sort(key=lambda r: (cat_order.get(r["Category"], 9), id_key(r["Req_ID"])) )

    with open(OUT_JSONL, 'w', encoding='utf-8') as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    print(json.dumps({
        'total': len(rows),
        'jsonl': OUT_JSONL,
        'generated_at': datetime.utcnow().isoformat() + 'Z'
    }, ensure_ascii=False))


if __name__ == '__main__':
    main()
