import hashlib
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import List

import yaml

_SETTINGS_PATH = Path("data/config.yaml")
_LOCAL_PATH = Path("config.yaml")


def _md5(s: str) -> str:
    return hashlib.md5(s.encode()).hexdigest()


@dataclass
class Config:
    sd_username: str = ""
    sd_password_hash: str = ""
    days: int = 3
    schedule_interval_hours: float = 6.0
    output_path: str = "data/epg.xml"
    enabled_lineups: List[str] = field(default_factory=list)


def _apply_yaml(cfg: Config, data: dict) -> None:
    if v := data.get("sd_username"):
        cfg.sd_username = v
    if v := data.get("sd_password_hash"):
        cfg.sd_password_hash = v
    if "days" in data:
        cfg.days = int(data["days"])
    if "schedule_interval_hours" in data:
        cfg.schedule_interval_hours = float(data["schedule_interval_hours"])
    if "output_path" in data:
        cfg.output_path = data["output_path"]
    if "enabled_lineups" in data:
        cfg.enabled_lineups = list(data["enabled_lineups"] or [])


def _apply_env(cfg: Config) -> None:
    if v := os.environ.get("SD_USERNAME"):
        cfg.sd_username = v
    if v := os.environ.get("SD_PASSWORD"):
        cfg.sd_password_hash = _md5(v)
    if v := os.environ.get("SD_DAYS"):
        cfg.days = int(v)
    if v := os.environ.get("SCHEDULE_INTERVAL_HOURS"):
        cfg.schedule_interval_hours = float(v)
    if v := os.environ.get("SD_OUTPUT_PATH"):
        cfg.output_path = v


def load_config() -> Config:
    cfg = Config()
    if _LOCAL_PATH.exists():
        with open(_LOCAL_PATH) as f:
            _apply_yaml(cfg, yaml.safe_load(f) or {})
    _apply_env(cfg)
    if _SETTINGS_PATH.exists():
        with open(_SETTINGS_PATH) as f:
            _apply_yaml(cfg, yaml.safe_load(f) or {})
    return cfg


_cfg: Config | None = None


def get_config() -> Config:
    global _cfg
    if _cfg is None:
        _cfg = load_config()
    return _cfg


def reload_config() -> Config:
    global _cfg
    _cfg = load_config()
    return _cfg


def save_config(updates: dict):
    _SETTINGS_PATH.parent.mkdir(exist_ok=True)
    data: dict = {}
    if _SETTINGS_PATH.exists():
        with open(_SETTINGS_PATH) as f:
            data = yaml.safe_load(f) or {}

    if "sd_username" in updates:
        data["sd_username"] = updates["sd_username"]
    if updates.get("sd_password"):
        data["sd_password_hash"] = _md5(updates["sd_password"])
    if "days" in updates:
        data["days"] = int(updates["days"])
    if "schedule_interval_hours" in updates:
        data["schedule_interval_hours"] = float(updates["schedule_interval_hours"])
    if "output_path" in updates:
        data["output_path"] = updates["output_path"]
    if "enabled_lineups" in updates:
        data["enabled_lineups"] = updates["enabled_lineups"]

    with open(_SETTINGS_PATH, "w") as f:
        yaml.dump(data, f, default_flow_style=False, allow_unicode=True)

    reload_config()
