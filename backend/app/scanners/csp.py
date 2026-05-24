import httpx
from app.scanners.base import BaseScanner,FindingResult
_CRITICAL_DIRECTIVES = {"default-src","script-src","object-src"}
class CspScanner(BaseScanner):
    name = "csp"

    async def scan(self,target_url :str) ->list[FindingResult]:
        findings:list[FindingResult] = []
        try :
            async with httpx.AsyncClient(timeout = 5, follow_redirects=True) as client:
                response = await client.get(target_url)
        except Exception as exc:
            return [
                FindingResult(
                    title="Unable to fetch target for CSP scan",
                    severity="medium",
                    evidence=str(exc),
                    recommendation="Check network connectivity and whether the target URL is reachable.",
                )
            ]
        csp_value = response.headers.get("content-security-policy")

        if not csp_value:
            findings.append(
                FindingResult(
                    title="Content-Security-Policy header is missing",
                    severity="high",
                    evidence="No Content-Security-Policy header found in response",
                    recommendation="Add a Content-Security-Policy header to restrict resource loading and reduce XSS risk",
                )
            )
            return findings        

         
        directives:dict[str,str] = {}
        for part in csp_value.split(";"):
            part = part.strip()
            if not part:
                continue
            tokens = part.split(None,1)
            directive_name = tokens[0].lower()
            directive_value = tokens[1] if len (tokens) > 1 else ""
            directives[directive_name] = directive_value
        effective_script_src = directives.get("script-src") or directives.get("default-src","")

        if "'unsafe-inline'" in effective_script_src:       
            findings.append(
                FindingResult(
                    title = "CSP allows 'unsafe-inline' in script-src",
                    severity = "high",
                    evidence = f"script-src or default-src contains 'unsafe-inline':{effective_script_src!r}",
                    recommendation="Remove 'unsafe-inline' and use nonces or hashes to allow specific inline scripts.",

                )
            )
        if "'unsafe-eval'" in effective_script_src:
            findings.append(
                FindingResult(
                    title="CSP allows 'unsafe-eval' in script-src",
                    severity="high",
                    evidence=f"script-src (or default-src) contains 'unsafe-eval': {effective_script_src!r}",
                    recommendation="Remove 'unsafe-eval' to prevent dynamic code execution via eval().",
                )
            )
        for directive_name, directive_value in directives.items():
            if directive_name not in ("script-src", "default-src", "object-src"):
                continue
            for token in directive_value.split():
                if token in ("*", "https:"):
                    findings.append(
                        FindingResult(
                            title=f"CSP uses overly broad wildcard in {directive_name}",
                            severity="high",
                            evidence=f"{directive_name}: {directive_value!r} contains '{token}'",
                            recommendation=f"Replace the wildcard in {directive_name} with explicit trusted origins.",
                        )
                    )
                    break

        if "default-src" not in directives:
            for directive in _CRITICAL_DIRECTIVES - {"default-src"} - set(directives.keys()):
                findings.append(
                    FindingResult(
                        title=f"CSP is missing '{directive}' directive",
                        severity="medium",
                        evidence=f"Neither '{directive}' nor 'default-src' found in CSP",
                        recommendation=f"Add a '{directive}' directive or a 'default-src' fallback.",
                    )
                )

        return findings    