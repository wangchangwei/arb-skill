# tests/test_json_fmt.py
import json
from datetime import datetime
from pathlib import Path
from src.formatters.json_fmt import JsonFormatter
from src.models import ArbitrationData, AttendanceRecord


def _sample_data():
    return ArbitrationData(
        username="张三",
        period_start="202403",
        period_end="202406",
        attendance_records=[
            AttendanceRecord(
                user_id="u_001",
                check_time=datetime(2024, 3, 15, 9, 0, 0),
                location_name="杭州总部",
                type="上班",
                check_result="正常",
            )
        ],
        collected_at="2024-07-01T10:00:00",
    )


def test_json_output_creates_file(tmp_path):
    formatter = JsonFormatter(output_dir=str(tmp_path))
    path = formatter.format(_sample_data())
    assert Path(path).exists()
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["username"] == "张三"
    assert len(data["attendance_records"]) == 1


def test_json_filename_format(tmp_path):
    formatter = JsonFormatter(output_dir=str(tmp_path))
    path = formatter.format(_sample_data())
    assert "仲裁证据_张三_202403-202406.json" in path


def test_json_datetime_serialized_as_iso(tmp_path):
    formatter = JsonFormatter(output_dir=str(tmp_path))
    formatter.format(_sample_data())
    with open(
        tmp_path / "仲裁证据_张三_202403-202406.json", "r", encoding="utf-8"
    ) as f:
        data = json