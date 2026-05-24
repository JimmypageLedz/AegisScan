from fastapi import APIRouter, Depends, HTTPException

from sqlalchemy.orm import Session
from app.api.deps import get_db
from app.models.asset import Asset
from app.models.finding import Finding
from app.models.risk_report import RiskReport
from app.models.scan_task import ScanTask
from app.schemas.asset import AssetCreate, AssetRead

router = APIRouter(prefix="/assets",tags=["assets"])

@router.get("",response_model=list[AssetRead])

def list_assets(db: Session = Depends(get_db)):
    assets =db.query(Asset).all()
    return assets

@router.post("", response_model=AssetRead)
def create_asset(payload: AssetCreate, db: Session = Depends(get_db)):
    asset = Asset(
        name=payload.name,
        target_url=str(payload.target_url),
        description=payload.description,
    )
    db.add(asset)
    db.commit()
    db.refresh(asset)
    return asset


@router.delete("/{asset_id}")
def delete_asset(asset_id: int, db: Session = Depends(get_db)):
    asset = db.get(Asset, asset_id)
    if asset is None:
        raise HTTPException(status_code=404, detail="Asset not found")

    task_ids = [
        task_id
        for (task_id,) in db.query(ScanTask.id).filter(ScanTask.asset_id == asset_id).all()
    ]

    if task_ids:
        db.query(RiskReport).filter(RiskReport.task_id.in_(task_ids)).delete(synchronize_session=False)
        db.query(Finding).filter(Finding.task_id.in_(task_ids)).delete(synchronize_session=False)

    db.query(ScanTask).filter(ScanTask.asset_id == asset_id).delete(synchronize_session=False)
    db.delete(asset)
    db.commit()

    return {"deleted": True, "asset_id": asset_id}
