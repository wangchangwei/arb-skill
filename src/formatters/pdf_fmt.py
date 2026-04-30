# src/formatters/pdf_fmt.py
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

from jinja2 import Template

from src.models import ArbitrationData


class PdfFormatter:
    def __init__(self, output_dir: str = "./output", template_path: str | None = None):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        if template_path:
            self.template_path = Path(template_path)
        else:
            self.template_path = (
                Path(__file__).parent.parent.parent / "templates" / "evidence.html"
            )

    def format(self, data: ArbitrationData) -> str:
        filename = f"仲裁证据_{data.username}_{data.period_start}-{data.period_end}.pdf"
        filepath = self.output_dir / filename

        html_content = self._render_html(data)
        self._html_to_pdf(html_content, filepath)

        return str(filepath)

    def _render_html(self, data: ArbitrationData) -> str:
        template_text = self.template_path.read_text(encoding="utf-8")
        template = Template(template_text)

        records = []
        for rec in data.attendance_records:
            d = asdict(rec)
            d["check_time"] = rec.check_time.strftime("%Y-%m-%d %H:%M:%S")
            records.append(d)

        messages = []
        for msg in data.message_records:
            d = asdict(msg)
            d["create_time"] = msg.create_time.strftime("%Y-%m-%d %H:%M:%S")
            messages.append(d)

        stats = [asdict(s) for s in data.attendance_stats]

        return template.render(
            username=data.username,
            period_start=data.period_start,
            period_end=data.period_end,
            collected_at=data.collected_at or datetime.now().isoformat(),
            attendance_records=records,
            attendance_stats=stats,
            message_records=messages,
        )

    @staticmethod
    def _html_to_pdf(html: str, output_path: Path) -> None:
        from weasyprint import HTML

        HTML(string=html).write_pdf(str(output_path))
