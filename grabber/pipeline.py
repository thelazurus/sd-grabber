import asyncio
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path

from grabber.config import Config
from grabber.database import finish_run, start_run
from grabber.sd_client import get_lineup_channels, get_lineups, get_programs, get_schedules
from grabber.xmltv import build_xmltv

logger = logging.getLogger(__name__)

_pipeline_lock = asyncio.Lock()
_run_status: dict = {"running": False, "stage": "idle"}


def get_run_status() -> dict:
    return dict(_run_status)


async def run_pipeline(cfg: Config) -> dict:
    if _pipeline_lock.locked():
        raise RuntimeError("Pipeline already running")

    async with _pipeline_lock:
        run_id = await start_run()
        stats: dict = {"lineups": 0, "stations": 0, "airings": 0, "programs": 0}
        _run_status.update({
            "running": True,
            "run_id": run_id,
            "stats": stats,
            "started": datetime.now(timezone.utc).isoformat(),
            "stage": "fetching lineups",
        })

        try:
            lineups = await get_lineups(cfg.sd_username, cfg.sd_password_hash)
            if cfg.enabled_lineups:
                lineups = [l for l in lineups if l["lineup"] in cfg.enabled_lineups]
            stats["lineups"] = len(lineups)
            logger.info("%d lineups", len(lineups))

            _run_status["stage"] = "fetching channels"
            all_stations: dict[str, dict] = {}
            for lineup in lineups:
                data = await get_lineup_channels(
                    cfg.sd_username, cfg.sd_password_hash, lineup["lineup"]
                )
                for station in data.get("stations", []):
                    all_stations[station["stationID"]] = station
            stats["stations"] = len(all_stations)
            logger.info("%d stations", len(all_stations))

            _run_status.update({"stage": "fetching schedules", "stats": dict(stats)})
            today = datetime.now(timezone.utc).date()
            dates = [(today + timedelta(days=i)).isoformat() for i in range(cfg.days)]
            sched_requests = [
                {"stationID": sid, "date": dates} for sid in all_stations
            ]
            schedules = await get_schedules(
                cfg.sd_username, cfg.sd_password_hash, sched_requests
            )
            stats["airings"] = sum(len(s.get("programs", [])) for s in schedules)
            logger.info("%d airings across %d schedules", stats["airings"], len(schedules))

            _run_status.update({"stage": "fetching program details", "stats": dict(stats)})
            program_ids = list({
                airing["programID"]
                for sched in schedules
                for airing in sched.get("programs", [])
            })
            program_list = await get_programs(
                cfg.sd_username, cfg.sd_password_hash, program_ids
            )
            programs_by_id = {p["programID"]: p for p in program_list}
            stats["programs"] = len(programs_by_id)
            logger.info("%d unique programs", len(programs_by_id))

            _run_status.update({"stage": "writing XMLTV", "stats": dict(stats)})
            xml_bytes = build_xmltv(list(all_stations.values()), schedules, programs_by_id)
            output = Path(cfg.output_path)
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_bytes(xml_bytes)
            logger.info("Wrote %s (%d bytes)", cfg.output_path, len(xml_bytes))

            await finish_run(run_id, "success", stats)
            _run_status.update({"stats": dict(stats)})
            return stats

        except Exception as exc:
            logger.exception("Pipeline failed: %s", exc)
            await finish_run(run_id, "error", stats)
            raise
        finally:
            _run_status.update({"running": False, "stage": "idle"})
