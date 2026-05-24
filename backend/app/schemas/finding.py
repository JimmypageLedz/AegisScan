from pydantic import BaseModel

class FindingRead(BaseModel):
    id :int
    task_id:int
    title: str
    severity: str
    evidence:str |None =None
    recommendation:str | None = None
    model_config = {"from_attributes":True}
