from dataclasses import dataclass, field
from typing import Literal


@dataclass
class SalaryDiscrepancy:
    actual_salary: float           # 实际月薪（证据：工资流水）
    declared_salary: float         # 社保申报基数（证据：社保缴费记录）
    monthly_social_gap: float     # 每月社保差额
    monthly_housing_gap: float    # 每月公积金差额
    monthly_total_gap: float     # 每月总差额
    work_months: int             # 工作月数
    total_gap: float             # 累计差额
    legal_basis: list[str] = field(default_factory=list)


@dataclass
class SocialSecurityAnalysis:
    actual_salary: float         # 实际月薪
    declared_salary: float        # 申报基数
    social_rate: float           # 社保公司缴纳比例（约31%）
    housing_rate: float          # 公积金公司缴纳比例（5%-12%）
    monthly_social_gap: float    # 每月社保差额
    monthly_housing_gap: float   # 每月公积金差额
    total_social_gap: float     # 累计社保差额
    total_housing_gap: float     # 累计公积金差额
    total_gap: float             # 累计总差额
    can_claim_compensation: bool # 能否主张经济补偿金
    compensation_months: int     # 经济补偿金月数


# 北京2026年社保基数上下限（参考）
# 实际计算时需用户提供当地社保缴费记录
DEFAULT_SOCIAL_RATE = 0.305  # 养老16%+医疗10%+失业0.5%+工伤0.4%+生育0.8% ≈ 27.7%，取整约30.5%
DEFAULT_HOUSING_RATE = 0.12   # 公积金通常12%


def analyze_social_security(
    actual_salary: float,
    declared_salary: float,
    work_months: int,
    social_rate: float = DEFAULT_SOCIAL_RATE,
    housing_rate: float = DEFAULT_HOUSING_RATE,
) -> SalaryDiscrepancy:
    """
    分析社保/公积金缴纳不足的差额及可主张权益。

    Args:
        actual_salary: 实际月薪（从工资流水获取）
        declared_salary: 社保申报基数（从社保缴费记录获取）
        work_months: 工作月数
        social_rate: 社保公司缴纳比例（默认30.5%）
        housing_rate: 公积金公司缴纳比例（默认12%）

    Returns:
        SalaryDiscrepancy with gap analysis and claimable amounts.
    """
    if declared_salary >= actual_salary:
        return SalaryDiscrepancy(
            actual_salary=actual_salary,
            declared_salary=declared_salary,
            monthly_social_gap=0.0,
            monthly_housing_gap=0.0,
            monthly_total_gap=0.0,
            work_months=work_months,
            total_gap=0.0,
            legal_basis=["《社会保险法》第12条：用人单位应按工资总额缴纳社保"],
        )

    # 每月差额
    monthly_social_gap = round((actual_salary - declared_salary) * social_rate, 2)
    monthly_housing_gap = round((actual_salary - declared_salary) * housing_rate, 2)
    monthly_total_gap = monthly_social_gap + monthly_housing_gap

    # 累计差额
    total_social_gap = round(monthly_social_gap * work_months, 2)
    total_housing_gap = round(monthly_housing_gap * work_months, 2)
    total_gap = total_social_gap + total_housing_gap

    # 经济补偿金：因未缴社保被迫离职可主张
    years = work_months / 12
    compensation_months = max(1, int(years)) if years >= 1 else 1
    can_claim = True  # 未依法缴纳社保，员工可被迫解除合同主张补偿

    legal_basis = [
        "《社会保险法》第12条 — 用人单位按工资总额缴纳社保",
        "《劳动合同法》第38条 — 未依法缴纳社保，员工可解除合同",
        "《劳动合同法》第46条 — 解除合同应支付经济补偿",
        "《劳动合同法》第47条 — 经济补偿按工作年限计算",
        "《住房公积金管理条例》第16条 — 公积金缴存额按工资计算",
    ]

    return SalaryDiscrepancy(
        actual_salary=actual_salary,
        declared_salary=declared_salary,
        monthly_social_gap=monthly_social_gap,
        monthly_housing_gap=monthly_housing_gap,
        monthly_total_gap=monthly_total_gap,
        work_months=work_months,
        total_gap=total_gap,
        legal_basis=legal_basis,
    )


def format_social_security_report(
    ss: SalaryDiscrepancy,
    base_salary: float,
) -> str:
    """生成社保差额分析报告（可提交仲裁）。"""
    lines = []
    lines.append("=" * 60)
    lines.append("[社保/公积金缴纳差额分析报告]")
    lines.append("=" * 60)
    lines.append("")
    lines.append(f"【一、缴费基数比对】")
    lines.append(f"  实际月薪（工资流水）：{ss.actual_salary:.2f} 元")
    lines.append(f"  社保申报基数（缴费记录）：{ss.declared_salary:.2f} 元")
    lines.append(f"  基数差额：{ss.actual_salary - ss.declared_salary:.2f} 元")
    lines.append("")
    lines.append(f"【二、每月差额明细】")
    lines.append(f"  社保差额（公司少缴）：{ss.monthly_social_gap:.2f} 元/月")
    lines.append(f"  公积金差额（公司少缴）：{ss.monthly_housing_gap:.2f} 元/月")
    lines.append(f"  每月总差额：{ss.monthly_total_gap:.2f} 元/月")
    lines.append("")
    lines.append(f"【三、累计差额（工作{ss.work_months}个月）】")
    lines.append(f"  社保累计差额：{ss.monthly_social_gap * ss.work_months:.2f} 元")
    lines.append(f"  公积金累计差额：{ss.monthly_housing_gap * ss.work_months:.2f} 元")
    lines.append(f"  累计总差额：{ss.total_gap:.2f} 元")
    lines.append("")
    lines.append(f"【四、法律依据】")
    for i, basis in enumerate(ss.legal_basis, 1):
        lines.append(f"  {i}. {basis}")
    lines.append("")
    lines.append(f"【五、可主张权益】")
    lines.append(f"  1. 要求公司补缴社保差额：{ss.total_gap:.2f} 元")
    lines.append(f"  2. 如因未缴社保被迫离职，可主张经济补偿金：")
    years = ss.work_months // 12
    months = max(1, years) if years >= 1 else 1
    lines.append(f"     {months}个月 × {base_salary:.2f}元 = {months * base_salary:.2f} 元")
    lines.append("=" * 60)

    return "\n".join(lines)
