#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import json
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DEFAULT_JSONL = os.path.join(ROOT, "requirements_register.jsonl")


def read_jsonl(path: str):
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            yield json.loads(line)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--jsonl', default=DEFAULT_JSONL)
    p.add_argument('--index', type=int, required=True, help='1-based index')
    args = p.parse_args()

    idx = args.index
    if idx <= 0:
        print(json.dumps({'error': 'index must be >= 1'}))
        return

    for i, obj in enumerate(read_jsonl(args.jsonl), start=1):
        if i == idx:
            print(json.dumps(obj, ensure_ascii=False, indent=2))
            return
    print(json.dumps({'error': f'index out of range (>{i if i else 0})'}))


if __name__ == '__main__':
    main()
