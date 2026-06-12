import json
from copy import deepcopy
from pathlib import Path

from .constants import DEFAULT_CHARACTER_ID, DEFAULT_OBS_PORT
from .paths import app_data_dir


DEFAULT_SETTINGS = {
    "fps": 60,
    "frame_speed": 5,
    "rapid_tap_smoothing_ms": 70,
    "preview_scale_percent": 60,
    "show_preview_on_startup": False,
    "keys": {"q": "left", "w": "right"},
    "bg_mode": 0,
    "character": DEFAULT_CHARACTER_ID,
    "obs_port": DEFAULT_OBS_PORT,
}

DEFAULT_POSITION = {
    "x": 0,
    "y": 0,
    "locked": False,
}


class ConfigManager:
    def __init__(self, data_dir=None, legacy_dir=None):
        self.data_dir = Path(data_dir or app_data_dir())
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.legacy_dir = Path(legacy_dir or Path.cwd())
        self.settings_file = self.data_dir / "config.json"
        self.position_file = self.data_dir / "position.json"
        self.settings = deepcopy(DEFAULT_SETTINGS)
        self.position = deepcopy(DEFAULT_POSITION)
        self.load()

    def load(self):
        self.settings.update(self._read_with_migration("config.json"))
        self.position.update(self._read_with_migration("position.json"))
        self._migrate_legacy_settings()

    def _migrate_legacy_settings(self):
        legacy_actions = {"A": "left", "B": "right"}
        keys = self.settings.get("keys", {})
        self.settings["keys"] = {
            key: legacy_actions.get(action, action)
            for key, action in keys.items()
        }

    def _read_with_migration(self, filename):
        current = self.data_dir / filename
        legacy = self.legacy_dir / filename
        source = current if current.exists() else legacy
        if not source.exists():
            return {}
        try:
            data = json.loads(source.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {}
        if source == legacy and source != current:
            self._write_json(current, data)
        return data if isinstance(data, dict) else {}

    def save_position(self, x, y, locked):
        self.position.update({"x": x, "y": y, "locked": locked})
        self._write_json(self.position_file, self.position)

    def save_settings(self):
        self._write_json(self.settings_file, self.settings)

    @staticmethod
    def _write_json(path, data):
        temp_path = path.with_suffix(f"{path.suffix}.tmp")
        temp_path.write_text(
            json.dumps(data, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        temp_path.replace(path)
