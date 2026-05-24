import httpx

from app.scanners.base import BaseScanner,FindingResult

class CookieScanner(BaseScanner):
    name = "cookie"

    async def scan(self,target_url:str)->list[FindingResult]:
        findings:list[FindingResult] = []

        try:
            async with httpx.AsyncClient(timeout=5,follow_redirects=True) as client:
                response = await client.get(target_url)
        except Exception as exc:
            return [
                FindingResult(
                    title="Unable to fetch target for cookie scan",
                    severity="medium",
                    evidence=str(exc),
                    recommendation="Check network connectivity and whether the target URL is reachable.",
                )

            ]
        set_cookie_headers = response.headers.get_list("set-cookie")

        for cookie_headers in set_cookie_headers:
            cookie_name = cookie_headers.split("=",1)[0].strip()
            attributes = [part.strip().lower() for part in cookie_headers.split(";")[1:]]

            if "secure" not in attributes:
                findings.append(
                    FindingResult(
                        title="Cookie missing Secure flag",
                        severity="medium",
                        evidence=f"Cookie'{cookie_name} does not have the secure flag.",
                        recommendation = "Add the Secure flag so the cookie is only sent over HTTPS",

                    )
                )
            if"httponly" not in attributes:
                findings.append(
                     FindingResult(
                        title="Cookie missing HttpOnly flag",
                        severity="medium",
                        evidence=f"Cookie '{cookie_name}' does not have the HttpOnly flag.",
                        recommendation="Add the HttpOnly flag to reduce exposure to client-side script access.",
                     )
                )
            if not any(attribute.startswith("samesite=") for attribute in attributes):
                findings.append(
                    FindingResult(
                        title="Cookie missing SameSite attribute",
                        severity="low",
                        evidence=f"Cookie '{cookie_name}' does not define SameSite.",
                        recommendation="Set SameSite=Lax or SameSite=Strict where appropriate.",
                    )
                )
        return findings
