import json
from datetime import datetime, timezone
from pathlib import Path

import aiosqlite

from grabber import DATA_DIR

DB_PATH = DATA_DIR / "sd_grabber.db"

_SCHEMA = """
CREATE TABLE IF NOT EXISTS run_history (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    started_at  TEXT NOT NULL,
    finished_at TEXT,
    status      TEXT NOT NULL DEFAULT 'running',
    stats       TEXT
);
"""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


async def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.executescript(_SCHEMA)
        await db.commit()


async def start_run() -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "INSERT INTO run_history (started_at, status) VALUES (?, 'running')",
            (_now(),),
        )
        await db.commit()
        return cur.lastrowid


async def finish_run(run_id: int, status: str, stats: dict):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE run_history SET finished_at=?, status=?, stats=? WHERE id=?",
            (_now(), status, json.dumps(stats), run_id),
        )
        await db.commit()


async def list_runs(limit: int = 20) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM run_history ORDER BY started_at DESC LIMIT ?", (limit,)
        ) as cur:
            rows = [dict(r) for r in await cur.fetchall()]
    for r in rows:
        if r.get("stats"):
            r["stats"] = json.loads(r["stats"])
    return rows
