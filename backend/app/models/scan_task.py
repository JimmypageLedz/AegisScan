from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped,mapped_column

from app.db import Base
class ScanTask(Base):
    __tablename__ = "scan_tasks"

    id: Mapped[int] = mapped_column(primary_key=True,index=True)
    asset_id:Mapped[int]=mapped_column(ForeignKey("assets.id"), nullable=False)
    status:Mapped[str] = mapped_column(String(50),default="pending",nullable=False)
    

