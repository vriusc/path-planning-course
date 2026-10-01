#!/usr/bin/env python3
"""Generate textbook notebooks. From repo root: python tools/build_notebooks.py"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
OUT = ROOT / "notebooks"
OUT.mkdir(exist_ok=True)

from tools.l00_09 import LESSONS_00_09
from tools.l10_28 import LESSONS_10_28


def cells(*parts):
    out = []
    for p in parts:
        if p[0] == "md":
            out.append({"cell_type": "markdown", "metadata": {}, "source": p[1].strip() + "\n"})
        else:
            out.append(
                {
                    "cell_type": "code",
                    "metadata": {},
                    "execution_count": None,
                    "outputs": [],
                    "source": p[1].strip() + "\n",
                }
            )
    return out


def nb(title, body):
    return {
        "nbformat": 4,
        "nbformat_minor": 5,
        "metadata": {
            "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
            "language_info": {"name": "python", "pygments_lexer": "ipython3"},
        },
        "cells": cells(("md", f"# {title}"), *body),
    }


def main():
    lessons = LESSONS_00_09 + LESSONS_10_28
    for name, title, body in lessons:
        path = OUT / f"{name}.ipynb"
        path.write_text(json.dumps(nb(title, body), ensure_ascii=False, indent=1), encoding="utf-8")
        print("wrote", path.name, "cells", 1 + len(body))
    print("total", len(lessons))


if __name__ == "__main__":
    main()
