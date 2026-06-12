import os
import sys
from pathlib import Path

from .constants import APP_NAME


def resource_root():
    bundled_root = getattr(sys, "_MEIPASS", None)
    if bundled_root:
        return Path(bundled_root)
    return Path(__file__).resolve().parent.parent


def resource_path(*parts):
    return resource_root().joinpath(*parts)


def app_data_dir():
    base = Path(os.environ.get("APPDATA", Path.home()))
    path = base / APP_NAME
    path.mkdir(parents=True, exist_ok=True)
    return path


def user_characters_dir():
    path = app_data_dir() / "characters"
    path.mkdir(parents=True, exist_ok=True)
    return path
