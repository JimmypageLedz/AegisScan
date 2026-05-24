from fastapi import APIRouter,Depends,HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.finding import Finding
from app.schemas.finding import FindingRead

router = APIRouter(prefix="/findings",tags=["findings"])

@router.get("",response_model=list[FindingRead])
def list_findings(task_id: int | None = None ,db: Session = Depends(get_db)):
    query = db.query(Finding)

    if task_id is not None:
        query = query.filter(Finding.task_id == task_id)

    return query.all()


@router.delete("/{finding_id}")
def delete_finding(finding_id: int, db: Session = Depends(get_db)):
    finding = db.get(Finding, finding_id)
    if finding is None:
        raise HTTPException(status_code=404, detail="Finding not found")

    db.delete(finding)
    db.commit()

    return {"deleted": True, "finding_id": finding_id}
