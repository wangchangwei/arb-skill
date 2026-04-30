from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from jinja2 import Template


@dataclass
class ClaimItem:
    name: str
    amount: float
    basis: str


@dataclass
class EvidencePoint:
    type: str  # favorable / unfavorable
    description: str
    legal_basis: str
    weight: str


@dataclass
class ComprehensiveReportData:
    username: str = ""
    company_name: str = ""
    period_start: str = ""
    period_end: str = ""
    base_salary: float = 0.0

    # 考勤
    attendance_data: list[dict] = field(default_factory=list)
    monthly_overtime: dict[str, float] = field(default_factory=dict)
    attendance_stats: list[dict] = field(default_factory=list)

    # 权益计算
    overtime_pay: float = 0.0
    unused_leave_pay: float = 0.0
    termination_compensation: float = 0.0
    notice_pay: float = 0.0
    no_contract_pay: float = 0.0
    social_security_gap: float = 0.0
    housing_fund_gap: float = 0.0
    total_claims: float = 0.0
    calculation_detail: str = ""

    # 社保差额
    social_security_analysis: dict = field(default_factory=dict)

    # 证据分析
    favorable_points: list[EvidencePoint] = field(default_factory=list)
    unfavorable_points: list[EvidencePoint] = field(default_factory=list)
    missing_evidence: list[str] = field(default_factory=list)
    evidence_strength: str = ""

    # 法律依据
    legal_basis: list[str] = field(default_factory=list)

    # Meta
    generated_at: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M"))

    def to_dict(self) -> dict:
        d = asdict(self)
        # Convert EvidencePoint objects to dicts
        d["favorable_points"] = [
            {k: v for k, v in asdict(p).items()} for p in self.favorable_points
        ]
        d["unfavorable_points"] = [
            {k: v for k, v in asdict(p).items()} for p in self.unfavorable_points
        ]
        return d


class ComprehensivePdfFormatter:
    def __init__(self, output_dir: str = "./output", template_path: str | None = None):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        if template_path:
            self.template_path = Path(template_path)
        else:
            self.template_path = (
                Path(__file__).parent.parent.parent / "templates" / "comprehensive_evidence.html"
            )

    def format(self, data: ComprehensiveReportData) -> str:
        filename = f"劳动仲裁证据包_{data.username}_{data.period_start}-{data.period_end}.pdf"
        filepath = self.output_dir / filename

        html_content = self._render_html(data)
        self._html_to_pdf(html_content, filepath)

        return str(filepath)

    def format_html(self, data: ComprehensiveReportData) -> str:
        """Generate HTML without PDF conversion (for preview)."""
        return self._render_html(data)

    def _render_html(self, data: ComprehensiveReportData) -> str:
        template_text = self.template_path.read_text(encoding="utf-8")
        template = Template(template_text)
        return template.render(**data.to_dict())

    @staticmethod
    def _html_to_pdf(html: str, output_path: Path) -> None:
        try:
            from weasyprint import HTML
            HTML(string=html).write_pdf(str(output_path))
        except (ImportError, OSError):
            # Fallback: save as HTML
            html_path = output_path.with_suffix(".html")
            html_path.write_text(html, encoding="utf-8")
            raise RuntimeError(
                f"weasyprint not available. HTML saved to: {html_path}"
            )
