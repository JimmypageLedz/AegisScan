from pydantic import BaseModel

class ScanTaskCreate(BaseModel):
    asset_id:int

class ScanTaskRead(BaseModel):
    id:int
    asset_id:int
    status:str

    model_config = {"from_attributes":True}
    