#!/usr/bin/env python3
"""Validate course-map invariants without requiring PyYAML."""

from __future__ import annotations

import re
from pathlib import Path


def main() -> int:
    text = Path("course/course-map.yml").read_text(encoding="utf-8")
    hours = [int(value) for value in re.findall(r"^    hours: (\d+)$", text, re.MULTILINE)]
    if not hours or sum(hours) != 40:
        print(f"course hours must total 40 (found {sum(hours)})")
        return 1
    for lab in re.findall(r"labs: \[([^]]+)\]", text):
        for name in (part.strip() for part in lab.split(",")):
            if not Path("course/labs", name).is_dir():
                print(f"missing lab directory: {name}")
                return 1
    print(f"course map OK ({len(hours)} modules, {sum(hours)} hours)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
