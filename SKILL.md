---
name: arb-skill
description: >-
  劳动仲裁证据材料采集工具。帮普通员工收集证据、算清楚钱、准备材料。
  Trigger: "劳动仲裁" "仲裁" "加班费" "赔偿金" "社保差额" "被辞退" "劳动纠纷"
---

# 仲裁-skill

> 帮普通员工收集证据、算清楚钱、准备材料。**不做律师，做工具。**

## 核心能力

- **文件解析** — 考勤 CSV/Excel 上传后 AI 自动解析，无需 API
- **权益计算** — 加班费、违法解除赔偿金（2N）、代通知金、未签合同双倍、未休年假、社保/公积金差额
- **证据分析** — 有利 / 不利 / 缺失证据清单 + 证据强度评级
- **报告生成** — JSON / Excel / PDF / HTML 完整证据包（含十大认知误区附录）
- **仲裁指引** — 操作路线图 + 申请书模板 + 法律条款库

## 安装

**方式一：npm 安装（推荐）**
```bash
npx skills add yourusername/arb-skill
```

**方式二：从 GitHub 手动安装到本地 skills 目录**
```bash
# 克隆到本地 skills 目录
git clone https://github.com/yourusername/arb-skill.git ~/.claude/skills/arb-skill
```

## 快速使用

```python
# 1. 解析考勤文件
from src.tools.file_reader import parse_attendance_file
text = parse_attendance_file("考勤.xlsx")

# 2. 计算权益
from src.calculators.rights_calc import calculate_rights
r = calculate_rights(base_salary=15000, monthly_overtime={"2025-03": 12.5}, work_months=24, is_illegal_termination=True)

# 3. 社保差额分析
from src.calculators.social_security import analyze_social_security
gap = analyze_social_security(actual_salary=15000, declared_salary=8000, work_months=24)

# 4. 生成完整报告
from src.formatters.comprehensive_fmt import ComprehensiveReportData, ComprehensivePdfFormatter, EvidencePoint
data = ComprehensiveReportData(username="张三", company_name="XX科技", base_salary=15000, total_claims=50000)
fmt = ComprehensivePdfFormatter(output_dir="./output")
path = fmt.format(data)
```

## 报告结构

生成的证据包包含：

1. 封面 — 当事人信息 + 基准月薪
2. 仲裁请求总额 — 各项金额汇总
3. 考勤数据分析 — 月度加班明细表
4. 权益计算明细 — 计算过程 + 法律依据
5. 社保/公积金差额 — 实际月薪 vs 申报基数对比
6. 证据分析 — 有利 / 不利 / 缺失证据点
7. 法律依据
8. **附录：十大认知误区** — 员工常犯的法律认知错误及正确理解

## 内置劳动法知识库

| 法条 | 内容 |
|------|------|
| 《工资支付暂行规定》第13条 | 加班费计算标准（平日150%/休日200%/法定假日300%） |
| 《劳动合同法》第47条 | 经济补偿计算标准（N） |
| 《劳动合同法》第48条 | 违法解除劳动合同的赔偿 |
| 《劳动合同法》第87条 | 2N赔偿金标准 |
| 《职工带薪年休假条例》第5条 | 未休年假折算（300%） |

详见 [docs/](docs/) 目录下的完整指南。

## 项目结构

```
src/
├── calculators/           # 权益计算（加班费/赔偿金/社保差额）
├── formatters/            # 报告输出（PDF/HTML）
├── tools/                 # Skill工具接口
├── analyzer/              # 证据分析器
├── parsers/               # 备用文件解析器
└── knowledge/             # 劳动法知识库
docs/
├── ARB-ROADMAP-用户操作指南.md
├── ARB-GUIDE-申请书内容指南.md
└── ARB-KNOWLEDGE-十大认知误区.md
templates/
└── comprehensive_evidence.html
```

## 环境要求

- Python 3.10+
- `weasyprint`（Linux/macOS 直接支持；Windows 需 GTK3，否则回退为 HTML）

## 用户操作流程

1. 收集证据 → 考勤 Excel、工资流水、聊天截图、劳动合同、社保记录
2. 上传给 Agent → `parse_attendance_file()` 分析数据
3. 计算权益 → `calculate_claims()` 算出金额
4. 生成报告 → 输出证据包
5. 提交仲裁 → 按申请书指南填写，向仲裁委提交

详见 [仲裁 Roadmap](docs/ARB-ROADMAP-用户操作指南.md)。
