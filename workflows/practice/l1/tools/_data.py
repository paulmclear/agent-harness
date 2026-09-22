from functools import cache
from pathlib import Path

import yaml

_DATA_DIR = Path(__file__).parent / "data"


@cache
def load(filename: str) -> list[dict]:
    with open(_DATA_DIR / filename) as f:
        return yaml.safe_load(f)
