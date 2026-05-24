from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from grabber import database as db
from grabber.config import get_config
from grabber.pipeline import get_run_status
from grabber.scheduler import next_run_time

router = APIRouter()
templates = Jinja2Templates(directory=str(Path(__file__).parent.parent / "templates"), autoescape=True)


@router.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    cfg = get_config()
    run_status = get_run_status()
    history = await db.list_runs(limit=10)
    output_exists = Path(cfg.output_path).exists()

    return templates.TemplateResponse(request, "index.html", {
        "active": "dashboard",
        "cfg": cfg,
        "run_status": run_status,
        "history": history,
        "next_run": next_run_time(),
        "configured": bool(cfg.sd_username and cfg.sd_password_hash),
        "output_exists": output_exists,
    })


@router.get("/settings", response_class=HTMLResponse)
async def settings_page(request: Request):
    cfg = get_config()
    return templates.TemplateResponse(request, "settings.html", {
        "active": "settings",
        "cfg": cfg,
    })
