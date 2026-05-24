import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI

from grabber.config import get_config
from grabber.database import init_db
from grabber.routes.api import router as api_router
from grabber.routes.epg import router as epg_router
from grabber.routes.ui import router as ui_router
from grabber.scheduler import start_scheduler, stop_scheduler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)

Path("data").mkdir(exist_ok=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    cfg = get_config()
    if cfg.sd_username and cfg.sd_password_hash:
        start_scheduler()
    yield
    stop_scheduler()


app = FastAPI(title="SD Grabber", lifespan=lifespan)

app.include_router(epg_router)
app.include_router(api_router)
app.include_router(ui_router)
