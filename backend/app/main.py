from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.assets import router as assets_router
from app.db import Base, engine
from app.config import settings
from app.models.asset import Asset
from app.api.tasks import router as tasks_router
from app.api.findings import router as findings_router
from app.api.reports import router as reports_router
from app.api.llm import router as llm_router
from app.models.risk_report import RiskReport

app = FastAPI(title="AegisScan API")

if settings.app_debug:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:5173",
            "http://127.0.0.1:5173",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)

@app.get("/")
def read_root():
    return {"message":"AegisScan API is running"}

@app.get("/health")
def health_check():
    return {"status":"ok"}

app.include_router(assets_router)
app.include_router(tasks_router)
app.include_router(findings_router)
app.include_router(reports_router)
app.include_router(llm_router)
