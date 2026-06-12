import json
import tempfile
import unittest
from pathlib import Path

from zxanim.config import ConfigManager


class ConfigManagerTests(unittest.TestCase):
    def test_migrates_legacy_files_to_app_data(self):
        with tempfile.TemporaryDirectory() as data, tempfile.TemporaryDirectory() as legacy:
            Path(legacy, "config.json").write_text(
                json.dumps({"frame_speed": 9}),
                encoding="utf-8",
            )
            config = ConfigManager(data_dir=data, legacy_dir=legacy)
            self.assertEqual(config.settings["frame_speed"], 9)
            self.assertTrue(Path(data, "config.json").exists())

    def test_saves_position(self):
        with tempfile.TemporaryDirectory() as data:
            config = ConfigManager(data_dir=data, legacy_dir=data)
            config.save_position(12, 34, True)
            saved = json.loads(Path(data, "position.json").read_text("utf-8"))
            self.assertEqual(saved, {"locked": True, "x": 12, "y": 34})

    def test_migrates_legacy_action_names(self):
        with tempfile.TemporaryDirectory() as data:
            Path(data, "config.json").write_text(
                json.dumps({"keys": {"q": "A", "w": "B"}}),
                encoding="utf-8",
            )
            config = ConfigManager(data_dir=data, legacy_dir=data)
            self.assertEqual(
                config.settings["keys"],
                {"q": "left", "w": "right"},
            )

    def test_desktop_preview_is_hidden_by_default(self):
        with tempfile.TemporaryDirectory() as data:
            config = ConfigManager(data_dir=data, legacy_dir=data)
            self.assertFalse(config.settings["show_preview_on_startup"])
            self.assertEqual(config.settings["preview_scale_percent"], 60)


if __name__ == "__main__":
    unittest.main()
