"""Notebook cell helpers."""

BOOT = """
import sys
from pathlib import Path
ROOT = Path.cwd() if (Path.cwd() / "lib").exists() else Path.cwd().parent
sys.path.insert(0, str(ROOT))
""".strip()


def md(text: str):
    return ("md", text)


def code(text: str):
    return ("code", text)
