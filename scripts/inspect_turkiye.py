#!/usr/bin/env python3
"""Legacy entry point for canonical ingestion and its complete quality report.

Prefer ``python -m src.data.turkiye`` from the repository root.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.data.turkiye import main


if __name__ == "__main__":
    main()
