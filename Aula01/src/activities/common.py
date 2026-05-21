from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
DATA_PATH = ROOT / "data" / "porto_mock_data.json"
MEMORY_PATH = ROOT / ".agent_memory.jsonl"


def configure_environment() -> None:
    env_path = ROOT / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        if not line or line.strip().startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )


def load_mock_data() -> dict[str, Any]:
    return json.loads(DATA_PATH.read_text(encoding="utf-8"))


def get_model_name(default: str = "gpt-4.1-mini") -> str:
    return os.getenv("OPENAI_MODEL", default)


def has_openai_key() -> bool:
    return bool(os.getenv("OPENAI_API_KEY"))


def normalize(value: str) -> str:
    return value.strip().lower()
