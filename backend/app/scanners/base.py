from dataclasses import dataclass

@dataclass
class FindingResult:
    title: str
    severity :str = "low"
    evidence:str | None=None
    recommendation:str | None=None

class BaseScanner:
    name = "base"

    async def scan(self,target_url: str)->list[FindingResult]:
        raise NotImplementedError
    