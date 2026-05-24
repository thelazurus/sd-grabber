from fastapi import APIRouter, BackgroundTasks, HTTPException

from grabber import database as db
from grabber.config import get_config, save_config
from grabber.pipeline import get_run_status, run_pipeline
from grabber.scheduler import next_run_time, reschedule, start_scheduler
from grabber.sd_client import get_lineups, get_status, invalidate_token

router = APIRouter(prefix="/api")


@router.post("/run")
async def trigger_run(background_tasks: BackgroundTasks):
    status = get_run_status()
    if status.get("running"):
        raise HTTPException(status_code=409, detail="Pipeline already running")
    cfg = get_config()
    if not cfg.sd_username or not cfg.sd_password_hash:
        raise HTTPException(status_code=400, detail="SD credentials not configured")
    background_tasks.add_task(run_pipeline, cfg)
    return {"status": "started"}


@router.get("/status")
async def pipeline_status():
    status = get_run_status()
    status["next_run"] = next_run_time()
    return status


@router.get("/history")
async def run_history():
    return await db.list_runs()


@router.get("/sd/status")
async def sd_account_status():
    cfg = get_config()
    if not cfg.sd_username or not cfg.sd_password_hash:
        return {"configured": False}
    try:
        data = await get_status(cfg.sd_username, cfg.sd_password_hash)
        return {"configured": True, "account": data}
    except Exception as exc:
        return {"configured": True, "error": str(exc)}


@router.get("/sd/lineups")
async def sd_lineups():
    cfg = get_config()
    if not cfg.sd_username or not cfg.sd_password_hash:
        raise HTTPException(status_code=400, detail="SD credentials not configured")
    try:
        return await get_lineups(cfg.sd_username, cfg.sd_password_hash)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc))


@router.post("/settings")
async def update_settings(body: dict):
    save_config(body)
    cfg = get_config()
    if "sd_username" in body or "sd_password" in body:
        invalidate_token()
        if cfg.sd_username and cfg.sd_password_hash:
            start_scheduler()
    if "schedule_interval_hours" in body:
        reschedule(float(body["schedule_interval_hours"]))
    return {"status": "ok"}
