from fastapi import APIRouter,Depends,HTTPException
from sqlalchemy.orm import Session
from app.models.finding import Finding
from app.models.risk_report import RiskReport
from app.models.scan_task import ScanTask

from app.api.deps import get_db
from app.models.asset import Asset

from app.schemas.scan_task import ScanTaskCreate,ScanTaskRead
from app.tasks.worker import scan_task_job

router = APIRouter(prefix="/tasks",tags=["tasks"])

@router.get("",response_model=list[ScanTaskRead])
def list_tasks(db:Session = Depends(get_db)):
    tasks = db.query(ScanTask).all()
    return tasks

@router.post("",response_model=ScanTaskRead)
def create_task(payload:ScanTaskCreate,db:Session= Depends(get_db)):
    asset = db.get(Asset,payload.asset_id)
    if asset is None:
        raise HTTPException(status_code=404,detail="Asset not found")
    
    task = ScanTask(asset_id=payload.asset_id,status="pending")
    db.add(task)
    db.commit()
    db.refresh(task)

    scan_task_job.delay(task.id)

    db.refresh(task)
    return task


@router.delete("/{task_id}")
def delete_task(task_id: int, db: Session = Depends(get_db)):
    task = db.get(ScanTask, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")

    db.query(RiskReport).filter(RiskReport.task_id == task_id).delete(synchronize_session=False)
    db.query(Finding).filter(Finding.task_id == task_id).delete(synchronize_session=False)
    db.delete(task)
    db.commit()

    return {"deleted": True, "task_id": task_id}
