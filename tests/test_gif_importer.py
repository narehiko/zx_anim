import json
import tempfile
import unittest
from pathlib import Path

from PIL import Image

from zxanim.gif_importer import import_gif_as_character


class GifImporterTests(unittest.TestCase):
    def test_imports_gif_as_two_action_character_pack(self):
        with tempfile.TemporaryDirectory() as directory:
            gif_path = Path(directory, "My Character.gif")
            first = Image.new("RGBA", (16, 12), (255, 0, 0, 0))
            second = Image.new("RGBA", (16, 12), (0, 255, 0, 128))
            first.save(
                gif_path,
                save_all=True,
                append_images=[second],
                duration=80,
                loop=0,
                transparency=0,
            )

            pack_id = import_gif_as_character(gif_path, directory)
            pack_dir = Path(directory, pack_id)
            manifest = json.loads(
                Path(pack_dir, "character.json").read_text(encoding="utf-8")
            )

            self.assertEqual(pack_id, "my-character")
            self.assertEqual(manifest["canvas"], {"width": 16, "height": 12})
            self.assertEqual(set(manifest["actions"]), {"left", "right"})
            self.assertEqual(
                manifest["actions"]["left"]["frames"],
                manifest["actions"]["right"]["frames"],
            )
            for frame in manifest["actions"]["left"]["frames"]:
                self.assertTrue(Path(pack_dir, frame).is_file())


if __name__ == "__main__":
    unittest.main()
