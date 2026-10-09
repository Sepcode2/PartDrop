"""Instellingen worden in de KiCad-configmap bewaard, zodat ze een plugin-update overleven."""
import json
import os

from . import kicad_env

DEFAULTS = {
    "lib_dir": os.path.join(os.path.expanduser("~"), "Documents", "KiCad", "PartDrop"),
    "lib_name": "MijnLib",
    "watch_dir": os.path.join(os.path.expanduser("~"), "Downloads"),
    "watch": False,
    "overwrite": False,
    "prefer_step": True,
    "delete_after_import": False,
    "stay_on_top": False,
    "language": "auto",
}


def _path():
    return os.path.join(kicad_env.config_dir(), "partdrop.json")


def load():
    cfg = dict(DEFAULTS)
    try:
        with open(_path(), encoding="utf-8") as f:
            cfg.update(json.load(f))
    except (OSError, ValueError):
        pass
    return cfg


def save(cfg):
    try:
        os.makedirs(os.path.dirname(_path()), exist_ok=True)
        with open(_path(), "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2)
    except OSError:
        pass
