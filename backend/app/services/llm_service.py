import json

from openai import OpenAI
from openai import OpenAIError

from app.config import settings
from app.models.finding import Finding


def generate_structured_report(
    findings: list[Finding],
    model_name: str | None = None,
) -> dict[str, str | None]:
    if not settings.openai_api_key:
        raise RuntimeError("OPENAI_API_KEY is not configured")

    if not settings.openai_base_url:
        raise RuntimeError("OPENAI_BASE_URL is not configured")

    client = OpenAI(
        api_key=settings.openai_api_key,
        base_url=settings.openai_base_url,
    )

    effective_model = model_name or settings.openai_model or "gpt-4.1-mini"

    # Keep the model input compact and structured so the response is easier to parse.
    findings_payload = [
        {
            "title": finding.title,
            "severity": finding.severity,
            "evidence": finding.evidence,
            "recommendation": finding.recommendation,
        }
        for finding in findings
    ]

    system_prompt = (
        "You are a security analyst. "
        "Generate a concise structured risk report from the provided web security findings. "
        "Return valid JSON only. "
        "All field values must be written in Simplified Chinese."
    )

    user_prompt = (
        "Based on the following findings, produce a JSON object with these keys: "
        "summary, severity, impact, remediation, confidence. "
        "Keep the JSON keys in English exactly as specified, but write every value in Simplified Chinese.\n\n"
        f"Findings:\n{json.dumps(findings_payload, ensure_ascii=False, indent=2)}"
    )

    try:
        response = client.chat.completions.create(
            model=effective_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.2,
        )
    except OpenAIError as exc:
        raise RuntimeError(f"LLM request failed: {exc}") from exc

    raw_text = response.choices[0].message.content or ""

    try:
        parsed = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        raise RuntimeError("LLM did not return valid JSON") from exc

    required_fields = ["summary", "severity", "impact", "remediation", "confidence"]
    for field in required_fields:
        if field not in parsed:
            raise RuntimeError(f"LLM response is missing required field: {field}")

    return {
        "summary": str(parsed["summary"]),
        "severity": str(parsed["severity"]),
        "impact": str(parsed["impact"]),
        "remediation": str(parsed["remediation"]),
        "confidence": str(parsed["confidence"]),
        "model_name": effective_model,
        "raw_output": raw_text,
    }


def list_available_models() -> list[str]:
    if not settings.openai_api_key:
        raise RuntimeError("OPENAI_API_KEY is not configured")

    if not settings.openai_base_url:
        raise RuntimeError("OPENAI_BASE_URL is not configured")

    client = OpenAI(
        api_key=settings.openai_api_key,
        base_url=settings.openai_base_url,
        timeout=settings.llm_timeout_seconds,
    )

    try:
        response = client.models.list()
    except OpenAIError as exc:
        raise RuntimeError(f"LLM model list request failed: {exc}") from exc

    model_ids = {
        model.id
        for model in response.data
        if getattr(model, "id", None)
    }

    return sorted(model_ids)
