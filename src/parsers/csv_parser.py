import csv
from io import StringIO
from pathlib import Path
from datetime import datetime

from src.models import AttendanceRecord, AttendanceStats


def parse_attendance_csv(content: str) -> tuple[list[AttendanceRecord], list[AttendanceStats]]:
    """
    Parse attendance CSV content.
    Auto-detects format A (daily flow) or format B (monthly stats).
    Returns (records, stats).
    """
    reader = csv.DictReader(StringIO(content))
    rows = list(reader)

    if not rows:
        return [], []

    # Detect format by headers
    headers = set(rows[0].keys())
    if "日期" in headers or "时间" in headers:
        return _parse_daily_flow(rows), []
    else:
        return [], _parse_monthly_stats(rows)


def _parse_daily_flow(rows: list[dict]) -> list[AttendanceRecord]:
    """Format A: daily check-in/out flow."""
    records = []
    for row in rows:
        try:
            date_str = row.get("日期", "").strip()
            time_str = row.get("时间", "").strip()
            if not date_str:
                continue

            check_time_str = f"{date_str} {time_str}" if time_str else date_str
            try:
                check_time = datetime.strptime(check_time_str, "%Y-%m-%d %H:%M")
            except ValueError:
                check_time = datetime.strptime(date_str, "%Y-%m-%d")

            records.append(AttendanceRecord(
                user_id=row.get("员工ID", "").strip(),
                check_time=check_time,
                location_name=row.get("地点", "").strip(),
                type=row.get("类型", "").strip(),
                check_result=row.get("结果", "正常").strip(),
                comment=row.get("备注", "").strip(),
            ))
        except Exception:
            continue
    return records


def _parse_monthly_stats(rows: list[dict]) -> list[AttendanceStats]:
    """Format B: monthly attendance summary."""
    stats = []
    for row in rows:
        try:
            user_id = row.get("员工ID", row.get("user_id", "")).strip()
            user_name = row.get("姓名", row.get("name", user_id)).strip()
            if not user_id and not user_name:
                continue

            def safe_float(val):
                try:
                    v = val.strip()
                    if "h" in v.lower():
                        v = v.lower().replace("h", "").strip()
                    return float(v)
                except (ValueError, AttributeError):
                    return 0.0

            def safe_int(val):
                try:
                    return int(float(safe_float(val)))
                except (ValueError, AttributeError):
                    return 0

            stat = AttendanceStats(
                user_id=user_id,
                user_name=user_name,
                period_start=row.get("开始日期", "").strip(),
                period_end=row.get("结束日期", "").strip(),
                attendance_days=safe_int(row.get("出勤天数", row.get("attendance_days", 0))),
                late_count=safe_int(row.get("迟到次数", row.get("late_count", 0))),
                early_leave_count=safe_int(row.get("早退次数", row.get("early_leave_count", 0))),
                overtime_hours=safe_float(row.get("加班时长", row.get("overtime_hours", 0))),
                leave_days=safe_float(row.get("请假天数", row.get("leave_days", 0))),
            )
            stats.append(stat)
        except Exception:
            continue
    return stats
