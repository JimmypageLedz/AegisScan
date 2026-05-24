from collections import Counter

from sqlalchemy.orm import Session

from app.config import settings
from app.models.finding import Finding
from app.models.risk_report import RiskReport


def _build_mock_report(task_id: int, findings: list[Finding], model_name: str | None) -> dict[str, str | None]:
    severity_counter = Counter(finding.severity for finding in findings)

    if severity_counter.get("high"):
        top_severity = "high"
    elif severity_counter.get("medium"):
        top_severity = "medium"
    else:
        top_severity = "low"

    top_findings = findings[:3]
    summary_titles = "、".join(finding.title for finding in top_findings) or "未发现明显问题"

    remediation_lines = []
    for finding in top_findings:
        if finding.recommendation:
            remediation_lines.append(f"- {finding.recommendation}")

    if not remediation_lines:
        remediation_lines.append("- 建议复核扫描范围，并结合业务场景人工确认目标配置。")

    return {
        "summary": f"任务 {task_id} 共发现 {len(findings)} 条安全配置问题，主要包括：{summary_titles}。",
        "severity": top_severity,
        "impact": (
            "这些发现说明目标站点的 Web 安全配置存在薄弱点。根据具体接口上下文，"
            "可能增加浏览器侧攻击、信息泄露或不安全跨域访问的风险。"
        ),
        "remediation": "\n".join(remediation_lines),
        "confidence": "medium",
        "model_name": model_name or "mock-report-generator",
        "raw_output": None,
    }


def generate_report_for_task(
    db: Session,
    task_id: int,
    mode: str = "mock",
    model_name: str | None = None,
) -> RiskReport:
    findings = db.query(Finding).filter(Finding.task_id == task_id).all()
    if not findings:
        raise ValueError("No findings found for the given task")

    existing_report = db.query(RiskReport).filter(RiskReport.task_id == task_id).first()

    effective_mode = settings.llm_mode if mode == "auto" else (mode or settings.llm_mode)
    if effective_mode == "mock":
        report_data = _build_mock_report(task_id, findings, model_name)
    elif effective_mode == "real":
        try:
            from app.services.llm_service import generate_structured_report
        except ImportError as exc:
            raise RuntimeError("The openai package is not installed") from exc

        try:
            report_data = generate_structured_report(
                findings=findings,
                model_name=model_name,
            )
        except RuntimeError as exc:
            report_data = _build_mock_report(task_id, findings, model_name)
            report_data["model_name"] = f"{report_data['model_name']} (LLM fallback)"
            report_data["raw_output"] = f"LLM request failed, fallback report generated locally: {exc}"
    else:
        raise ValueError("Unsupported report generation mode")

    if existing_report is None:
        report = RiskReport(task_id=task_id, **report_data)
        db.add(report)
    else:
        report = existing_report
        report.summary = str(report_data["summary"])
        report.severity = str(report_data["severity"])
        report.impact = str(report_data["impact"])
        report.remediation = str(report_data["remediation"])
        report.confidence = str(report_data["confidence"])
        report.model_name = None if report_data["model_name"] is None else str(report_data["model_name"])
        report.raw_output = None if report_data["raw_output"] is None else str(report_data["raw_output"])

    db.commit()
    db.refresh(report)
    return report
