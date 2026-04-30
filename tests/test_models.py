# tests/test_models.py
from datetime import datetime
from src.models import (
    AttendanceRecord,
    AttendanceStats,
    MessageRecord,
    ArbitrationData,
)


def test_attendance_record_creation():
    record = AttendanceRecord(
        user_id="u_001",
        check_time=datetime(2024, 3, 15, 9, 0, 0),
        location_name="杭州总部",
        type="上班",
        check_result="正常",
        comment="",
    )
    assert record.user_id == "u_001"
    assert record.type == "上班"
    assert record.check_result == "正常"


def test_attendance_stats_defaults():
    stats = AttendanceStats(
        user_id="u_001",
        user_name="张三",
        period_start="20240301",
        period_end="20240331",
    )
    assert stats.attendance_days == 0
    assert stats.late_count == 0
    assert stats.overtime_hours == 0.0


def test_message_record_creation():
    msg = MessageRecord(
        chat_id="oc_001",
        sender_id="u_001",
        msg_type="text",
        create_time=datetime(2024, 3, 15, 10, 30, 0),
        content="明天加班",
    )
    assert msg.msg_type == "text"
    assert msg.content == "明天加班"


def test_arbitration_data_aggregates():
    data = ArbitrationData(
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
    )
    assert len(data.attendance_records) == 1
    assert data.collected_at == ""
