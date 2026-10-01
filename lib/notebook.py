"""Helpers used at the top of every lesson notebook."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def studio():
    from lib.studio.widget import PlannerStudio

    return PlannerStudio()
