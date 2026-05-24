from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from app.config import settings
connect_args_ = {}
if settings.database_url.startswith("sqlite"):
    connect_args_ = {"check_same_thread":False}
engine = create_engine(settings.database_url,connect_args=connect_args_)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Base(DeclarativeBase):                                                                  
    pass