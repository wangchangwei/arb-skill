# src/models.py
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class AttendanceRecord:
    user_id: str
    check_time: datetime
    location_name: str
    type: str  # "上班" / "下班"
    check_result: str  # "正常" / "异常" / "缺卡"
    comment: str = ""


@dataclass
class AttendanceStats:
    user_id: str
    user_name: str
    period_start: str  # yyyyMMdd
    period_end: str  # yyyyMMdd
    attendance_days: int = 0
    late_count: int = 0
    early_leave_count: int = 0
    overtime_hours: float = 0.0
    leave_days: float = 0.0


@dataclass
class MessageRecord:
    chat_id: str
    sender_id: str
    msg_type: str  # "text" / "image" / "file"
    create_time: datetime
    content: str


@dataclass
class ArbitrationData:
    username: str
    period_start: str
    period_end: str
    attendance_records: list[AttendanceRecord] = field(default_factory=list)
    attendance_stats: list[AttendanceStats] = field(default_factory=list)
    message_records: list[MessageRecord] = field(default_factory=list)
    collected_at: str = ""  # ISO timestamp, filled after collection
