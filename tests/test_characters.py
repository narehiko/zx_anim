import json
import tempfile
import unittest
from pathlib import Path

from zxanim.characters import CharacterPackError, CharacterRepository


class CharacterRepositoryTests(unittest.TestCase):
    def test_loads_valid_pack(self):
        with tempfile.TemporaryDirectory() as bundled, tempfile.TemporaryDirectory() as user:
            pack_dir = Path(bundled, "sample")
            pack_dir.mkdir()
            Path(pack_dir, "frame.png").write_bytes(b"png")
            Path(pack_dir, "character.json").write_text(
                json.dumps(
                    {
                        "id": "sample",
                        "name": "Sample",
                        "canvas": {"width": 100, "height": 100},
                        "default_action": "tap",
                        "actions": {
                            "tap": {
                                "name": "Tap",
                                "frames": ["frame.png"],
                            }
                        },
                    }
                ),
                encoding="utf-8",
            )
            repository = CharacterRepository(bundled, user)
            self.assertEqual(repository.require("sample").name, "Sample")

    def test_rejects_paths_outside_pack(self):
        with tempfile.TemporaryDirectory() as bundled, tempfile.TemporaryDirectory() as user:
            pack_dir = Path(bundled, "sample")
            pack_dir.mkdir()
            Path(bundled, "outside.png").write_bytes(b"png")
            Path(pack_dir, "character.json").write_text(
                json.dumps(
                    {
                        "id": "sample",
                        "name": "Sample",
                        "canvas": {"width": 100, "height": 100},
                        "default_action": "tap",
                        "actions": {
                            "tap": {
                                "frames": ["../outside.png"],
                            }
                        },
                    }
                ),
                encoding="utf-8",
            )
            repository = CharacterRepository(bundled, user)
            with self.assertRaises(CharacterPackError):
                repository.require("sample")


if __name__ == "__main__":
    unittest.main()
