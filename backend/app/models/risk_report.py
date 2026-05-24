from sqlalchemy import ForeignKey,String,Text
from sqlalchemy.orm import Mapped,mapped_column

from app.db import  Base

class RiskReport(Base):
    __tablename__="risk_reports"

    id:Mapped[int] = mapped_column(primary_key=True,index = True)
    task_id:Mapped[int] = mapped_column(ForeignKey("scan_tasks.id"),nullable=False,unique=True)
    summary:Mapped[str] = mapped_column(Text,nullable=False)
    severity:Mapped[str] = mapped_column(String(20),nullable=False)
    impact:Mapped[str] = mapped_column(Text,nullable=False)
    remediation:Mapped[str] = mapped_column(Text,nullable=False)
    confidence:Mapped[str] = mapped_column(String(20),nullable=False)
    model_name:Mapped[str|None] = mapped_column(String(100),nullable=True)
    raw_output:Mapped[str|None] = mapped_column(Text,nullable=True)