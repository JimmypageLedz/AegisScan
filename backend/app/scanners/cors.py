import httpx

from app.scanners.base import BaseScanner, FindingResult


class CorsScanner(BaseScanner):
    name = "cors"

    async def scan(self, target_url: str) -> list[FindingResult]:
        findings: list[FindingResult] = []
        test_origin = "http://evil.example"

        try:
            async with httpx.AsyncClient(timeout=5, follow_redirects=True) as client:
                response = await client.get(
                    target_url,
                    headers={"Origin": test_origin},
                )
        except Exception as exc:
            return [
                FindingResult(
                    title="Unable to fetch target for CORS scan",
                    severity="medium",
                    evidence=str(exc),
                    recommendation="Check network connectivity and whether the target URL is reachable.",
                )
            ]

        allow_origin = response.headers.get("access-control-allow-origin")
        allow_credentials = response.headers.get("access-control-allow-credentials")

        if not allow_origin:
            return findings

        if allow_origin == "*":
            findings.append(
                FindingResult(
                    title="CORS allows any origin",
                    severity="medium",
                    evidence="Access-Control-Allow-Origin: *",
                    recommendation=(
                        "Restrict Access-Control-Allow-Origin to specific trusted origins. "
                        "If this is a public test endpoint, verify whether the response contains "
                        "sensitive or authenticated data before treating it as a production issue."
                    ),
                )
            )

        if allow_origin == test_origin:
            findings.append(
                FindingResult(
                    title="CORS reflects arbitrary Origin",
                    severity="high",
                    evidence=f"Access-Control-Allow-Origin reflects the supplied Origin: {test_origin}",
                    recommendation=(
                        "Do not reflect arbitrary Origin values. Use an allowlist of trusted origins. "
                        "If this is a public test endpoint, confirm whether this behavior is intentional "
                        "and whether the endpoint exposes sensitive data."
                    ),
                )
            )

        if allow_credentials and allow_credentials.lower() == "true":
            if allow_origin == "*" or allow_origin == test_origin:
                findings.append(
                    FindingResult(
                        title="CORS allows credentials for an unsafe origin",
                        severity="high",
                        evidence=(
                            f"Access-Control-Allow-Origin: {allow_origin}, "
                            f"Access-Control-Allow-Credentials: {allow_credentials}"
                        ),
                        recommendation=(
                            "Only allow credentials for explicitly trusted origins. "
                            "If this endpoint is intentionally public, verify that it does not return "
                            "user-specific or sensitive authenticated data."
                        ),
                    )
                )

        return findings
