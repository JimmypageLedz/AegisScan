from sqlalchemy import ForeignKey,String, Text
from sqlalchemy.orm import Mapped,mapped_column

from app.db import Base


class Finding(Base):
    __tablename__="findings"

    id:Mapped[int] = mapped_column(primary_key=True,index = True)
    task_id:Mapped[int]=mapped_column(ForeignKey("scan_tasks.id"), nullable=False)
    title:Mapped[str] = mapped_column(String(200),nullable=False)
    severity: Mapped[str] = mapped_column(String(20),default="low",nullable=False)
    evidence:Mapped[str | None] = mapped_column(Text,nullable=True)
    recommendation:Mapped[str | None] = mapped_column(Text,nullable=True)
