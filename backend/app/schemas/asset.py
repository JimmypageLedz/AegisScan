from pydantic import BaseModel,HttpUrl

class AssetBase(BaseModel):
    name: str
    target_url:HttpUrl
    description:str | None = None
class AssetCreate(AssetBase):
    pass

class AssetRead(AssetBase):
    id :int

    model_config = {"from_attributes": True}