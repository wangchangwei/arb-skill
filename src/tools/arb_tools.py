import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

from src.calculators import calculate_rights, CalculationResult
from src.formatters import JsonFormatter, ExcelFormatter, PdfFormatter
from src.models import ArbitrationData
from src.parsers import parse_attendance_csv, parse_attendance_excel


class _DateTimeEncoder(json.JSONEncoder):
    """JSON encoder that handles datetime objects."""
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)


def _serialize_calculation_result(result: CalculationResult) -> dict:
    """Serialize CalculationResult to dict with ISO datetime strings."""
    d = asdict(result)
    # overtime_details contain OvertimeDetail dataclasses - already flat
    return d


def parse_attendance_structured(file_path: str) -> str:
    """Parse uploaded attendance file (CSV/Excel), returning JSON string.

    Args:
        file_path: Path to the attendance file (CSV or Excel format).

    Returns:
        JSON string with keys:
            - records: list of attendance records (each with ISO check_time)
            - stats: list of attendance stats
            - record_count: number of records parsed
            - stat_count: number of stats parsed

    Supports:
        - CSV files with daily check-in/out flow (headers: 日期, 时间, 地点, 类型, 结果, 备注)
        - CSV files with monthly stats (headers: 员工ID, 姓名, 出勤天数, 迟到次数, ...)
        - Excel files with sheet "打卡流水" or "考勤统计"
    """
    path = Path(file_path)

    if path.suffix.lower() == ".csv":
        content = path.read_text(encoding="utf-8")
        records, stats = parse_attendance_csv(content)
    elif path.suffix.lower() in (".xlsx", ".xls"):
        records, stats = parse_attendance_excel(str(path))
    else:
        raise ValueError(f"Unsupported file format: {path.suffix}. Use .csv or .xlsx")

    # Serialize with ISO datetime strings
    records_data = []
    for rec in records:
        d = asdict(rec)
        d["check_time"] = rec.check_time.isoformat()
        records_data.append(d)

    stats_data = [asdict(s) for s in stats]

    result = {
        "records": records_data,
        "stats": stats_data,
        "record_count": len(records),
        "stat_count": len(stats),
    }
    return json.dumps(result, ensure_ascii=False, indent=2, cls=_DateTimeEncoder)


def calculate_claims(
    base_salary: float,
    overtime_hours: float,
    work_months: int,
    unpaid_leave_days: float = 0,
    no_contract_months: int = 0,
    is_illegal_termination: bool = False,
) -> str:
    """Calculate labor arbitration claims, returning JSON string.

    Args:
        base_salary: Monthly base salary in CNY.
        overtime_hours: Total overtime hours claimed.
        work_months: Total months worked.
        unpaid_leave_days: Unused annual leave days (default 0).
        no_contract_months: Months worked without a labor contract (default 0).
        is_illegal_termination: Whether termination was illegal (default False).
            If True, adds 2N compensation based on years worked.

    Returns:
        JSON string containing:
            - base_salary, hourly_rate, daily_rate, work_months, overtime_hours
            - overtime_details: breakdown of weekday/rest/holiday overtime
            - total_overtime_pay: total overtime payment
            - unpaid_leave_days, unpaid_leave_pay
            - termination_compensation: 2N compensation (if applicable)
            - notice_pay: 1 month salary as notice period pay
            - no_contract_months, no_contract_pay
            - total_claims: sum of all claims
            - calculation_detail: human-readable breakdown
            - legal_basis: list of applicable labor law articles
    """
    result = calculate_rights(
        base_salary=base_salary,
        overtime_hours=overtime_hours,
        work_months=work_months,
        unpaid_leave_days=unpaid_leave_days,
        no_contract_months=no_contract_months,
        is_illegal_termination=is_illegal_termination,
    )

    serialized = _serialize_calculation_result(result)
    return json.dumps(serialized, ensure_ascii=False, indent=2, cls=_DateTimeEncoder)


def export_arbitration_doc(
    data_json: str,
    format: str,
    output_path: str | None = None,
) -> str:
    """Export arbitration evidence document, returning file path.

    Args:
        data_json: JSON string containing ArbitrationData fields:
            - username: employee name
            - period_start: start date (yyyyMMdd)
            - period_end: end date (yyyyMMdd)
            - attendance_records: list of AttendanceRecord (optional)
            - attendance_stats: list of AttendanceStats (optional)
            - message_records: list of MessageRecord (optional)
        format: Output format - "json", "excel", or "pdf"
        output_path: Optional output file path. If None, uses default naming.

    Returns:
        Path to the generated file.

    Raises:
        ValueError: If format is not one of "json", "excel", "pdf".
    """
    data_dict = json.loads(data_json)

    # Parse datetime fields from ISO strings
    for rec in data_dict.get("attendance_records", []):
        if "check_time" in rec and isinstance(rec["check_time"], str):
            rec["check_time"] = datetime.fromisoformat(rec["check_time"])

    for msg in data_dict.get("message_records", []):
        if "create_time" in msg and isinstance(msg["create_time"], str):
            msg["create_time"] = datetime.fromisoformat(msg["create_time"])

    data = ArbitrationData(
        username=data_dict["username"],
        period_start=data_dict["period_start"],
        period_end=data_dict["period_end"],
        attendance_records=data_dict.get("attendance_records", []),
        attendance_stats=data_dict.get("attendance_stats", []),
        message_records=data_dict.get("message_records", []),
        collected_at=data_dict.get("collected_at", datetime.now().isoformat()),
    )

    # Determine output directory
    output_dir = "./output"
    if output_path:
        output_dir = str(Path(output_path).parent)

    if format == "json":
        formatter = JsonFormatter(output_dir=output_dir)
        filepath = formatter.format(data)
        if output_path:
            Path(filepath).rename(output_path)
            filepath = output_path
    elif format == "excel":
        formatter = ExcelFormatter(output_dir=output_dir)
        filepath = formatter.format(data)
        if output_path:
            Path(filepath).rename(output_path)
            filepath = output_path
    elif format == "pdf":
        formatter = PdfFormatter(output_dir=output_dir)
        filepath = formatter.format(data)
        if output_path:
            Path(filepath).rename(output_path)
            filepath = output_path
    else:
        raise ValueError(f"Unsupported format: {format}. Use 'json', 'excel', or 'pdf'.")

    return filepath
