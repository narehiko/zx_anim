import json
import tempfile
import unittest
from pathlib import Path
from urllib.request import urlopen

from zxanim.characters import CharacterRepository
from zxanim.obs_server import ObsServer, ObsState


class ObsServerTests(unittest.TestCase):
    def test_serves_state_and_character_asset(self):
        with tempfile.TemporaryDirectory() as bundled, tempfile.TemporaryDirectory() as user:
            pack_dir = Path(bundled, "sample")
            pack_dir.mkdir()
            Path(pack_dir, "frame.png").write_bytes(b"image")
            Path(pack_dir, "character.json").write_text(
                json.dumps(
                    {
                        "id": "sample",
                        "name": "Sample",
                        "canvas": {"width": 100, "height": 100},
                        "default_action": "tap",
                        "actions": {"tap": {"frames": ["frame.png"]}},
                    }
                ),
                encoding="utf-8",
            )
            repository = CharacterRepository(bundled, user)
            state = ObsState()
            state.update("/asset/sample/frame.png")
            server = ObsServer(repository, state, 0)
            server.start()
            try:
                with urlopen(f"{server.url}state") as response:
                    self.assertEqual(
                        json.loads(response.read()),
                        {"asset": "/asset/sample/frame.png"},
                    )
                with urlopen(f"{server.url}asset/sample/frame.png") as response:
                    self.assertEqual(response.read(), b"image")
            finally:
                server.stop()


if __name__ == "__main__":
    unittest.main()
