from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.risk_report import RiskReport
from app.schemas.report import ReportGenerateRequest, ReportRead
from app.services.report_service import generate_report_for_task

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/{task_id}", response_model=ReportRead)
def get_report(task_id: int, db: Session = Depends(get_db)):
    report = db.query(RiskReport).filter(RiskReport.task_id == task_id).first()
    if report is None:
        raise HTTPException(status_code=404, detail="Report not found")
    return report


@router.post("/{task_id}/generate", response_model=ReportRead)
def generate_report(task_id: int, payload: ReportGenerateRequest, db: Session = Depends(get_db)):
    try:
        return generate_report_for_task(
            db=db,
            task_id=task_id,
            mode=payload.mode,
            model_name=payload.model,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except NotImplementedError as exc:
        raise HTTPException(status_code=501, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.delete("/{task_id}")
def delete_report(task_id: int, db: Session = Depends(get_db)):
    report = db.query(RiskReport).filter(RiskReport.task_id == task_id).first()
    if report is None:
        raise HTTPException(status_code=404, detail="Report not found")

    db.delete(report)
    db.commit()

    return {"deleted": True, "task_id": task_id}
