import httpx

from app.scanners.base import BaseScanner,FindingResult


class AliveScanner(BaseScanner):
    name = "alive"

    async def scan(self,target_url: str) -> list[FindingResult]:
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get(target_url)
            
            if response.status_code < 400:
                return []
            return [
                FindingResult(
                    title="Target return error status",
                    severity="low",
                    evidence=f"status_code={response.status_code}",
                    recommendation="Check whether the target URL is correct and accessible"
                )
            ]
        except Exception as exc:
            return [
                FindingResult(
                    title="Target is unreachable",
                    severity="medium",
                    evidence=str(exc),
                    recommendation="Check network connectivity and whether the target is online."
                )
            ]