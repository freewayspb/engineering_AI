#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import json
import zipfile
import os
import sys
import xml.etree.ElementTree as ET

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DEFAULT_XLSX = os.path.join(ROOT, "requirements_register.xlsx")


def read_rows_from_xlsx(xlsx_path: str):
    with zipfile.ZipFile(xlsx_path, 'r') as z:
        sheet_xml = z.read('xl/worksheets/sheet1.xml')
    # Parse XML (inline strings t="inlineStr")
    ns = {
        'main': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'
    }
    root = ET.fromstring(sheet_xml)
    rows = []
    for row_el in root.findall('.//main:sheetData/main:row', ns):
        cells = []
        for c in row_el.findall('main:c', ns):
            t = c.get('t')
            if t == 'inlineStr':
                is_el = c.find('main:is', ns)
                t_el = is_el.find('main:t', ns) if is_el is not None else None
                cells.append(t_el.text if t_el is not None else '')
            else:
                # Treat missing type as empty text
                v_el = c.find('main:v', ns)
                cells.append(v_el.text if v_el is not None else '')
        rows.append(cells)
    if not rows:
        return []
    headers = rows[0]
    data_rows = []
    for r in rows[1:]:
        row_dict = {}
        for i, h in enumerate(headers):
            key = h if h else f"col{i+1}"
            val = r[i] if i < len(r) else ''
            row_dict[key] = val
        data_rows.append(row_dict)
    return data_rows


def main():
    parser = argparse.ArgumentParser(description='Read requirements rows from minimal XLSX.')
    parser.add_argument('--xlsx', default=DEFAULT_XLSX, help='Path to requirements_register.xlsx')
    parser.add_argument('--index', type=int, default=None, help='1-based index of the requirement to output')
    parser.add_argument('--limit', type=int, default=None, help='Limit number of rows to output')
    args = parser.parse_args()

    if not os.path.exists(args.xlsx):
        print(json.dumps({'error': f'File not found: {args.xlsx}'}))
        sys.exit(1)

    rows = read_rows_from_xlsx(args.xlsx)

    if args.index is not None:
        idx = args.index - 1
        if idx < 0 or idx >= len(rows):
            print(json.dumps({'error': f'Index out of range (1..{len(rows)})'}))
            sys.exit(1)
        print(json.dumps(rows[idx], ensure_ascii=False, indent=2))
        return

    if args.limit is not None:
        rows = rows[: args.limit]

    print(json.dumps({'total': len(rows), 'rows': rows}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
