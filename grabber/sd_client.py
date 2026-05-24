import logging
from datetime import datetime, timezone

import aiohttp

SD_BASE = "https://json.schedulesdirect.org/20141201"
_UA = "sd-grabber/1.0 (https://github.com/thelazurus/sd-grabber)"
logger = logging.getLogger(__name__)


def _session_headers(token: str | None = None) -> dict:
    h = {"User-Agent": _UA}
    if token:
        h["token"] = token
    return h

_token: str | None = None
_token_fetched: datetime | None = None


async def _get_token(username: str, password_hash: str) -> str:
    global _token, _token_fetched
    if _token and _token_fetched:
        age = (datetime.now(timezone.utc) - _token_fetched).total_seconds()
        if age < 23 * 3600:
            return _token

    async with aiohttp.ClientSession(headers=_session_headers()) as session:
        async with session.post(
            f"{SD_BASE}/token",
            json={"username": username, "password": password_hash},
            timeout=aiohttp.ClientTimeout(total=30),
        ) as r:
            data = await r.json(content_type=None)
            if not r.ok:
                raise RuntimeError(f"SD token request failed ({r.status}): {data}")

    if data.get("code", 0) != 0:
        raise RuntimeError(f"SD auth failed: {data.get('message', data)}")

    _token = data["token"]
    _token_fetched = datetime.now(timezone.utc)
    logger.info("SD token acquired")
    return _token


def invalidate_token():
    global _token, _token_fetched
    _token = None
    _token_fetched = None


async def get_status(username: str, password_hash: str) -> dict:
    token = await _get_token(username, password_hash)
    async with aiohttp.ClientSession(headers=_session_headers(token)) as session:
        async with session.get(
            f"{SD_BASE}/status", timeout=aiohttp.ClientTimeout(total=30)
        ) as r:
            r.raise_for_status()
            return await r.json()


async def get_lineups(username: str, password_hash: str) -> list:
    token = await _get_token(username, password_hash)
    async with aiohttp.ClientSession(headers=_session_headers(token)) as session:
        async with session.get(
            f"{SD_BASE}/lineups", timeout=aiohttp.ClientTimeout(total=30)
        ) as r:
            r.raise_for_status()
            data = await r.json()
            return data.get("lineups", [])


async def get_lineup_channels(username: str, password_hash: str, lineup_id: str) -> dict:
    token = await _get_token(username, password_hash)
    async with aiohttp.ClientSession(headers=_session_headers(token)) as session:
        async with session.get(
            f"{SD_BASE}/lineups/{lineup_id}",
            timeout=aiohttp.ClientTimeout(total=60),
        ) as r:
            r.raise_for_status()
            return await r.json()


async def get_schedules(username: str, password_hash: str, requests: list) -> list:
    token = await _get_token(username, password_hash)
    results = []
    # SD allows up to 5000 station-days per request; use conservative chunks
    chunk_size = 500
    for i in range(0, len(requests), chunk_size):
        chunk = requests[i : i + chunk_size]
        async with aiohttp.ClientSession(headers=_session_headers(token)) as session:
            async with session.post(
                f"{SD_BASE}/schedules",
                json=chunk,
                timeout=aiohttp.ClientTimeout(total=120),
            ) as r:
                r.raise_for_status()
                results.extend(await r.json())
    return results


async def get_programs(username: str, password_hash: str, program_ids: list) -> list:
    token = await _get_token(username, password_hash)
    results = []
    chunk_size = 5000
    for i in range(0, len(program_ids), chunk_size):
        chunk = program_ids[i : i + chunk_size]
        async with aiohttp.ClientSession(headers=_session_headers(token)) as session:
            async with session.post(
                f"{SD_BASE}/programs",
                json=chunk,
                timeout=aiohttp.ClientTimeout(total=300),
            ) as r:
                r.raise_for_status()
                results.extend(await r.json())
    return results
