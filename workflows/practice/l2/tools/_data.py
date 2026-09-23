from functools import cache
from pathlib import Path
from typing import Any

import yaml

_DATA_DIR = Path(__file__).parent / "data"


@cache
def load_yaml(filename: str) -> Any:
    """Load a fixture file from ``tools/data/``. Cached: treat the result as read-only."""
    with open(_DATA_DIR / filename) as f:
        return yaml.safe_load(f)
