from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import FileResponse, Response

from grabber.config import get_config

router = APIRouter()


@router.get("/epg.xml")
async def serve_epg():
    cfg = get_config()
    output = Path(cfg.output_path)
    if not output.exists():
        return Response(content="<!-- no data yet, run the grabber first -->", media_type="application/xml")
    return FileResponse(str(output), media_type="application/xml")
