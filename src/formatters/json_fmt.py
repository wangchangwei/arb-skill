# src/formatters/json_fmt.py
import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

from src.models import ArbitrationData


class _DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)


class JsonFormatter:
    def __init__(self, output_dir: str = "./output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def format(self, data: ArbitrationData) -> str:
        filename = f"仲裁证据_{data.username}_{data.period_start}-{data.period_end}.json"
        filepath = self.output_dir / filename

        raw = asdict(data)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(raw, f, ensure_ascii=False, indent=2, cls=_DateTimeEncoder)

        return str(filepath)
