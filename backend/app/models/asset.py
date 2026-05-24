from sqlalchemy import String
from sqlalchemy.orm import Mapped,mapped_column

from app.db import Base

class Asset(Base):
    __tablename__="assets"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name:Mapped[str] = mapped_column(String(100),nullable=False)
    target_url: Mapped[str] = mapped_column(String(500),nullable=False,unique=True)
    description: Mapped[str | None] = mapped_column(String(500),nullable=True)

