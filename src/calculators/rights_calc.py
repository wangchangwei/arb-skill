from dataclasses import dataclass, field
from typing import Literal
from datetime import date, datetime, timedelta
from calendar import monthrange


try:
    import chinese_calendar as cc
    HAS_CHINESE_CALENDAR = True
except ImportError:
    HAS_CHINESE_CALENDAR = False


@dataclass
class OvertimeDetail:
    type: Literal["weekday", "rest", "holiday"]
    hours: float
    hourly_rate: float
    multiplier: float
    amount: float
    legal_basis: str


@dataclass
class MonthlyOvertime:
    month: str  # "2026-01"
    month_label: str  # "2026年01月"
    weekday_hours: float
    rest_hours: float
    holiday_hours: float
    workday_count: int  # 该月工作日天数
    holiday_count: int  # 该月法定假日天数
    weekday_pay: float
    rest_pay: float
    holiday_pay: float
    total_pay: float


@dataclass
class CalculationResult:
    base_salary: float
    hourly_rate: float
    daily_rate: float
    work_months: int
    total_overtime_hours: float

    monthly_breakdown: list[MonthlyOvertime] = field(default_factory=list)
    total_overtime_pay: float = 0.0

    unpaid_leave_days: float = 0.0
    unpaid_leave_pay: float = 0.0

    termination_compensation: float = 0.0
    notice_pay: float = 0.0

    no_contract_months: int = 0
    no_contract_pay: float = 0.0

    total_claims: float = 0.0
    calculation_detail: str = ""
    legal_basis: list[str] = field(default_factory=list)


def _get_month_holiday_info(year: int, month: int) -> tuple[int, int]:
    """返回指定月份的(工作日天数, 法定假日天数)。"""
    if not HAS_CHINESE_CALENDAR:
        # Fallback: 估算 22工作日 + 法定假日
        _, days_in_month = monthrange(year, month)
        # 粗估法定假日（春节3天、国庆3天、清明/端午/劳动/中秋各1天 = ~11天均摊到每月）
        return 22, days_in_month - 22

    workday_count = 0
    holiday_count = 0

    first_day = date(year, month, 1)
    _, days_in_month = monthrange(year, month)

    for day in range(1, days_in_month + 1):
        d = date(year, month, day)
        if cc.is_holiday(d):
            holiday_count += 1
        else:
            workday_count += 1

    return workday_count, holiday_count


def _calc_month_overtime(
    hours: float,
    hourly_rate: float,
    workday_hours: float,
    holiday_hours: float,
) -> tuple[float, float, float, float]:
    """按实际工作日/假日拆分，计算加班费。"""
    # 工作日加班 = 工作日加班小时 × 1.5
    workday_pay = round(workday_hours * hourly_rate * 1.5, 2)
    # 休日加班 = 休日加班小时 × 2.0
    rest_pay = round(holiday_hours * hourly_rate * 2.0, 2)

    total = workday_pay + rest_pay
    return workday_hours, holiday_hours, workday_pay, rest_pay, total


def calculate_rights(
    base_salary: float,
    monthly_overtime: dict[str, float] | None = None,
    total_overtime_hours: float | None = None,
    work_months: int = 0,
    daily_rate: float | None = None,
    hourly_rate: float | None = None,
    unpaid_leave_days: float = 0.0,
    no_contract_months: int = 0,
    is_illegal_termination: bool = False,
) -> CalculationResult:
    """
    Calculate labor arbitration claims with monthly overtime breakdown.

    Args:
        base_salary: Monthly salary in CNY.
        monthly_overtime: Dict of month -> total overtime hours, e.g. {"2026-01": 48.5}
                         Key format: "YYYY-MM"
        total_overtime_hours: Fallback total overtime hours if monthly_overtime not provided.
        work_months: Total months worked.
        daily_rate: Daily rate (optional, defaults to base_salary / 21.75).
        hourly_rate: Hourly rate (optional, defaults to base_salary / 21.75 / 8).
        unpaid_leave_days: Unused annual leave days.
        no_contract_months: Months without labor contract.
        is_illegal_termination: Whether termination was illegal.
    """
    daily_rate = daily_rate or (base_salary / 21.75)
    hourly_rate = hourly_rate or (base_salary / 21.75 / 8)

    result = CalculationResult(
        base_salary=base_salary,
        hourly_rate=hourly_rate,
        daily_rate=daily_rate,
        work_months=work_months,
        total_overtime_hours=0.0,
        unpaid_leave_days=unpaid_leave_days,
        no_contract_months=no_contract_months,
    )

    lines = []
    lines.append(f"[Salary Base] Monthly: {base_salary:.2f} CNY, Daily: {daily_rate:.2f} CNY, Hourly: {hourly_rate:.2f} CNY")
    if not HAS_CHINESE_CALENDAR:
        lines.append("[WARNING] chinese-calendar not installed. Using estimated workday/holiday counts.")
    lines.append("")

    # 1. Overtime pay with monthly breakdown
    lines.append("[1. Overtime Pay Calculation (Monthly Breakdown - China Calendar)]")

    monthly_breakdown = []
    total_overtime_pay = 0.0
    grand_total_hours = 0.0

    if monthly_overtime:
        for month_str, hours in sorted(monthly_overtime.items()):
            if hours <= 0:
                continue
            year, mon = map(int, month_str.split('-'))
            month_label = f"{year}年{mon:02d}月"

            # 获取该月工作日/假日数
            workday_count, holiday_count = _get_month_holiday_info(year, mon)

            # 按实际工作日/假日天数比例拆分加班小时
            total_days = workday_count + holiday_count
            if total_days > 0:
                workday_hours = round(hours * workday_count / total_days, 2)
                holiday_hours = round(hours * holiday_count / total_days, 2)
            else:
                workday_hours = hours * 0.9
                holiday_hours = hours * 0.1

            w_h, h_h, w_pay, r_pay, total_m = _calc_month_overtime(
                hours, hourly_rate, workday_hours, holiday_hours
            )

            monthly_breakdown.append(MonthlyOvertime(
                month=month_str,
                month_label=month_label,
                weekday_hours=w_h,
                rest_hours=h_h,
                holiday_hours=0,  # 法定假日单独处理
                workday_count=workday_count,
                holiday_count=holiday_count,
                weekday_pay=w_pay,
                rest_pay=r_pay,
                holiday_pay=0,
                total_pay=total_m,
            ))
            total_overtime_pay += total_m
            grand_total_hours += hours

        for m in monthly_breakdown:
            lines.append(f"  {m.month_label} (工作日{m.workday_count}天, 法定假日{m.holiday_count}天)")
            lines.append(f"    加班{m.weekday_hours + m.rest_hours:.1f}小时 = 工作日{m.weekday_hours:.1f}h + 休日{m.rest_hours:.1f}h")
            lines.append(f"    工作日加班: {m.weekday_hours:.1f}h x {hourly_rate:.2f} x 1.5 = {m.weekday_pay:.2f} CNY")
            lines.append(f"    休日加班: {m.rest_hours:.1f}h x {hourly_rate:.2f} x 2.0 = {m.rest_pay:.2f} CNY")
            lines.append(f"    月度小计: {m.total_pay:.2f} CNY")

        lines.append(f"  ----------------------------------------")
        lines.append(f"  月度加班费合计: {total_overtime_pay:.2f} CNY ({grand_total_hours:.1f}小时)")

    elif total_overtime_hours and total_overtime_hours > 0:
        # Fallback: aggregate
        lines.append(f"  [Aggregate - no monthly breakdown]")
        lines.append(f"  Total: {total_overtime_hours:.1f} hours x {hourly_rate:.2f} CNY/h")
        total_overtime_pay = round(total_overtime_hours * hourly_rate * 1.5, 2)
        lines.append(f"  Estimated (平日): {total_overtime_pay:.2f} CNY")
        grand_total_hours = total_overtime_hours
    else:
        lines.append("  无加班记录")

    result.monthly_breakdown = monthly_breakdown
    result.total_overtime_hours = grand_total_hours
    result.total_overtime_pay = total_overtime_pay
    lines.append("")

    # 2. Unused annual leave
    if unpaid_leave_days > 0:
        result.unpaid_leave_pay = round(unpaid_leave_days * daily_rate * 3.0, 2)
        lines.append("[2. Unused Annual Leave Compensation]")
        lines.append(f"  {unpaid_leave_days:.1f} days x {daily_rate:.2f} x 3.0 = {result.unpaid_leave_pay:.2f} CNY")
        lines.append("  Legal basis: Annual Leave Regulation Art.5 Sec.3")
        lines.append("")
    else:
        lines.append("[2. Unused Annual Leave] None")

    # 3. Illegal termination compensation (2N)
    if is_illegal_termination:
        years = max(1, work_months // 12)
        result.termination_compensation = round(years * 2 * base_salary, 2)
        lines.append("")
        lines.append("[3. Illegal Termination Compensation (2N)]")
        lines.append(f"  {years} years x {base_salary:.2f} x 2 = {result.termination_compensation:.2f} CNY")
        lines.append("  Legal basis: Labor Contract Law Art.87")

    # 4. Notice pay
    result.notice_pay = base_salary
    lines.append("")
    lines.append("[4. Notice Pay]")
    lines.append(f"  1 month salary = {result.notice_pay:.2f} CNY")
    lines.append("  Legal basis: Labor Contract Law Art.40")

    # 5. No contract double pay
    if no_contract_months > 0:
        result.no_contract_months = no_contract_months
        result.no_contract_pay = round(no_contract_months * base_salary, 2)
        lines.append("")
        lines.append("[5. No Contract Double Pay]")
        lines.append(f"  {no_contract_months} months x {base_salary:.2f} = {result.no_contract_pay:.2f} CNY")
        lines.append("  Legal basis: Labor Contract Law Art.82")

    # Total
    result.total_claims = (
        result.total_overtime_pay
        + result.unpaid_leave_pay
        + result.termination_compensation
        + result.notice_pay
        + result.no_contract_pay
    )
    lines.append("")
    lines.append("=" * 50)
    lines.append(f"[TOTAL CLAIMS] {result.total_claims:.2f} CNY")
    lines.append("")
    lines.append("[Legal Basis Summary]")
    legal_basis = [
        "Wage Provision Art.13 - Overtime calculation (平日150%/休日200%/法定假日300%)",
        "Annual Leave Regulation Art.5 - Leave compensation",
        "Labor Contract Law Art.40 - Notice pay",
        "Labor Contract Law Art.44 - Wage payment",
        "Labor Contract Law Art.87 - Illegal termination (2N)",
        "Labor Contract Law Art.82 - No contract double pay",
    ]
    for i, basis in enumerate(legal_basis, 1):
        lines.append(f"  {i}. {basis}")
    result.legal_basis = legal_basis

    result.calculation_detail = "\n".join(lines)
    return result
