from pydantic import BaseModel
from typing import Literal
class ReportGenerateRequest(BaseModel):
    mode: Literal["mock", "real", "auto"] = "auto"
    model: str | None = None

class ReportRead(BaseModel):
    id:int
    task_id: int
    summary: str
    severity:str
    impact:str
    remediation: str
    confidence:str
    model_name:str | None = None
    raw_output:str |None = None

    model_config = {"from_attributes":True}
    
