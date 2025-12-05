"""Add serena submodule to Python path for direct imports."""

import sys
from pathlib import Path

# Add serena src to Python path
_serena_src = Path(__file__).parent / "serena" / "src"
if _serena_src.exists() and str(_serena_src) not in sys.path:
    sys.path.insert(0, str(_serena_src))