import httpx

from app.scanners.base import BaseScanner,FindingResult

class HeaderScanner(BaseScanner):
    name="headers"

    async def scan(self,target_url:str)->list[FindingResult]:
        findings:list[FindingResult] = []


        try:
            async with httpx.AsyncClient(timeout=5,follow_redirects=True) as client:
                response = await client.get(target_url)
        except Exception as exc:
            return [

                FindingResult(
                    title="Unable to fetch target for header scan",
                    severity="medium",
                    evidence=str(exc),
                    recommendation="Check network connectivity and whether the target URL is reachable",

                )
            ]

        headers = response.headers

        if "strict-transport-security" not in headers:
            findings.append(
                FindingResult(
                    title="Missing HSTS header",
                    severity="medium",
                    evidence="Strict-Transport-Security header not found",
                    recommendation="Add the Strict-Transport-Security header with an appropriate max-age",

                )
            )
        if "x-frame-options" not in headers:
            findings.append(
                FindingResult(
                    title="Missing X-Frame-Options header",
                    severity="medium",
                    evidence="X-Frame-Options header not found",
                    recommendation="Add X-Frame-Options to reduce clickjacking risk",


                )


            )
        if "x-content-type-options" not in headers:
            findings.append(
                FindingResult(
                    title="Missing X-Content-Type-Options header",
                    severity="low",
                    evidence="X-Content-Type-Options headers ot found",
                    recommendation="Add X-Content-Type-Options: no sniff.",

                )
            )
        if "referrer-policy" not in headers:
            findings.append(
                FindingResult(
                    title="Missing Referrer-Policy  header",
                    severity="low",
                    evidence="Referer Policy header not found",
                    recommendation="Add a Referrer-Policy header approriate for the aplication",

                )

            )
        if "server" in headers:
            findings.append(
                FindingResult(
                    title="Server header is exposed",
                    severity="low",
                    evidence=f"Server: {headers['server']}",
                    recommendation="Consider reducing or removing the Server header to limit information disclosure.",
                )
            )

        if "x-powered-by" in headers:
            findings.append(
                FindingResult(
                    title="X-Powered-By header is exposed",
                    severity="low",
                    evidence=f"X-Powered-By: {headers['x-powered-by']}",
                    recommendation="Consider removing the X-Powered-By header to limit information disclosure.",
                )
            )
        return findings
