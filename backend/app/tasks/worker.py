from app.celery_app import celery_app

from app.tasks.runner import run_scan_task_sync
@celery_app.task(name="scan_task_job")
def scan_task_job(task_id:int)->None:
    run_scan_task_sync(task_id)