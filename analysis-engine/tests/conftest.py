"""Shared pytest configuration for analysis-engine tests.

Adds the analysis-engine root to sys.path so ``models`` and ``parsers``
are importable regardless of the directory pytest is invoked from.
"""

from __future__ import annotations

import sys
from pathlib import Path

_ENGINE_ROOT = Path(__file__).resolve().parent.parent

if str(_ENGINE_ROOT) not in sys.path:
    sys.path.insert(0, str(_ENGINE_ROOT))
