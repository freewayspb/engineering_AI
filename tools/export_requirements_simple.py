#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import csv
import json
import zipfile
import xml.etree.ElementTree as ET

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
XLSX = os.path.join(ROOT, "requirements_register.xlsx")
JSONL = os.path.join(ROOT, "requirements_register.jsonl")
CSV = os.path.join(ROOT, "requirements_register.csv")

COLS = [
    "Req_ID",
    "Category",
    "Name",
    "Description",
    "Source_File",
    "Section_Path",
    "Related_Artifacts",
]


def read_rows_from_xlsx(xlsx_path: str):
    with zipfile.ZipFile(xlsx_path, 'r') as z:
        sheet_xml = z.read('xl/worksheets/sheet1.xml')
    ns = {'m': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
    root = ET.fromstring(sheet_xml)
    rows = []
    for row_el in root.findall('.//m:sheetData/m:row', ns):
        cells = []
        for c in row_el.findall('m:c', ns):
            # inlineStr
            t = c.get('t')
            if t == 'inlineStr':
                t_el = c.find('m:is/m:t', ns)
                cells.append(t_el.text if t_el is not None else '')
            else:
                v_el = c.find('m:v', ns)
                cells.append(v_el.text if v_el is not None else '')
        rows.append(cells)
    if not rows:
        return []
    headers = rows[0]
    data_rows = []
    for r in rows[1:]:
        row = {}
        for i, h in enumerate(headers):
            key = h if h else f"col{i+1}"
            val = r[i] if i < len(r) else ''
            row[key] = val
        data_rows.append(row)
    return data_rows


def main():
    rows = read_rows_from_xlsx(XLSX)
    # Write JSONL
    with open(JSONL, 'w', encoding='utf-8') as f:
        for r in rows:
            obj = {k: r.get(k, '') for k in COLS}
            f.write(json.dumps(obj, ensure_ascii=False) + "\n")
    # Write CSV
    with open(CSV, 'w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, fieldnames=COLS)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, '') for k in COLS})
    print(json.dumps({
        'exported': len(rows),
        'jsonl': JSONL,
        'csv': CSV,
    }, ensure_ascii=False))


if __name__ == '__main__':
    main()
