import asyncio

from app.db import SessionLocal
from app.models.asset import Asset
from app.models.scan_task import ScanTask
from app.models.finding import Finding
from app.scanners.alive import AliveScanner
from app.scanners.headers import HeaderScanner
from app.scanners.cookie import CookieScanner
from app.scanners.csp import CspScanner
from app.scanners.cors import CorsScanner
async def run_scan_task(task_id) ->None:
    db=SessionLocal()
    try:
        task = db.get(ScanTask,task_id)
        if task is None:
            return
        asset = db.get(Asset,task.asset_id)
        if asset is None:
            task.status="failed"
            db.commit()
            return
        task.status = "running"
        db.commit()

        alive_scanner = AliveScanner()
        alive_results = await alive_scanner.scan(asset.target_url)

        for result in alive_results:
            finding = Finding(
                task_id=task.id,
                title=result.title,
                severity=result.severity,
                evidence=result.evidence,
                recommendation=result.recommendation,
            )
            db.add(finding)
        if any(result.title == "Target is unreachable" for result in  alive_results):
            task.status = "finished"
            db.commit()
            return
        header_scanner = HeaderScanner()
        header_results = await header_scanner.scan(asset.target_url)
        for result in header_results:
            finding = Finding(
                task_id = task.id,
                title=result.title,
                severity = result.severity,
                evidence=result.evidence,
                recommendation=result.recommendation,
            )
            db.add(finding)              #存活验证


        db.commit()
        cookie_scanner = CookieScanner()
        cookie_results = await cookie_scanner.scan(asset.target_url)
        for result in cookie_results:
            finding = Finding(
                task_id = task.id,
                title=result.title,
                severity = result.severity,
                evidence=result.evidence,
                recommendation=result.recommendation,
            )
            db.add(finding)              #cookie扫描



        csp_scanner = CspScanner()
        csp_results = await csp_scanner.scan(asset.target_url)
        for result in csp_results:
            finding = Finding(
                task_id = task.id,
                title=result.title,
                severity=result.severity,
                evidence=result.evidence,
                recommendation=result.recommendation,
            )
            db.add(finding)               #csp扫描
        
        cors_scanner = CorsScanner()
        cors_results = await cors_scanner.scan(asset.target_url)
        for result in cors_results:
            finding = Finding(
                task_id = task.id,
                title=result.title,
                severity=result.severity,
                evidence=result.evidence,
                recommendation=result.recommendation,        # cors扫描
            )
            db.add(finding)    
        task.status = "finished"  #扫描结束
        db.commit()
    except Exception:
        if "task" in locals() and task is not None:
            task.status = "failed"
            db.commit()
        raise
    finally:
        db.close()

def run_scan_task_sync(task_id:int) -> None:
    asyncio.run(run_scan_task(task_id))
